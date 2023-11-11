from typing import Callable
from PySide6.QtWidgets import QHBoxLayout

from fancyfolders.constants import DEFAULT_FONT, ICON_SCALE_SLIDER_MAX, MAXIMUM_ICON_SCALE_VALUE, MINIMUM_ICON_SCALE_VALUE, SFFont
from fancyfolders.ui.components.horizontalslider import HorizontalSlider, TickStyle
from fancyfolders.utilities import interpolate_int_to_float_with_midpoint


class ScaleThicknessSliders(QHBoxLayout):
    def __init__(self, scale_change: Callable[[int], None], font_change: Callable[[SFFont], None]):
        super().__init__()

        # Icon scale slider
        self.scale_slider = HorizontalSlider(ICON_SCALE_SLIDER_MAX, int(
            (ICON_SCALE_SLIDER_MAX - 1)/2) + 1, TickStyle.CENTER)
        self.scale_slider.valueChanged.connect(scale_change)
        self.addWidget(self.scale_slider)

        # Font weight slider
        self.font_weight_slider = HorizontalSlider(
            len(SFFont), DEFAULT_FONT.value, TickStyle.EACH)
        self.font_weight_slider.valueChanged.connect(font_change)
        self.addWidget(self.font_weight_slider)

    def getScale(self) -> float:
        return interpolate_int_to_float_with_midpoint(
            self.scale_slider.value, 1, ICON_SCALE_SLIDER_MAX,
            MINIMUM_ICON_SCALE_VALUE, 1.0, MAXIMUM_ICON_SCALE_VALUE
        )

    def getThickness(self) -> SFFont:
        return self.font_weight_slider.value
