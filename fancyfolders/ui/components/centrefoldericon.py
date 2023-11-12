from uuid import UUID
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy
from PIL.ImageQt import ImageQt
from PIL.Image import Image

from fancyfolders.constants import FolderStyle


class CenterFolderIcon(QLabel):
    """Displays the preview folder image and scales it when the size of the widget changes.
    """

    MINIMUM_SIZE = (400, 240)

    folderPixmap: Image = None
    receivingUUID: UUID = None

    # TODO: override drag enter to render a dotted box around to accept drops
    # TODO: add spinner when about to set folder icon

    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(*self.MINIMUM_SIZE)
        self.setAcceptDrops(True)

    def setReadyToReceive(self, uuid: UUID):
        """Sets the CenterFolderIcon ready to receive an asyncronously generated folder
        icon with the given unique ID. Once set, will disregard the image data received
        from any previous tasks.

        Args:
            uuid (UUID): Unique ID of latest folder icon generation task
        """
        self.receivingUUID = uuid
        # DEBUG
        # print("READY TO RECEIVE " + str(uuid))

    def receiveImageData(self, uuid: UUID, image: Image, folderStyle: FolderStyle):
        """Callback from an asyncronous folder icon generation method with a given unique ID.
        If the ID matches the currently accepting one, accepts the image data and outputs it
        to the screen.

        Args:
            uuid (UUID): Unique ID of completed task
            image (Image): Folder icon image
            folderStyle (FolderStyle): Folder style of completed folder icon
        """
        if uuid == self.receivingUUID:
            self._setFolderImage(image, folderStyle)
            # DEBUG
            # print("ACCEPTING " + str(uuid))
        else:
            pass
            # DEBUG
            # print("DENYING " + str(uuid))

    def _setFolderImage(self, image: Image, folderStyle=FolderStyle.big_sur_light):
        """Sets the image on the display.

        Args:
            image (Image): PIL Image to display
            folder_style (FolderStyle, optional): The folder style of the image to set in order to 
              crop away any extra space. Defaults to FolderStyle.big_sur_light.
        """

        crop_rect_percentages = folderStyle.preview_crop_percentages()
        crop_rect = QRect()
        crop_rect.setCoords(
            *tuple(int(image.size[0] * percent) for percent in crop_rect_percentages))

        # Remove any unnecessary blank space on the image to avoid weird UI layout
        cropped_image = ImageQt(image).copy(crop_rect)

        self.folderPixmap = QPixmap(cropped_image)
        self.update()

    def paintEvent(self, _: QPaintEvent) -> None:
        """Custom paint event to scale the image when the size of the widget changes.
        """

        if self.folderPixmap is None:
            return

        dpi_ratio = self.devicePixelRatio()
        self.folderPixmap.setDevicePixelRatio(dpi_ratio)

        size = QSize(int(self.size().width() * dpi_ratio),
                     int(self.size().height() * dpi_ratio))
        painter = QPainter(self)
        point = QPoint(0, 0)

        scaledPix = self.folderPixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        point.setX(int((size.width() - scaledPix.width())/(2 * dpi_ratio)))
        point.setY(int((size.height() - scaledPix.height())/(2 * dpi_ratio)))

        painter.drawPixmap(point, scaledPix)
        painter.end()
