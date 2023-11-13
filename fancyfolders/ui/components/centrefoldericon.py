from typing import Optional
from uuid import UUID
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget
from PIL.ImageQt import ImageQt
from PIL.Image import Image

from fancyfolders.constants import FolderStyle
from fancyfolders.external.waitingspinnerwidget import QWaitingSpinner


class CenterFolderIconContainer(QWidget):
    """Container to hold a folder icon and loading spinner.
    """

    MINIMUM_SIZE = (400, 240)
    SPINNER_PADDING = 15
    SPINNER_COLOUR = (109, 176, 126)

    receiving_uuid: UUID = None

    def __init__(self) -> None:
        """Creates a new folder icon container with a new folder icon and spinner
        """
        super().__init__()

        # Ensure minimum size of the center folder icon
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(*self.MINIMUM_SIZE)
        self.setAcceptDrops(True)

        # Z-stack container to hold the folder icon and the spinner on different planes
        self.container = QGridLayout()
        self.container.setContentsMargins(0, 0, 0, 0)

        # Spinner
        spinner_container = QHBoxLayout()
        spinner_container.setContentsMargins(
            self.SPINNER_PADDING, self.SPINNER_PADDING,
            self.SPINNER_PADDING, self.SPINNER_PADDING)
        self.spinner = QWaitingSpinner(
            self, QColor.fromRgb(*self.SPINNER_COLOUR), 80.0,
            0.0, 50.0, 1.5,
            10, 6.0, 6.0, 10.0,
            False)
        spinner_container.addWidget(self.spinner)
        self.container.addLayout(
            spinner_container, 0, 0, Qt.AlignBottom | Qt.AlignRight)

        # Folder icon
        self.folderIcon = CenterFolderIcon()
        self.container.addWidget(self.folderIcon, 0, 0)

        self.setLayout(self.container)

    def setReadyToReceive(self, uuid: UUID):
        """Sets the CenterFolderIcon ready to receive an asynchronously
        generated folder icon with the given unique ID. Once set, will disregard
        the image data received from any previous tasks.

        Args:
            uuid (UUID): Unique ID of latest folder icon generation task
        """
        self.receiving_uuid = uuid
        self.spinner.start()
        # DEBUG
        # print("READY TO RECEIVE " + str(uuid))

    def receive_image_data(self, uuid: UUID, image: Image,
                           folder_style: FolderStyle):
        """Callback from an asynchronous folder icon generation method with a
        given unique ID. If the ID matches the currently accepting one, accepts
        the image data and outputs it to the screen.

        Args:
            uuid (UUID): Unique ID of completed task
            image (Image): Folder icon image
            folder_style (FolderStyle): Folder style of completed folder icon
        """
        if uuid == self.receiving_uuid:
            self.folderIcon.set_folder_image(image, folder_style)
            self.spinner.stop()
            # DEBUG
            # print("ACCEPTING " + str(uuid))
        else:
            pass
            # DEBUG
            # print("DENYING " + str(uuid))


class CenterFolderIcon(QLabel):
    """Displays the preview folder image and scales it when the size of the
    widget changes.
    """

    folder_pixmap: Optional[QPixmap] = None

    # TODO: override drag enter to render a dotted box around to accept drops

    def __init__(self):
        super().__init__()

    def set_folder_image(self, image: Image, folder_style=FolderStyle.big_sur_light):
        """Sets the image on the display.

        Args:
            image (Image): PIL Image to display
            folder_style (FolderStyle): The folder style of the image to set in order to
              crop away any extra space. Defaults to FolderStyle.big_sur_light.
        """

        crop_rect_percentages = folder_style.preview_crop_percentages()
        crop_rect = QRect()
        crop_rect.setCoords(
            *tuple(int(image.size[0] * percent) for percent in crop_rect_percentages))

        # Remove any unnecessary blank space on the image to avoid weird UI layout
        cropped_image: ImageQt = ImageQt(image).copy(crop_rect)

        self.folder_pixmap = QPixmap(cropped_image)
        self.update()

    def paintEvent(self, _: QPaintEvent) -> None:
        """Custom paint event to scale the image when the size of the widget changes.
        """

        if self.folder_pixmap is None:
            return

        dpi_ratio = self.devicePixelRatio()
        self.folder_pixmap.setDevicePixelRatio(dpi_ratio)

        size = QSize(int(self.size().width() * dpi_ratio),
                     int(self.size().height() * dpi_ratio))
        painter = QPainter(self)
        point = QPoint(0, 0)

        scaled_pix = self.folder_pixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        point.setX(int((size.width() - scaled_pix.width())/(2 * dpi_ratio)))
        point.setY(int((size.height() - scaled_pix.height())/(2 * dpi_ratio)))

        painter.drawPixmap(point, scaled_pix)
        painter.end()
