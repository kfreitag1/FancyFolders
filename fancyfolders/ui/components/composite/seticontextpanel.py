from typing import Callable
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit
from fancyfolders.ui.components.customlabel import CustomLabel
from fancyfolders.ui.components.instructionpanel import InstructionPanel


class SetIconTextPanel(InstructionPanel):
    """Represents the 1st instruction panel, containing user input to set icon text 
    """

    def __init__(self, onChange: Callable[[], None]):
        super().__init__(1, (72, 140, 161), "Set folder icon / image / text",
                         extra_spacing=True)

        # Text icon input
        self.iconTextInput = QLineEdit()
        self.iconTextInput.setMaxLength(20)
        self.iconTextInput.setPlaceholderText("icon text")
        self.iconTextInput.setAlignment(Qt.AlignCenter)
        self.iconTextInput.textChanged.connect(lambda _: onChange())

        container = QHBoxLayout()
        container.addWidget(CustomLabel(
            "Drag symbol / image above, or type text:", is_bold=False))
        container.addSpacing(5)
        container.addWidget(self.iconTextInput)

        # Add main container to instruction panel
        self.addLayout(container)

    def getIconText(self):
        return self.iconTextInput.text()
