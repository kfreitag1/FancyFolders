from enum import Enum
from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import QRadioButton

from fancyfolders.constants import TintColour


class ColourButtonType(Enum):
    COLOUR = 0,
    NO_COLOUR = 1,
    MULTICOLOUR = 2


class ColourRadioButton(QRadioButton):
    """Custom button used in the colour palette selector for folder tint."""

    BORDER_RADIUS = 5.0
    ACTIVE_BORDER_WIDTH = 3.0
    INACTIVE_BORDER_WIDTH = 2.0

    INACTIVE_BORDER_COLOUR = (212, 212, 212)
    ACTIVE_BORDER_COLOUR = (100, 198, 237)

    EMPTY_FILL_COLOUR = (255, 255, 255)

    def __init__(self, button_type: ColourButtonType,
                 colour: Optional[tuple[int, int, int]] = None) -> None:
        """Constructs a new colour radio button with the specified type

        :param button_type: Whether the button represents a regular color,
            no colour, or a multicolour option
        :param colour: Colour to set (r, g, b), or None
        """
        super().__init__()

        self.colour = colour
        self.type = button_type

        self.setMinimumHeight(30)

    def hitButton(self, point: QPoint) -> bool:
        """Changes the area where the button is clickable."""
        return self._get_center_square().contains(point)

    def paintEvent(self, _: QPaintEvent) -> None:
        """Custom paint event to draw the colour button using either the colour, or
        special style as specified in the init.
        """
        center_rect = self._get_center_square()

        border_width = self.ACTIVE_BORDER_WIDTH if self.isChecked(
        ) else self.INACTIVE_BORDER_WIDTH
        border_colour = self.ACTIVE_BORDER_COLOUR if self.isChecked(
        ) else self.INACTIVE_BORDER_COLOUR

        fill_colour = self.colour if self.colour is not None else self.EMPTY_FILL_COLOUR

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        outline_pen = QPen()
        outline_pen.setWidth(border_width)
        outline_pen.setColor(QColor.fromRgb(*border_colour))

        fill_brush = QBrush()
        fill_brush.setColor(QColor.fromRgb(*fill_colour))
        fill_brush.setStyle(Qt.SolidPattern)

        painter.setPen(outline_pen)
        painter.setBrush(fill_brush)

        border_offset = border_width * 0.8
        painter.drawRoundedRect(
            center_rect.adjusted(
                border_offset, border_offset, -border_offset, -border_offset),
            self.BORDER_RADIUS - border_offset, self.BORDER_RADIUS - border_offset
        )

        # Draw custom features for the default option
        if self.type is ColourButtonType.NO_COLOUR:
            dash_pen = QPen()
            dash_pen.setColor(QColor.fromRgb(*self.INACTIVE_BORDER_COLOUR))
            dash_pen.setCapStyle(Qt.RoundCap)
            dash_pen.setWidth(3)

            painter.setPen(dash_pen)

            start_point = center_rect.topLeft() + QPoint(8, 8)
            end_point = center_rect.bottomRight() + QPoint(-8, -8)

            painter.drawLine(start_point, end_point)

        # Draw custom feature for the custom colour option
        elif self.type is ColourButtonType.MULTICOLOUR:
            center_point = center_rect.center()
            rainbow_gradient = QConicalGradient(center_point, 0)
            rainbow_gradient.setColorAt(0.0, QColor(*TintColour.red.value))
            rainbow_gradient.setColorAt(0.2, QColor(*TintColour.yellow.value))
            rainbow_gradient.setColorAt(0.5, QColor(*TintColour.orange.value))
            rainbow_gradient.setColorAt(0.8, QColor(*TintColour.purple.value))
            rainbow_gradient.setColorAt(1.0, QColor(*TintColour.red.value))

            rainbow_pen = QPen(rainbow_gradient, 5.0)

            painter.setPen(rainbow_pen)
            painter.setBrush(Qt.NoBrush)

            painter.drawEllipse(center_point + QPoint(1, 1), 6, 6)

        painter.end()

    def _get_center_square(self) -> QRect:
        """Returns the square contained within the center of the widget size.
        Requires that the width is greater than the height

        :return: Rect containing the center square
        """
        size = self.size()

        width_adjustment = (size.width() - size.height()) / 2
        total_rect = QRect(QPoint(0, 0), size)

        return total_rect.adjusted(width_adjustment, 0, -width_adjustment, 0)
