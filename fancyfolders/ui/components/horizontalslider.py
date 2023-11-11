from enum import Enum
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider


class TickStyle(Enum):
    NONE = 0
    CENTER = 1
    EACH = 2


class HorizontalSlider(QSlider):
    def __init__(self, max_ticks, start_value=0, tick_style=TickStyle.NONE):
        super().__init__(Qt.Horizontal)

        self.setMinimum(1)
        self.setMaximum(max_ticks)
        self.setMinimumHeight(50)
        self.setValue(start_value)
        self.setTracking(True)

        self.setTickPosition(
            QSlider.NoTicks if tick_style is TickStyle.NONE else QSlider.TicksBelow)

        if tick_style is TickStyle.CENTER:
            self.setTickInterval(max_ticks + 1)
        elif tick_style is TickStyle.EACH:
            self.setTickInterval(1)
