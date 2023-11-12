import math
from typing import Optional
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QBrush, QColor, QPaintEvent, QPainter, QPalette, QPen
from PySide6.QtWidgets import QLabel, QSizePolicy


class NonEditableLine(QLabel):
    """Represents a non-editable text field with background and placeholder text.
    """

    BACKGROUND_COLOUR = QColor.fromRgb(255, 255, 255)
    PLACEHOLDER_COLOUR = QColor.fromRgb(200, 200, 200)
    TEXT_COLOUR = QColor.fromRgb(0, 0, 0)

    def __init__(self, placeholderText):
        super().__init__()

        # Store a reference of placeholder to set when text is empty
        self.placeholderText = placeholderText

        self.setMinimumHeight(20)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum
        )

    def setText(self, text: Optional[str]):
        """Sets the text of the label, or clears if given None. When cleared
        the placeholder text is shown.

        Args:
            text (Optional[str]): Text to display, or None
        """
        super().setText(text if text is not None else self.placeholderText)

        if text is None:
            self._setTextColour(self.PLACEHOLDER_COLOUR)
        else:
            self._setTextColour(self.TEXT_COLOUR)

    def _setTextColour(self, colour: QColor):
        """Convenience method to set the colour of the displayed text.

        Args:
            colour (QColor): New text colour
        """
        palette = self.palette()
        palette.setColor(QPalette.WindowText, colour)
        self.setPalette(palette)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Overriden paint event to add a custom rounded rectangle background

        Args:
            event (QPaintEvent): Paint event to pass through
        """
        width = self.size().width()
        height = self.size().height()
        cornerRadius = math.floor(height / 2)

        maxRect = QRect(0, 0, width, height)

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.Antialiasing)

            # Solid background rounded rectangle
            brush = QBrush(self.BACKGROUND_COLOUR, Qt.SolidPattern)
            painter.setBrush(brush)
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(maxRect, cornerRadius, cornerRadius)

        # Call parent paint event to draw the text overtop the background
        super().paintEvent(event)
