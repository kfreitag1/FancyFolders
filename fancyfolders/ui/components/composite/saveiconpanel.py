from typing import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy

from fancyfolders.constants import MAIN_PANEL_COLOUR
from fancyfolders.ui.components.instructionpanel import InstructionPanel


class SaveIconPanel(InstructionPanel):
    """Represents the 3rd instruction panel, containing buttons to save or
    reset the folder icon
    """

    def __init__(self, on_save: Callable[[], None],
                 on_clear: Callable[[], None]) -> None:
        super().__init__(3, MAIN_PANEL_COLOUR)

        # Save icon
        self.generate_button = QPushButton("Save folder icon")
        self.generate_button.clicked.connect(on_save)

        # Clear button
        self.clear_button = QPushButton("Reset icon")
        self.clear_button.clicked.connect(on_clear)
        self.clear_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Minimum)

        container = QHBoxLayout()
        container.addWidget(self.generate_button)
        container.addSpacing(5)
        container.addWidget(self.clear_button)

        # Add main container to instruction panel
        self.addLayout(container)
