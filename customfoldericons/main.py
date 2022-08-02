from io import BytesIO
import os
from textwrap import fill
from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QMouseEvent, QPaintEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QButtonGroup, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QRadioButton, QSlider, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt
from PIL import Image
import Cocoa

from customfoldericons.constants import ICON_SCALE_SLIDER_MAX, MAXIMUM_ICON_SCALE_VALUE, MINIMUM_ICON_SCALE_VALUE, FolderStyle, SFFont, TintColour
from customfoldericons.image_transformations import generate_colour_map_lookup_table, generate_folder_icon, generate_mask_from_image, generate_mask_from_text
from customfoldericons.utilities import interpolate_int_to_float_with_midpoint, resource_path


class CenterIcon(QLabel):
  MINIMUM_SIZE = (400, 400)

  def __init__(self):
    super().__init__()

    self.setMinimumSize(*self.MINIMUM_SIZE)
    self.setAcceptDrops(True)

    # self.set_image(image)

  def set_image(self, image):
    self.pixmap = QPixmap(image)
    self.update()

  def paintEvent(self, _: QPaintEvent) -> None:
    size = self.size()
    painter = QPainter(self)
    point = QPoint(0,0)

    scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    point.setX((size.width() - scaledPix.width())/2)
    point.setY((size.height() - scaledPix.height())/2)

    painter.drawPixmap(point, scaledPix)
    painter.end()

class ColourRadioButton(QRadioButton):
  BORDER_RADIUS = 5.0
  ACTIVE_BORDER_WIDTH = 3.0
  INACTIVE_BORDER_WIDTH = 2.0

  INACTIVE_BORDER_COLOUR = (212, 212, 212)
  ACTIVE_BORDER_COLOUR = (100, 198, 237)
  
  EMPTY_FILL_COLOUR = (255, 255, 255)

  def __init__(self, colour=None, default=False, multicolour=False, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.colour = colour
    self.is_default = default
    self.is_multicolour = multicolour

    self.setMinimumHeight(30)

  def hitButton(self, point: QPoint) -> bool:
    return self._get_center_rect().contains(point)

  def paintEvent(self, _: QPaintEvent) -> None:
    center_rect = self._get_center_rect()

    border_width = self.ACTIVE_BORDER_WIDTH if self.isChecked() else self.INACTIVE_BORDER_WIDTH
    border_colour = self.ACTIVE_BORDER_COLOUR if self.isChecked() else self.INACTIVE_BORDER_COLOUR

    fill_colour = self.colour if self.colour is not None else self.EMPTY_FILL_COLOUR

    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)

    outline_pen = QPen()
    outline_pen.setWidth(border_width)
    outline_pen.setColor(QColor.fromRgb(*border_colour))
    
    fill_brush = QBrush()
    fill_brush.setColor(QColor.fromRgb(*fill_colour))
    fill_brush.setStyle(Qt.SolidPattern)

    painter.setPen(outline_pen)
    painter.setBrush(fill_brush)

    border_offset = border_width * 0.8
    painter.drawRoundedRect(
      center_rect.adjusted(border_offset, border_offset, -border_offset, -border_offset), 
      self.BORDER_RADIUS - border_offset, self.BORDER_RADIUS - border_offset
    )

    if self.is_default:
      dash_pen = QPen()
      dash_pen.setColor(QColor.fromRgb(*self.INACTIVE_BORDER_COLOUR))
      dash_pen.setCapStyle(Qt.RoundCap)
      dash_pen.setWidth(3)
      
      painter.setPen(dash_pen)

      start_point = center_rect.topLeft() + QPoint(8, 8)
      end_point = center_rect.bottomRight() + QPoint(-8, -8)

      painter.drawLine(start_point, end_point)
    if self.is_multicolour:
      ...

    painter.end()

  def _get_center_rect(self):
    size = self.size()

    width_adjustment = (size.width() - size.height()) / 2
    total_rect = QRect(QPoint(0, 0), size)
    
    return total_rect.adjusted(width_adjustment, 0, -width_adjustment, 0)


class NonEditableLine(QLineEdit):
  def __init__(self, placeholder_text):
    super().__init__()

    self.setPlaceholderText(placeholder_text)

    self.setReadOnly(True)
    self.setAlignment(Qt.AlignCenter)
  
  def set_text(self, text):
    self.text = text

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    self.image = None

    # self.lookup_table = None

    self.image_mask = None
    self.tint_colour = None  # None = none, otherwise tuple of rgb int
    self.image_text = ""
    self.output_folder = None
    self.output_location_directory = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
    self.folder_style = FolderStyle.big_sur_light
    self.font_style = SFFont.bold
    self.icon_scale = 1

    self.center_image = CenterIcon()
    self.center_image.dragEnterEvent = self.unified_drag_enter
    self.center_image.dropEvent = self.unified_drop



    self.colour_button_group = QButtonGroup()
    colour_pallete_layout = QHBoxLayout()

    colour_buttons = []

    colour_buttons.append(ColourRadioButton(default=True))
    for tint_colour in TintColour:
      colour_buttons.append(ColourRadioButton(colour=tint_colour.value))
    colour_buttons.append(ColourRadioButton(multicolour=True))

    colour_buttons[-1].clicked.connect(self.choose_custom_colour)

    for colour_button in colour_buttons:
      colour_button.clicked.connect(self.select_colour)
      self.colour_button_group.addButton(colour_button)
      colour_pallete_layout.addWidget(colour_button)

    colour_buttons[0].setChecked(True)





    self.scale_slider = QSlider(Qt.Horizontal)
    self.scale_slider.setMinimum(1)
    self.scale_slider.setMaximum(ICON_SCALE_SLIDER_MAX)
    self.scale_slider.setMinimumHeight(40)
    self.scale_slider.setTickInterval(ICON_SCALE_SLIDER_MAX + 1)
    self.scale_slider.setTickPosition(QSlider.TicksBelow)
    self.scale_slider.setValue(int((ICON_SCALE_SLIDER_MAX - 1)/2) + 1)
    self.scale_slider.setTracking(False)
    self.scale_slider.valueChanged.connect(self.icon_scale_changed)

    self.font_weight_slider = QSlider(Qt.Horizontal)
    self.font_weight_slider.setMinimum(1)
    self.font_weight_slider.setMaximum(8)
    self.font_weight_slider.setMinimumHeight(40)
    self.font_weight_slider.setTickInterval(1)
    self.font_weight_slider.setTickPosition(QSlider.TicksBelow)
    self.font_weight_slider.setValue(self.font_style.value)
    self.font_weight_slider.setTracking(False)
    self.font_weight_slider.valueChanged.connect(self.font_weight_changed)

    scale_font_weight_layout = QHBoxLayout()
    scale_font_weight_layout.addWidget(self.scale_slider)
    scale_font_weight_layout.addWidget(self.font_weight_slider)


    self.icon_input_field = QLineEdit()
    self.icon_input_field.setMaxLength(100)
    self.icon_input_field.setPlaceholderText("Drag symbol / image / type text")
    self.icon_input_field.setAlignment(Qt.AlignCenter)
    self.icon_input_field.setFont(QFont("SF Pro Rounded"))
    self.icon_input_field.textChanged.connect(self.icon_text_changed)
    # self.dragEnterEvent = self.unified_drag_enter
    # self.dropEvent = self.unified_drop

    self.generate_button = QPushButton("Save Icon")
    self.generate_button.clicked.connect(self.generate_folder)

    input_generate_layout = QHBoxLayout()
    input_generate_layout.addWidget(self.icon_input_field, 1)
    input_generate_layout.addSpacing(8)
    input_generate_layout.addWidget(self.generate_button)

    self.folder_replacement_field = NonEditableLine("Drag folder above to change its icon")
    self.folder_replacement_field.dragEnterEvent = self.unified_drag_enter
    self.folder_replacement_field.dropEvent = self.unified_drop


    folder_output_label = QLabel("OR make new folder in:")
    self.folder_output_path = NonEditableLine("")
    self.folder_output_path.setMinimumWidth(50)
    self.folder_output_picker_button = QPushButton("...")
    self.folder_output_picker_button.clicked.connect(self.open_output_location_directory)

    folder_output_layout = QHBoxLayout()
    folder_output_layout.addWidget(folder_output_label)
    folder_output_layout.addSpacing(8)
    folder_output_layout.addWidget(self.folder_output_path)
    folder_output_layout.addSpacing(8)
    folder_output_layout.addWidget(self.folder_output_picker_button)

    main_layout = QVBoxLayout()
    main_layout.setSpacing(1)
    main_layout.addWidget(self.center_image)
    main_layout.addLayout(colour_pallete_layout)
    main_layout.addLayout(scale_font_weight_layout)
    main_layout.addLayout(input_generate_layout)
    main_layout.addWidget(self.folder_replacement_field)
    main_layout.addLayout(folder_output_layout)
    # inputs_layout.addLayout(advanced_options, 3, 0, 3, 1)

    main_widget = QWidget()
    main_widget.setLayout(main_layout)
    self.setCentralWidget(main_widget)

    main_widget.setFocus()
    self.set_output_location_directory(self.output_location_directory)
    self.update_and_generate_image()

  def select_colour(self):
    print(self.sender().colour)
    self.tint_colour = self.sender().colour
    self.update_and_generate_image()

  def choose_custom_colour(self):
    print("TESTING")

  def update_and_generate_image(self):

    # if self.lookup_table is None:
    #   self.lookup_table = generate_colour_map_lookup_table(self.folder_style.base_colour(), (105,105,105))

    self.image = generate_folder_icon(
      self.folder_style,
      mask_image=self.image_mask,
      icon_scale=self.icon_scale,
      tint_colour=self.tint_colour,
    )
    self.center_image.set_image(ImageQt(self.image))

  # def set_image(self, image: Image):
  #   self.image = image
  #   self.center_image.set_image(ImageQt(self.image))

  def generate_folder(self):
    path = self.output_folder
    self.set_output_folder(None)

    if self.image is None: return

    if path is None:
      index = 1
      while True:
        new_folder_name = "untitled folder" + ("" if index == 1 else " {}".format(index))
        path = os.path.join(self.output_location_directory, new_folder_name)

        if not os.path.exists(path): 
          os.mkdir(path)
          break
        index += 1

    self.set_folder_icon(self.image, path)

  def open_output_location_directory(self):
    file_picker = QFileDialog(self)
    file_picker.setFileMode(QFileDialog.Directory)
    file_picker.setAcceptMode(QFileDialog.AcceptOpen)

    if file_picker.exec():
      path = file_picker.selectedFiles()[0]
      self.set_output_location_directory(path)

  def icon_text_changed(self, text):
    print(self.font_style)
    self.image_text = text
    self.image_mask = generate_mask_from_text(text, font_style=self.font_style, folder_style=self.folder_style)
    self.update_and_generate_image()

  def icon_scale_changed(self, value):
    self.icon_scale = interpolate_int_to_float_with_midpoint(
      value, 1, ICON_SCALE_SLIDER_MAX, MINIMUM_ICON_SCALE_VALUE, 1.0, MAXIMUM_ICON_SCALE_VALUE
    )
    self.update_and_generate_image()

  def font_weight_changed(self, value):
    self.font_style = SFFont(value)
    if self.image_text != "":
      self.image_mask = generate_mask_from_text(self.image_text, font_style=self.font_style, folder_style=self.folder_style)
    self.update_and_generate_image()

  def set_output_folder(self, path):
    self.output_folder = path
    self.folder_replacement_field.setText(path)

  def set_output_location_directory(self, path):
    self.output_location_directory = path
    self.folder_output_path.setText(os.path.basename(path))


  def unified_drag_enter(self, event: QDragEnterEvent):
    print("enter")
    event.acceptProposedAction()

  def unified_drop(self, event: QDropEvent):
    data = event.mimeData()

    # print("text", event.mimeData().text())
    # print("has image", event.mimeData().hasImage())
    # print("font", re.search("'SF.*'", event.mimeData().html()).group())
    # print("html", data.html())
    # print("urls", event.mimeData().urls())
    # print("formats", event.mimeData().formats())
    # print(event.mimeData().hasFormat("application/x-qt-image"))
    # print("image data", event.mimeData().imageData())

    # first check image data if format application/x-qt-image, then inder imagedata, is of QImage type

    if data.hasFormat("application/x-qt-image"):
      image = Image.fromqimage(data.imageData())
      self.image_text = ""
      self.image_mask = generate_mask_from_image(image, folder_style=self.folder_style)
      self.update_and_generate_image()

    # else check if directory or file with text/uri-list, starts with file://

    elif data.hasFormat("text/uri-list"):
      url = data.urls()[0]

      if url.scheme() == "file":
        path = url.toLocalFile()

        if os.path.isdir(path):
          self.set_output_folder(path)

        elif os.path.isfile(path):
          try:
            file_image = Image.open(path)
            self.image_text = ""
            self.image_mask = generate_mask_from_image(file_image, folder_style=self.folder_style)
            self.update_and_generate_image()
          except:
            print("NOT IMAGE OR COULD NOT OPEN")

    # else must be simple text text/plain, make sure has no url text/uri-list

    elif data.hasFormat("text/plain"):
      self.image_text = data.text()
      self.image_mask = generate_mask_from_text(data.text(), font_style=self.font_style, folder_style=self.folder_style)
      self.update_and_generate_image()

    event.accept()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    focused_widget = QApplication.focusWidget()
    if isinstance(focused_widget, QLineEdit):
      focused_widget.clearFocus()

    super().mousePressEvent(event)

  def set_folder_icon(self, pil_image, path):
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    
    ns_image = Cocoa.NSImage.alloc().initWithData_(buffered.getvalue())
    Cocoa.NSWorkspace.sharedWorkspace().setIcon_forFile_options_(ns_image, path, 0)


app = QApplication()

window = MainWindow()
window.show()

app.exec()