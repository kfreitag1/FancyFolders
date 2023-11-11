from enum import Enum
from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QPaintEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLayout, QLineEdit, QRadioButton, QSizePolicy, QSlider, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt

from fancyfolders.constants import VERSION, FolderStyle, TintColour
from fancyfolders.utilities import internal_resource_path


class CenterFolderIcon(QLabel):
    """Displays the preview folder image and scales it when the size of the widget changes.
    """

    MINIMUM_SIZE = (400, 340)

    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(*self.MINIMUM_SIZE)
        self.setAcceptDrops(True)

    def set_image(self, image, folder_style=FolderStyle.big_sur_light):
        """Sets the image on the display.

        Args:
            image (Image): PIL Image to display
            folder_style (FolderStyle, optional): The folder style of the image to set in order to 
              crop away any extra space. Defaults to FolderStyle.big_sur_light.
        """
        crop_rect_percentages = folder_style.preview_crop_percentages()
        crop_rect = QRect()
        crop_rect.setCoords(
            *tuple(int(image.size[0] * percent) for percent in crop_rect_percentages))

        # Remove any unnecessary blank space on the image to avoid weird UI layout
        cropped_image = ImageQt(image).copy(crop_rect)

        self.pixmap = QPixmap(cropped_image)
        self.update()

    def paintEvent(self, _: QPaintEvent) -> None:
        """Custom paint event to scale the image when the size of the widget changes.
        """
        dpi_ratio = self.devicePixelRatio()
        self.pixmap.setDevicePixelRatio(dpi_ratio)

        size = QSize(int(self.size().width() * dpi_ratio),
                     int(self.size().height() * dpi_ratio))
        painter = QPainter(self)
        point = QPoint(0, 0)

        scaledPix = self.pixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        point.setX(int((size.width() - scaledPix.width())/(2 * dpi_ratio)))
        point.setY(int((size.height() - scaledPix.height())/(2 * dpi_ratio)))

        painter.drawPixmap(point, scaledPix)
        painter.end()
