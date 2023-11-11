from typing import Callable, Optional
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout
from fancyfolders.constants import TintColour

from fancyfolders.ui.components.colourradiobutton import ColourButtonType, ColourRadioButton


class ColourPalette(QHBoxLayout):
    def __init__(self, select_colour: Callable[[], None]):
        super().__init__()

        # Variable to store current multicolour choice
        self.current_multicolour = None

        # Button group containing all selectable colour radio buttons
        self.colour_button_group = QButtonGroup()

        # Create group of buttons, in order: NO_COLOUR ... COLOURs ... MULTICOLOUR
        colour_buttons = []
        colour_buttons.append(ColourRadioButton(
            type=ColourButtonType.NO_COLOUR))
        for tint_colour in TintColour:
            colour_buttons.append(ColourRadioButton(
                type=ColourButtonType.COLOUR, colour=tint_colour.value))
        colour_buttons.append(ColourRadioButton(
            type=ColourButtonType.MULTICOLOUR))

        for colour_button in colour_buttons:
            colour_button.clicked.connect(select_colour)
            self.colour_button_group.addButton(colour_button)
            self.addWidget(colour_button)

        # NO_COLOUR is checked by default
        colour_buttons[0].setChecked(True)

    def setMulticolour(self, colour: tuple[int, int, int]):
        self.current_multicolour = colour

    def getColour(self) -> Optional[tuple[int, int, int]]:
        checked_button: ColourRadioButton = self.colour_button_group.checkedButton()

        if checked_button.type is ColourButtonType.COLOUR:
            return checked_button.colour
        elif checked_button.type is ColourButtonType.NO_COLOUR:
            return None
        elif checked_button.type is ColourButtonType.MULTICOLOUR:
            return self.current_multicolour

        raise ValueError("ColourButtonType is not one of the expected types")
