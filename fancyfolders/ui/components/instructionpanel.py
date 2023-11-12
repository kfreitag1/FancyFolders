import math
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import QLayout, QVBoxLayout, QWidget

from fancyfolders.ui.components.customlabel import CustomLabel


class InstructionPanel(QWidget):
    """Represents a panel containing a layout with a custom background and index number
    """

    CIRCLE_RADIUS = 14
    SPACING = 4

    def __init__(self, index: int, colour: tuple[int, int, int],
                 title: str = None, extra_spacing=False) -> None:
        """Constructs a new InstructionPanel with the given index number, colour,
        and layout object containing children elements to hold within the panel.

        Args:
            index (int): Number to show in circle on the left
            colour (tuple[int, int, int]): Key colour of the panel
            layout (QLayout): Children elements
        """
        super().__init__()

        self.index = index
        self.colour = colour

        # Wrapping layout to add title if desired
        self.wrapLayout = QVBoxLayout()
        self.wrapLayout.setContentsMargins(
            self.SPACING * 2, math.floor(self.SPACING * 1.5), self.SPACING * 2,
            self.SPACING * 2 if extra_spacing else 0)
        self.wrapLayout.setSpacing(0)

        if (title is not None):
            self.wrapLayout.addWidget(CustomLabel(title))

        # Correct spacing of layout with children elemnts and add them
        # layout.setSpacing(0)
        self.setLayout(self.wrapLayout)

        # Ensure child elements are not overlapping the circle on the left
        self.setContentsMargins(math.floor(self.CIRCLE_RADIUS * 2), 0, 0, 0)

    def addLayout(self, layout: QLayout):
        """Passthrough method to add a layout to the container

        Args:
            layout (QLayout): Layout to add
        """
        self.wrapLayout.addLayout(layout)

    def paintEvent(self, _: QPaintEvent) -> None:
        """Override paint event to draw a custom background for the instruction panel

        Args:
            _ (QPaintEvent): Unused paint event object
        """
        width = self.size().width()
        height = self.size().height()

        maxRect = QRect(0, 0, width, height)
        insetRect = maxRect.adjusted(self.CIRCLE_RADIUS + 2, 1, -1, -1)
        circleBounds = QRect(QPoint(2, math.floor(height / 2) - self.CIRCLE_RADIUS),
                             QSize(self.CIRCLE_RADIUS * 2, self.CIRCLE_RADIUS * 2))

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.Antialiasing)

            # Outline and fill pens are the same colour to blend into eachother
            outline_pen = QPen(QColor.fromRgb(*self.colour), 3, Qt.SolidLine,
                               Qt.RoundCap, Qt.RoundJoin)
            brush = QBrush(QColor.fromRgb(*self.colour), Qt.SolidPattern)

            # Solid background colour
            painter.setBrush(brush)
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(insetRect, 5, 5)

            # Circle with white center on left side of box (in center vertically)
            painter.setPen(outline_pen)
            painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
            painter.drawEllipse(circleBounds)

            # Index number in the center of the circle, same colour
            font = QFont()
            font.setStyleHint(QFont.SansSerif)
            font.setBold(True)
            font.setPointSize(math.floor(self.CIRCLE_RADIUS * 1.2))
            painter.setFont(font)
            painter.drawText(circleBounds, Qt.AlignHCenter |
                             Qt.AlignVCenter, str(self.index))
