from io import BytesIO
import os
from random import randint
from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QMouseEvent, QPaintEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QButtonGroup, QColorDialog, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QRadioButton, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt
from PIL import Image
import Cocoa

from fancyfolders.constants import ICON_SCALE_SLIDER_MAX, MAXIMUM_ICON_SCALE_VALUE, MINIMUM_ICON_SCALE_VALUE, PREVIEW_IMAGE_SIZE, FolderStyle, IconGenerationMethod, SFFont, TintColour
from fancyfolders.image_transformations import generate_folder_icon
from fancyfolders.utilities import interpolate_int_to_float_with_midpoint


class CenterIcon(QLabel):
  MINIMUM_SIZE = (400, 340)

  def __init__(self):
    super().__init__()

    self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.setMinimumSize(*self.MINIMUM_SIZE)
    self.setAcceptDrops(True)

  def set_image(self, image, folder_style=FolderStyle.big_sur_light):  # takes pil image
    crop_rect_percentages = folder_style.preview_crop_percentages()
    crop_rect = QRect()
    crop_rect.setCoords(*tuple(int(image.size[0] * percent) for percent in crop_rect_percentages))
    
    cropped_image = ImageQt(image).copy(crop_rect)

    self.pixmap = QPixmap(cropped_image)
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
      center_point = center_rect.center()
      rainbow_gradient = QConicalGradient(center_point, 0)
      rainbow_gradient.setColorAt(0.0, QColor(*TintColour.red.value))
      rainbow_gradient.setColorAt(0.2, QColor(*TintColour.yellow.value))
      rainbow_gradient.setColorAt(0.5, QColor(*TintColour.orange.value))
      rainbow_gradient.setColorAt(0.8, QColor(*TintColour.purple.value))
      rainbow_gradient.setColorAt(1.0, QColor(*TintColour.red.value))

      rainbow_pen = QPen(rainbow_gradient, 5.0)

      painter.setPen(rainbow_pen)
      painter.setBrush(Qt.NoBrush)

      painter.drawEllipse(center_point + QPoint(1, 1), 6, 6)

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

    ##############################
    # ICON GENERATION VARIABLES
    ##############################

    self.icon_generation_method = IconGenerationMethod.NONE
    self.icon_text = None
    self.icon_image = None

    self.icon_tint_colour = None  # None = none, otherwise tuple of rgb int
    self.icon_font_style = SFFont.bold
    self.icon_scale = 1

    self.folder_style = FolderStyle.big_sur_light

    self.output_folder = None
    self.output_location_directory = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")


    ##############################
    # UI SETUP
    ##############################

    self.folder_style_dropdown = QComboBox()
    self.folder_style_dropdown.addItems([style.display_name() for style in FolderStyle])
    self.folder_style_dropdown.setCurrentIndex(self.folder_style.value)
    self.folder_style_dropdown.currentIndexChanged.connect(self.select_folder_style)

    title_label = QLabel("Folder Icon Preview")
    title_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-size: 20px; font-style: italic; font-family: Georgia, 'Times New Roman';")

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

    for colour_button in colour_buttons:
      if not colour_button.is_multicolour:
        colour_button.clicked.connect(self.select_colour)
      self.colour_button_group.addButton(colour_button)
      colour_pallete_layout.addWidget(colour_button)

    colour_buttons[0].setChecked(True)
    colour_buttons[-1].clicked.connect(self.choose_custom_colour)


    scale_label = QLabel("Icon scale")
    scale_label.setAlignment(Qt.AlignHCenter)
    scale_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

    font_weight_label = QLabel("Symbol thickness")
    font_weight_label.setAlignment(Qt.AlignHCenter)
    font_weight_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

    scale_font_weight_label_container = QHBoxLayout()
    scale_font_weight_label_container.addWidget(scale_label)
    scale_font_weight_label_container.addWidget(font_weight_label)

    # TODO make sliders own class

    self.scale_slider = QSlider(Qt.Horizontal)
    self.scale_slider.setMinimum(1)
    self.scale_slider.setMaximum(ICON_SCALE_SLIDER_MAX)
    self.scale_slider.setMinimumHeight(40)
    self.scale_slider.setTickInterval(ICON_SCALE_SLIDER_MAX + 1)
    self.scale_slider.setTickPosition(QSlider.TicksBelow)
    self.scale_slider.setValue(int((ICON_SCALE_SLIDER_MAX - 1)/2) + 1)
    self.scale_slider.setTracking(True)
    self.scale_slider.valueChanged.connect(self.icon_scale_changed)

    self.font_weight_slider = QSlider(Qt.Horizontal)
    self.font_weight_slider.setMinimum(1)
    self.font_weight_slider.setMaximum(8)
    self.font_weight_slider.setMinimumHeight(40)
    self.font_weight_slider.setTickInterval(1)
    self.font_weight_slider.setTickPosition(QSlider.TicksBelow)
    self.font_weight_slider.setValue(self.icon_font_style.value)
    self.font_weight_slider.setTracking(True)
    self.font_weight_slider.valueChanged.connect(self.font_weight_changed)

    scale_font_weight_layout = QHBoxLayout()
    scale_font_weight_layout.addWidget(self.scale_slider)
    scale_font_weight_layout.addWidget(self.font_weight_slider)


    self.icon_input_field = QLineEdit()
    self.icon_input_field.setMaxLength(100)
    self.icon_input_field.setPlaceholderText("Drag symbol/image above or type text")
    self.icon_input_field.setAlignment(Qt.AlignCenter)
    self.icon_input_field.setFont(QFont("SF Pro Rounded"))
    self.icon_input_field.textChanged.connect(self.icon_text_changed)
    # self.dragEnterEvent = self.unified_drag_enter
    # self.dropEvent = self.unified_drop

    # TODO make custom class - larger and different colour

    self.generate_button = QPushButton("Save icon")
    self.generate_button.clicked.connect(self.generate_and_save_folder)

    input_generate_layout = QHBoxLayout()
    input_generate_layout.addWidget(self.icon_input_field, 1)
    input_generate_layout.addSpacing(8)
    input_generate_layout.addWidget(self.generate_button)

    self.folder_replacement_field = NonEditableLine("Drag folder above to change its icon")
    self.folder_replacement_field.dragEnterEvent = self.unified_drag_enter
    self.folder_replacement_field.dropEvent = self.unified_drop


    folder_output_label = QLabel("Or make new folder in:")
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
    main_layout.setSpacing(0)
    main_layout.addWidget(self.folder_style_dropdown)
    main_layout.addSpacerItem(QSpacerItem(0,15))
    main_layout.addWidget(title_label)
    main_layout.addWidget(self.center_image)
    main_layout.addSpacerItem(QSpacerItem(0, 5))
    main_layout.addLayout(colour_pallete_layout)
    main_layout.addSpacerItem(QSpacerItem(0, 10))
    main_layout.addLayout(scale_font_weight_label_container)
    main_layout.addLayout(scale_font_weight_layout)
    main_layout.addSpacerItem(QSpacerItem(0, 15))
    main_layout.addLayout(input_generate_layout)
    main_layout.addSpacerItem(QSpacerItem(0, 15))
    main_layout.addWidget(self.folder_replacement_field)
    main_layout.addLayout(folder_output_layout)
    # inputs_layout.addLayout(advanced_options, 3, 0, 3, 1)

    main_widget = QWidget()
    main_widget.setLayout(main_layout)
    self.setCentralWidget(main_widget)

    main_widget.setFocus()
    self.set_output_location_directory(self.output_location_directory)
    self.update_preview_folder_image()

  def select_colour(self):
    self.icon_tint_colour = self.sender().colour
    self.update_preview_folder_image()

  def choose_custom_colour(self):
    colour_dialog = QColorDialog()
    if colour_dialog.exec():
      colour = colour_dialog.currentColor()
      self.icon_tint_colour = (colour.red(), colour.green(), colour.blue())
      self.update_preview_folder_image()

  def generate_folder_image(self, size=None):
    return generate_folder_icon(
      folder_style=self.folder_style,
      preview_size=size,
      generation_method=self.icon_generation_method, 
      icon_scale=self.icon_scale, 
      tint_colour=self.icon_tint_colour, 
      text=self.icon_text, 
      font_style=self.icon_font_style, 
      image=self.icon_image
    )

  def select_folder_style(self, index):
    self.folder_style = FolderStyle(index)
    self.update_preview_folder_image()

  def update_preview_folder_image(self):
    image = self.generate_folder_image(size=PREVIEW_IMAGE_SIZE)
    self.center_image.set_image(image)

  def generate_and_save_folder(self):
    # Only set folder icon to specific folder once
    path = self.output_folder
    self.set_output_folder(None)

    # If there is no specific path, generate a new folder
    if path is None:
      index = 1
      while True:
        new_folder_name = "untitled folder" + ("" if index == 1 else " {}".format(index))
        path = os.path.join(self.output_location_directory, new_folder_name)

        if not os.path.exists(path): 
          os.mkdir(path)
          break
        index += 1

    self.setCursor(Qt.WaitCursor)

    # Set folder icon to the highest resolution image
    high_resolution_image = self.generate_folder_image()
    self.center_image.set_image(high_resolution_image)
    self.set_folder_icon(high_resolution_image, path)

    self.unsetCursor()

    # DEV IMAGE SAVE
    # high_resolution_image.save(os.path.join(self.output_location_directory, "imageoutput-" + str(randint(1, 99999)) + ".png"))

  def open_output_location_directory(self):
    file_picker = QFileDialog(self)
    file_picker.setFileMode(QFileDialog.Directory)
    file_picker.setAcceptMode(QFileDialog.AcceptOpen)

    if file_picker.exec():
      path = file_picker.selectedFiles()[0]
      self.set_output_location_directory(path)

  def icon_text_changed(self, text):
    if text.strip() == "":
      self.icon_generation_method = IconGenerationMethod.NONE
    else:
      self.icon_generation_method = IconGenerationMethod.TEXT
      self.icon_text = text

    self.update_preview_folder_image()

  def icon_scale_changed(self, value):
    self.icon_scale = interpolate_int_to_float_with_midpoint(
      value, 1, ICON_SCALE_SLIDER_MAX, MINIMUM_ICON_SCALE_VALUE, 1.0, MAXIMUM_ICON_SCALE_VALUE
    )
    self.update_preview_folder_image()

  def font_weight_changed(self, value):
    self.icon_font_style = SFFont(value)
    self.update_preview_folder_image()

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

    # first check image data if format application/x-qt-image, then inder imagedata, is of QImage type

    if data.hasFormat("application/x-qt-image"):
      self.icon_generation_method = IconGenerationMethod.IMAGE
      self.icon_image = Image.fromqimage(data.imageData())
      self.update_preview_folder_image()

    # else check if directory or file with text/uri-list, starts with file://

    elif data.hasFormat("text/uri-list"):
      url = data.urls()[0]

      if url.scheme() == "file":
        path = url.toLocalFile()

        if os.path.isdir(path):
          self.set_output_folder(path)

        elif os.path.isfile(path):
          try:
            self.icon_generation_method = IconGenerationMethod.IMAGE
            self.icon_image = Image.open(path)
            self.update_preview_folder_image()
          except:
            print("NOT IMAGE OR COULD NOT OPEN")

    # else must be simple text text/plain, make sure has no url text/uri-list

    elif data.hasFormat("text/plain"):
      self.icon_generation_method = IconGenerationMethod.TEXT
      self.icon_text = data.text()
      print(self.icon_text)
      self.update_preview_folder_image()

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