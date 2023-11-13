from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLayout, QVBoxLayout

from fancyfolders.constants import VERSION
from fancyfolders.utilities import internal_resource_path


class AboutPanel(QDialog):
    """Represents an 'about panel' for the Fancy Folders application"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("About Fancy Folders")

        app_icon_image = QPixmap(internal_resource_path("assets/app_icon.png"))
        dpi_ratio = self.devicePixelRatio()
        app_icon_image.setDevicePixelRatio(dpi_ratio)

        size = QSize(int(80 * dpi_ratio), int(80 * dpi_ratio))

        self.icon = QLabel()
        self.icon.setPixmap(app_icon_image.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # self.icon.setScaledContents(True)

        self.version_string = QLabel("Version " + VERSION)
        self.version_string.setAlignment(Qt.AlignCenter)
        self.version_string.setMinimumWidth(200)

        self.description = QLabel("Made by Kieran Freitag")
        self.description.setStyleSheet("font-style: italic")

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.addWidget(self.icon, alignment=Qt.AlignCenter)
        layout.addWidget(self.version_string, alignment=Qt.AlignCenter)
        layout.addWidget(self.description, alignment=Qt.AlignCenter)
        self.setLayout(layout)
