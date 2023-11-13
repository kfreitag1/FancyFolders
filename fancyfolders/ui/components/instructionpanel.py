import math

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import QLayout, QVBoxLayout, QWidget

from fancyfolders.ui.components.customlabel import CustomLabel


class InstructionPanel(QWidget):
    """Represents a panel containing a layout with a custom background and
    index number
    """

    CIRCLE_RADIUS = 14
    SPACING = 4

    def __init__(self, index: int, colour: tuple[int, int, int],
                 title: str = None, extra_spacing=False) -> None:
        """Constructs a new InstructionPanel with the given index number, colour,
        and layout object containing children elements to hold within the panel

        :param index: Number to show in circle on the left
        :param colour: Colour of the panel (r, g, b)
        :param title: Optional title of the panel
        :param extra_spacing: Should there be extra spacing on bottom?
        """
        super().__init__()

        self.index = index
        self.colour = colour

        # Wrapping layout to add title if desired
        self.wrap_layout = QVBoxLayout()
        self.wrap_layout.setContentsMargins(
            self.SPACING * 2, math.floor(self.SPACING * 1.5), self.SPACING * 2,
            self.SPACING * 2 if extra_spacing else 0)
        self.wrap_layout.setSpacing(0)

        if title is not None:
            self.wrap_layout.addWidget(CustomLabel(title))

        self.setLayout(self.wrap_layout)

        # Ensure child elements are not overlapping the circle on the left
        self.setContentsMargins(math.floor(self.CIRCLE_RADIUS * 2), 0, 0, 0)

    def addLayout(self, layout: QLayout) -> None:
        """Passthrough method to add a layout to the container

        :param layout: Child layout to add
        """
        self.wrap_layout.addLayout(layout)

    def paintEvent(self, _: QPaintEvent) -> None:
        """Override paint event to draw a custom background for the
        instruction panel

        :param _: Unused paint event object
        """
        width = self.size().width()
        height = self.size().height()

        max_rect = QRect(0, 0, width, height)
        inset_rect = max_rect.adjusted(self.CIRCLE_RADIUS + 2, 1, -1, -1)
        circle_bounds = QRect(QPoint(2, math.floor(height / 2) - self.CIRCLE_RADIUS),
                              QSize(self.CIRCLE_RADIUS * 2, self.CIRCLE_RADIUS * 2))

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.Antialiasing)

            # Outline and fill pens are the same colour to blend into each other
            outline_pen = QPen(QColor.fromRgb(*self.colour), 3, Qt.SolidLine,
                               Qt.RoundCap, Qt.RoundJoin)
            brush = QBrush(QColor.fromRgb(*self.colour), Qt.SolidPattern)

            # Solid background colour
            painter.setBrush(brush)
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(inset_rect, 5, 5)

            # Circle with white center on left side of box (in center vertically)
            painter.setPen(outline_pen)
            painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
            painter.drawEllipse(circle_bounds)

            # Index number in the center of the circle, same colour
            font = QFont()
            font.setStyleHint(QFont.SansSerif)
            font.setBold(True)
            font.setPointSize(math.floor(self.CIRCLE_RADIUS * 1.2))
            painter.setFont(font)
            painter.drawText(circle_bounds, Qt.AlignHCenter |
                             Qt.AlignVCenter, str(self.index))
