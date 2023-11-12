from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout
from fancyfolders.ui.components.containerradiobutton import ContainerRadioButton
from fancyfolders.ui.components.customlabel import CustomLabel
from fancyfolders.ui.components.instructionpanel import InstructionPanel
from fancyfolders.ui.components.noneditableline import NonEditableLine


class SaveIconPanel(InstructionPanel):
    """Represents the 3rd instruction panel, containing buttons to save or reset the folder icon
    """

    def __init__(self):
        super().__init__(3, (72, 140, 161))

        # Save icon
        self.generate_button = QPushButton("Save folder icon")
        # TODO: connect to action
        # self.generate_button.clicked.connect(self.generate_and_save_folder)

        # Clear button
        self.clear_button = QPushButton("Reset icon")
        # TODO: connect to action
        # self.clear_button.clicked.connect(self.clear_icon)
        self.clear_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Minimum)

        container = QHBoxLayout()
        container.addWidget(self.generate_button)
        container.addSpacing(5)
        container.addWidget(self.clear_button)

        # Add main container to instruction panel
        self.addLayout(container)