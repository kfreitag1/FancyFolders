import random
from PySide6.QtCore import QAbstractAnimation, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QAction, QColor, QContextMenuEvent, QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QLineEdit, QMainWindow, QMenu, QPushButton, QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt

from customfoldericons.image_transformations import generate_icon


class CenterIcon(QLabel):
  def __init__(self, image = None):
    super().__init__()

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

    self.label = QLabel("click in the wondow")
    self.label.setMaximumHeight(10)

    self.image = CenterIcon()
    self.image.setText("image")

    self.button = QPushButton("click for image")
    self.button.clicked.connect(self.showImage)

    layout = QVBoxLayout()
    layout.addWidget(self.label)
    layout.addWidget(self.image)
    layout.addWidget(self.button)

    main_widget = QWidget()
    main_widget.setLayout(layout)
    self.setCentralWidget(main_widget)

  def contextMenuEvent(self, event: QContextMenuEvent) -> None:
    context = QMenu(self)
    context.addAction(QAction("test1", self))
    context.addAction(QAction("test2", self))
    context.addSection("poop")
    context.addAction(QAction("test3", self))
    context.addAction(QAction("test4", self))
    context.addSeparator()
    context.addAction(QAction("test5", self))
    context.exec(event.globalPos())

  def showImage(self):
    pil_image = generate_icon("", "")
    temp_image = ImageQt(pil_image)
    self.image.set_image(temp_image)


app = QApplication()

window = MainWindow()
window.show()

app.exec()