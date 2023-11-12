from typing import Callable, Optional
from PySide6.QtWidgets import QButtonGroup, QColorDialog, QHBoxLayout
from fancyfolders.constants import TintColour

from fancyfolders.ui.components.colourradiobutton import ColourButtonType, ColourRadioButton


class ColourPalette(QHBoxLayout):
    """Represents a collection of buttons to select a folder tint colour
    """

    def __init__(self, onChange: Callable[[], None]):
        super().__init__()

        self.onChange = onChange

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
            if colour_button.type is ColourButtonType.MULTICOLOUR:
                colour_button.clicked.connect(self._chooseMulticolour)
            else:
                colour_button.clicked.connect(lambda _: onChange())

            self.colour_button_group.addButton(colour_button)
            self.addWidget(colour_button)

        # NO_COLOUR is checked by default
        colour_buttons[0].setChecked(True)

    def _chooseMulticolour(self):
        """Opens a dialog panel to set the multicolour colour
        """
        colour_dialog = QColorDialog()
        if colour_dialog.exec():
            colour = colour_dialog.currentColor()
            self.setMulticolour((colour.red(), colour.green(), colour.blue()))

    def setMulticolour(self, colour: tuple[int, int, int]):
        """Sets the multicolour and calls the update callback

        Args:
            colour (tuple[int, int, int]): The colour to set
        """
        self.current_multicolour = colour
        self.onChange()

    def getColour(self) -> Optional[tuple[int, int, int]]:
        """Gets the current colour selected by the palette

        Raises:
            ValueError: If checked button is not one of the expected types

        Returns:
            Optional[tuple[int, int, int]]: The selected colour, or None
        """
        checked_button: ColourRadioButton = self.colour_button_group.checkedButton()

        if checked_button.type is ColourButtonType.COLOUR:
            return checked_button.colour
        elif checked_button.type is ColourButtonType.NO_COLOUR:
            return None
        elif checked_button.type is ColourButtonType.MULTICOLOUR:
            return self.current_multicolour

        raise ValueError("ColourButtonType is not one of the expected types")
