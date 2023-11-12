from enum import Enum
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QSlider, QVBoxLayout


class TickStyle(Enum):
    NONE = 0
    CENTER = 1
    EACH = 2


class HorizontalSlider(QGridLayout):
    """Represents a horizontal slider input with the given label above it
    """

    def __init__(self, label: str, max_ticks: int, start_value=0, tick_style=TickStyle.NONE):
        super().__init__()

        # Label above the slider
        self.label = QLabel(label)
        self.label.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.label.setAlignment(Qt.AlignHCenter)
        self.label.setMinimumHeight(52)
        self.addWidget(self.label, 0, 0)

        # Construct horizontal slider with given parameters
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(max_ticks)
        self.slider.setMinimumHeight(45)
        self.slider.setValue(start_value)
        self.slider.setTracking(True)

        self.slider.setTickPosition(
            QSlider.NoTicks if tick_style is TickStyle.NONE else QSlider.TicksBelow)

        if tick_style is TickStyle.CENTER:
            self.slider.setTickInterval(max_ticks + 1)
        elif tick_style is TickStyle.EACH:
            self.slider.setTickInterval(1)

        self.addWidget(self.slider, 0, 0, Qt.AlignBottom)

    def getValue(self) -> int:
        return self.slider.value()
