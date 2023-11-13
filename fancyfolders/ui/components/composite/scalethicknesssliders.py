from typing import Callable

from PySide6.QtWidgets import QHBoxLayout

from fancyfolders.constants import (
    DEFAULT_FONT, ICON_SCALE_SLIDER_MAX, MAXIMUM_ICON_SCALE_VALUE,
    MINIMUM_ICON_SCALE_VALUE, SFFont)
from fancyfolders.ui.components.horizontalslider import HorizontalSlider, TickStyle
from fancyfolders.utilities import interpolate_int_to_float_with_midpoint


class ScaleThicknessSliders(QHBoxLayout):
    """Represents a group of two user input sliders to obtain icon scale
    and thickness
    """

    def __init__(self, on_change: Callable[[], None]) -> None:
        """Constructs a new widget containing scale and thickness sliders

        :param on_change: Callback to run whenever a change is made
        """
        super().__init__()

        # Icon scale slider
        self.scale_slider = HorizontalSlider(
            label="Scale",
            total_num_ticks=ICON_SCALE_SLIDER_MAX,
            initial_value=int((ICON_SCALE_SLIDER_MAX - 1) / 2) + 1,
            tick_style=TickStyle.CENTER)
        self.scale_slider.slider.valueChanged.connect(lambda _: on_change())
        self.addLayout(self.scale_slider)

        # Thickness slider
        self.thickness_slider = HorizontalSlider(
            label="Thickness", total_num_ticks=len(SFFont),
            initial_value=DEFAULT_FONT.value, tick_style=TickStyle.EACH)
        self.thickness_slider.slider.valueChanged.connect(lambda _: on_change())
        self.addLayout(self.thickness_slider)

    def get_scale(self) -> float:
        """Gets the selected icon scale, normalized to predetermined range

        :return: The icon scale
        """
        return interpolate_int_to_float_with_midpoint(
            self.scale_slider.slider.value(), 1, ICON_SCALE_SLIDER_MAX,
            MINIMUM_ICON_SCALE_VALUE, 1.0, MAXIMUM_ICON_SCALE_VALUE)

    def get_thickness(self) -> SFFont:
        """Gets the selected thickness

        :return: Enum representing font thickness
        """
        return SFFont(self.thickness_slider.slider.value())

    def reset(self) -> None:
        self.scale_slider.setValue(int((ICON_SCALE_SLIDER_MAX - 1) / 2) + 1)
        self.thickness_slider.setValue(DEFAULT_FONT.value)
