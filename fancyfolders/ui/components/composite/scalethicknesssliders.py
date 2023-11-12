from typing import Callable
from PySide6.QtWidgets import QHBoxLayout

from fancyfolders.constants import DEFAULT_FONT, ICON_SCALE_SLIDER_MAX, MAXIMUM_ICON_SCALE_VALUE, MINIMUM_ICON_SCALE_VALUE, SFFont
from fancyfolders.ui.components.horizontalslider import HorizontalSlider, TickStyle
from fancyfolders.utilities import interpolate_int_to_float_with_midpoint


class ScaleThicknessSliders(QHBoxLayout):
    """Represents a group of two user input sliders to obtain icon scale and thickness
    """

    def __init__(self, onChange: Callable[[], None]):
        super().__init__()

        # Icon scale slider
        self.scale_slider = HorizontalSlider(
            "Scale", ICON_SCALE_SLIDER_MAX, int(
                (ICON_SCALE_SLIDER_MAX - 1)/2) + 1,
            TickStyle.CENTER)
        self.scale_slider.slider.valueChanged.connect(lambda _: onChange())
        self.addLayout(self.scale_slider)

        # Font weight slider
        self.font_weight_slider = HorizontalSlider(
            "Thickness", len(SFFont), DEFAULT_FONT.value, TickStyle.EACH)
        self.font_weight_slider.slider.valueChanged.connect(
            lambda _: onChange())
        self.addLayout(self.font_weight_slider)

    def getScale(self) -> float:
        """Gets the selected icon scale, normalized to predetermined range

        Returns:
            float: The icon scale
        """
        return interpolate_int_to_float_with_midpoint(
            self.scale_slider.slider.value(), 1, ICON_SCALE_SLIDER_MAX,
            MINIMUM_ICON_SCALE_VALUE, 1.0, MAXIMUM_ICON_SCALE_VALUE
        )

    def getThickness(self) -> SFFont:
        """Gets the selected thickness.

        Returns:
            SFFont: Enum representing font thickness
        """
        return SFFont(self.font_weight_slider.slider.value())
