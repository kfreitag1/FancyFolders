from io import BytesIO
import os
from PySide6.QtCore import QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QMouseEvent, QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt
from PIL import Image
import Cocoa

from customfoldericons.constants import FolderStyle, SFFont
from customfoldericons.image_transformations import generate_folder_icon_from_image, generate_folder_icon_from_text
from customfoldericons.utilities import resource_path


class CenterIcon(QLabel):
  def __init__(self, image):
    super().__init__()

    self.setMinimumSize(400,400)
    self.setAcceptDrops(True)

    self.set_image(image)

  def set_image(self, image):
    self.pixmap = QPixmap(image)
    self.update()

  def paintEvent(self, event: QPaintEvent) -> None:
    size = self.size()
    painter = QPainter(self)
    point = QPoint(0,0)

    scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    point.setX((size.width() - scaledPix.width())/2)
    point.setY((size.height() - scaledPix.height())/2)

    painter.drawPixmap(point, scaledPix)
    painter.end()

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
    self.output_folder = None
    self.output_location_directory = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
    self.folder_style = FolderStyle.big_sur_light
    self.font_style = SFFont.black
    self.icon_scale = 1

    self.center_image = CenterIcon(ImageQt(Image.open(resource_path("assets/" + self.folder_style.filename()))))
    self.center_image.dragEnterEvent = self.unified_drag_enter
    self.center_image.dropEvent = self.unified_drop

    self.icon_input_field = QLineEdit()
    self.icon_input_field.setMaxLength(100)
    self.icon_input_field.setPlaceholderText("Drag symbol / image / type text")
    self.icon_input_field.setAlignment(Qt.AlignCenter)
    self.icon_input_field.setFont(QFont("SF Pro Rounded"))
    self.icon_input_field.textChanged.connect(self.icon_text_changed)
    # self.dragEnterEvent = self.unified_drag_enter
    # self.dropEvent = self.unified_drop

    self.generate_button = QPushButton("Generate Folder")
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
    main_layout.addLayout(input_generate_layout)
    main_layout.addWidget(self.folder_replacement_field)
    main_layout.addLayout(folder_output_layout)
    # inputs_layout.addLayout(advanced_options, 3, 0, 3, 1)


    main_widget = QWidget()
    main_widget.setLayout(main_layout)
    self.setCentralWidget(main_widget)

    self.set_output_location_directory(self.output_location_directory)
    main_widget.setFocus()

  def set_image(self, image: Image):
    self.image = image
    self.center_image.set_image(ImageQt(self.image))

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
    self.set_image(generate_folder_icon_from_text(text, font_style=self.font_style, folder_style=self.folder_style))

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
      self.set_image(generate_folder_icon_from_image(image, folder_style=self.folder_style))

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
            self.set_image(generate_folder_icon_from_image(file_image, folder_style=self.folder_style))
          except:
            print("ERROR OPENING IMAGE")

    # else must be simple text text/plain, make sure has no url text/uri-list

    elif data.hasFormat("text/plain"):
      self.set_image(generate_folder_icon_from_text(data.text(), font_style=self.font_style, folder_style=self.folder_style))

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