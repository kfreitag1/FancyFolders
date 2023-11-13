from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit

from fancyfolders.constants import MAIN_PANEL_COLOUR
from fancyfolders.ui.components.customlabel import CustomLabel
from fancyfolders.ui.components.instructionpanel import InstructionPanel


class SetIconTextPanel(InstructionPanel):
    """Represents the 1st instruction panel, containing user input to set
    icon text
    """

    def __init__(self, on_change: Callable[[], None]) -> None:
        """Constructs a new text instruction panel

        :param on_change: Callback to run whenever the text is edited
        """
        super().__init__(1, MAIN_PANEL_COLOUR,
                         "Set folder icon / image / text",
                         extra_spacing=True)

        # Text icon input
        self.icon_text_input = QLineEdit()
        self.icon_text_input.setMaxLength(20)
        self.icon_text_input.setPlaceholderText("icon text")
        self.icon_text_input.setAlignment(Qt.AlignCenter)
        self.icon_text_input.textChanged.connect(lambda _: on_change())

        container = QHBoxLayout()
        container.addWidget(CustomLabel(
            "Drag symbol / image above, or type text:", is_bold=False))
        container.addSpacing(5)
        container.addWidget(self.icon_text_input)

        # Add main container to instruction panel
        self.addLayout(container)

    def get_icon_text(self) -> str:
        return self.icon_text_input.text()

    def reset(self) -> None:
        self.icon_text_input.setText("")
