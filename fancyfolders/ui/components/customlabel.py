from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QLabel


class CustomLabel(QLabel):
    """Represents a label with a custom colour and boldness state, defaults to white and bold.
    """

    def __init__(self, text: str, colour: QColor = QColor.fromRgb(255, 255, 255),
                 is_bold: bool = True):
        super().__init__(text)

        font = self.font()
        font.setBold(is_bold)
        self.setFont(font)

        palette = self.palette()
        palette.setColor(QPalette.WindowText, colour)
        self.setPalette(palette)
