import html
import random
import re
from PySide6.QtCore import QAbstractAnimation, QLine, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QAction, QColor, QContextMenuEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QMouseEvent, QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt
from PIL import Image

from customfoldericons.image_transformations import FolderStyle, generate_folder_icon_from_image, generate_folder_icon_from_text
from customfoldericons.utilities import resource_path


class CenterIcon(QLabel):
  def __init__(self, image = None):
    super().__init__()

    self.setMinimumSize(400,400)
    self.setAcceptDrops(True)

    self.image = image
    if image is not None: self.set_image(image)

  def set_image(self, image):
    self.image = image
    self.pixmap = QPixmap(self.image)
    self.update()

  def paintEvent(self, event: QPaintEvent) -> None:
    if self.image is None: return

    size = self.size()
    painter = QPainter(self)
    point = QPoint(0,0)

    scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # start painting the label from left upper corner
    point.setX((size.width() - scaledPix.width())/2)
    point.setY((size.height() - scaledPix.height())/2)
    # print(point.x(), ' ', point.y())

    painter.drawPixmap(point, scaledPix)
    painter.end()

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    self.image = CenterIcon(ImageQt(Image.open(resource_path("assets/big_sur_light.png"))))
    self.image.dragEnterEvent = self.unified_drag_enter
    self.image.dropEvent = self.unified_drop

    self.icon_input_field = QLineEdit()
    self.icon_input_field.setMaxLength(20)
    self.icon_input_field.setPlaceholderText("Drag symbol / image / type text")
    self.icon_input_field.setAlignment(Qt.AlignCenter)
    self.icon_input_field.setFont(QFont("SF Pro Rounded"))
    self.dragEnterEvent = self.unified_drag_enter
    self.dropEvent = self.unified_drop

    self.generate_button = QPushButton("Generate Folder")
    self.generate_button.clicked.connect(self.generate_folder)

    input_generate_layout = QHBoxLayout()
    input_generate_layout.addWidget(self.icon_input_field, 1)
    input_generate_layout.addSpacing(8)
    input_generate_layout.addWidget(self.generate_button)

    self.folder_replacement_field = QLineEdit("Drag folder to change its icon")
    self.folder_replacement_field.setEnabled(False)
    self.folder_replacement_field.setStyleSheet("padding-left: 5px")
    self.dragEnterEvent = self.unified_drag_enter
    self.dropEvent = self.unified_drop

    folder_output_label = QLabel("Or output to:")

    self.folder_output_path = QLineEdit("Desktop")
    self.folder_output_path.setEnabled(False)
    self.folder_output_path.setStyleSheet("padding-left: 5px")
    self.folder_output_path.setMinimumWidth(50)

    self.folder_output_picker_button = QPushButton("Choose destination")

    folder_output_layout = QHBoxLayout()
    folder_output_layout.addWidget(folder_output_label)
    folder_output_layout.addSpacing(8)
    folder_output_layout.addWidget(self.folder_output_path)
    folder_output_layout.addSpacing(8)
    folder_output_layout.addWidget(self.folder_output_picker_button)

    main_layout = QVBoxLayout()
    main_layout.setSpacing(1)
    main_layout.addWidget(self.image)
    main_layout.addLayout(input_generate_layout)
    main_layout.addWidget(self.folder_replacement_field)
    main_layout.addLayout(folder_output_layout)
    # inputs_layout.addLayout(advanced_options, 3, 0, 3, 1)


    main_widget = QWidget()
    main_widget.setLayout(main_layout)
    self.setCentralWidget(main_widget)

    main_widget.setFocus()

  def generate_folder(self):
    pass


  def unified_drag_enter(self, event: QDragEnterEvent):
    print("enter")
    event.acceptProposedAction()

  def unified_drop(self, event: QDropEvent):
    data = event.mimeData()

    print("text", event.mimeData().text())
    # print("has image", event.mimeData().hasImage())
    # print("font", re.search("'SF.*'", event.mimeData().html()).group())
    print("html", data.html())
    # print("urls", event.mimeData().urls())
    print("formats", event.mimeData().formats())
    print(event.mimeData().hasFormat("application/x-qt-image"))
    # print("image data", event.mimeData().imageData())

    # first check image data if format application/x-qt-image, then inder imagedata, is of QImage type

    if data.hasFormat("application/x-qt-image"):
      qimage = data.imageData()
      symbol_image = generate_folder_icon_from_image(Image.fromqimage(qimage))
      self.image.set_image(ImageQt(symbol_image))

    # else check if sf symbol if format text/html, and if html has meta tag name Generator, content Cocoa HTML Writer
    # get symbol after &# , convert from html hex to unicode character

    # if data.hasFormat("text/html"):
    #   if "Cocoa HTML Writer" in data.html():  # Must be SF symbol
    #     print("Found it!!")
    #     html_symbol_code = re.search("&#.+;", data.html()).group()
    #     symbol_text = html.unescape(html_symbol_code)

    #     symbol_image = generate_folder_icon_from_text(FolderStyle.big_sur_light, symbol_text)
    #     self.image.set_image(ImageQt(symbol_image))



    # else check if directory or file with text/uri-list, starts with file://

      # set folder to change if present

      # set image file if it is an image .png .jpg .jpeg .tiff, etc....

    # else must be simple text text/plain, make sure has no url text/uri-list

    elif data.hasFormat("text/plain"):
      symbol_image = generate_folder_icon_from_text(data.text())
      self.image.set_image(ImageQt(symbol_image))

    event.accept()



  def mousePressEvent(self, event: QMouseEvent) -> None:
    focused_widget = QApplication.focusWidget()
    if isinstance(focused_widget, QLineEdit):
      focused_widget.clearFocus()

    super().mousePressEvent(event)


app = QApplication()

window = MainWindow()
window.show()

app.exec()