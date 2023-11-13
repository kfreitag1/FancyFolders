import os
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QFileDialog, QHBoxLayout, QVBoxLayout

from fancyfolders.ui.components.containerradiobutton import ContainerRadioButton
from fancyfolders.ui.components.customlabel import CustomLabel
from fancyfolders.ui.components.instructionpanel import InstructionPanel
from fancyfolders.ui.components.noneditableline import NonEditableLine


class SetLocationPanel(InstructionPanel):
    """Represents the 2nd instruction panel, containing fields to gather user
    input relating to where the folder will be generated
    """

    existing_folder_filepath = None
    new_location_filepath = os.path.join(
        os.path.join(os.path.expanduser("~")), "Desktop")

    def __init__(self):
        """Constructs a new location instruction panel"""
        super().__init__(2, (72, 140, 161),
                         "Set folder to change, or location to make new folder",
                         extra_spacing=True)

        # Folder to change field
        self.existing_folder_name_field = NonEditableLine("Drag folder above")

        # New folder output label, field, selector button
        self.new_folder_location = NonEditableLine("")
        self.new_folder_location.setCursor(Qt.PointingHandCursor)
        self.new_folder_location.mousePressEvent = lambda _: self._open_file_picker()

        self.radio_buttons = QButtonGroup(self)

        existing_folder_layout = QHBoxLayout()
        existing_folder_layout.addWidget(CustomLabel(
            "Change existing folder:", is_bold=False))
        existing_folder_layout.addWidget(self.existing_folder_name_field)
        self.existing_folder_radio = ContainerRadioButton(
            existing_folder_layout, self.radio_buttons, self)

        new_location_layout = QHBoxLayout()
        new_location_layout.setAlignment(Qt.AlignVCenter)
        new_location_layout.addWidget(CustomLabel(
            "Make a new folder in:", is_bold=False))
        new_location_layout.addWidget(self.new_folder_location)
        self.new_location_radio = ContainerRadioButton(
            new_location_layout, self.radio_buttons, self, is_default=True)

        container = QVBoxLayout()
        container.addWidget(self.existing_folder_radio)
        container.addWidget(self.new_location_radio)

        self._update_ui()

        # Add main container to instruction panel
        self.addLayout(container)

    def _open_file_picker(self):
        """Opens a file picker window to select an output directory for new folders."""
        file_picker_dialog = QFileDialog(self)
        file_picker_dialog.setFileMode(QFileDialog.Directory)
        file_picker_dialog.setAcceptMode(QFileDialog.AcceptOpen)

        if file_picker_dialog.exec():
            path = file_picker_dialog.selectedFiles()[0]
            self.set_new_folder_location_filepath(path)

    def _update_ui(self):
        """Updates the UI to reflect the data that was set
        """
        # Enable the existing folder filepath option if it is set
        self.existing_folder_radio.setEnabled(
            self.existing_folder_filepath is not None)
        if self.existing_folder_filepath is not None:
            print(os.path.basename(self.existing_folder_filepath))
            print(self.existing_folder_filepath)

        # Update the folder names in the fields based on the stored filepaths
        self.existing_folder_name_field.setText(
            None if self.existing_folder_filepath is None else
            os.path.basename(self.existing_folder_filepath))
        self.new_folder_location.setText(
            os.path.basename(self.new_location_filepath))

    def set_existing_folder_filepath(self, filepath: Optional[str]) -> None:
        """Sets the filepath to an existing folder that the user wishes
        to have the icon set

        :param filepath: Filepath, or None to remove previous filepath
        """
        self.existing_folder_filepath = filepath
        if filepath is not None:
            self.existing_folder_radio.setChecked(True)
        else:
            self.new_location_radio.setChecked(True)
        self._update_ui()

    def set_new_folder_location_filepath(self, filepath: str) -> None:
        """Sets the filepath to the location in which the new folder
        will be generated in

        :param filepath: Filepath
        :return:
        """
        self.new_location_filepath = filepath
        self.new_location_radio.setChecked(True)
        self._update_ui()

    def get_output_info(self) -> tuple[bool, str]:
        """Returns a filepath and whether the filepath represents an existing
        folder or a location to generate a new folder. True corresponds to a
        new location

        :return: Is the filepath a new location?, Filepath
        :raises ValueError: Thrown if the checked button was not one of the
            two radio buttons
        """
        if self.existing_folder_radio.isChecked():
            return False, self.existing_folder_filepath
        elif self.new_location_radio.isChecked():
            return True, self.new_location_filepath
        else:
            raise ValueError("Invalid checked button")
