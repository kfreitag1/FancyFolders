from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit


class NonEditableLine(QLineEdit):
    def __init__(self, placeholder_text):
        super().__init__()

        self.setPlaceholderText(placeholder_text)

        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)

    def set_text(self, text):
        self.text = text
