from typing import Callable, Optional

from PySide6.QtWidgets import QButtonGroup, QColorDialog, QHBoxLayout

from fancyfolders.constants import TintColour
from fancyfolders.ui.components.colourradiobutton import ColourButtonType, ColourRadioButton


class ColourPalette(QHBoxLayout):
    """Represents a collection of buttons to select a folder tint colour"""

    def __init__(self, on_change: Callable[[], None]):
        """Constructs a new colour palette

        :param on_change: Callback to run whenever a selection is made
        """
        super().__init__()

        self.on_change = on_change

        # Variable to store current multicolour choice
        self.current_multicolour = None

        # Button group containing all selectable colour radio buttons
        self.colour_button_group = QButtonGroup()

        # Create group of buttons, in order
        self.colour_buttons = [ColourRadioButton(button_type=ColourButtonType.NO_COLOUR)]
        self.colour_buttons += [ColourRadioButton(
            button_type=ColourButtonType.COLOUR, colour=tint_colour.value)
            for tint_colour in TintColour]
        self.colour_buttons += [ColourRadioButton(button_type=ColourButtonType.MULTICOLOUR)]

        for colour_button in self.colour_buttons:
            # Add on click events to all the buttons, multicolour is special
            if colour_button.type is ColourButtonType.MULTICOLOUR:
                colour_button.clicked.connect(self._choose_multicolour)
            else:
                colour_button.clicked.connect(lambda _: on_change())

            # Add the buttons to the button group and the parent component
            self.colour_button_group.addButton(colour_button)
            self.addWidget(colour_button)

        # No colour is checked by default
        self.reset()

    def _choose_multicolour(self):
        """Opens a dialog panel to set the multicolour colour"""
        colour_dialog = QColorDialog()
        if colour_dialog.exec():
            colour = colour_dialog.currentColor()
            self.set_multicolour((colour.red(), colour.green(), colour.blue()))

    def set_multicolour(self, colour: tuple[int, int, int]) -> None:
        """Sets the multicolour and calls the update callback

        :param colour: The colour to set (r, g, b)
        """
        self.current_multicolour = colour
        self.on_change()

    def get_colour(self) -> Optional[tuple[int, int, int]]:
        """Gets the current colour selected by the palette

        :return: The selected colour (r, g, b), or None
        :raises ValueError: If checked button is not one of the expected types
        """
        checked_button: ColourRadioButton = self.colour_button_group.checkedButton()

        if checked_button.type is ColourButtonType.COLOUR:
            return checked_button.colour
        elif checked_button.type is ColourButtonType.NO_COLOUR:
            return None
        elif checked_button.type is ColourButtonType.MULTICOLOUR:
            return self.current_multicolour

        raise ValueError("ColourButtonType is not one of the expected types")

    def reset(self) -> None:
        self.colour_buttons[0].setChecked(True)
