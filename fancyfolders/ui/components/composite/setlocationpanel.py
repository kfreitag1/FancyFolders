import os
from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QButtonGroup, QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout
from fancyfolders.ui.components.containerradiobutton import ContainerRadioButton
from fancyfolders.ui.components.customlabel import CustomLabel
from fancyfolders.ui.components.instructionpanel import InstructionPanel
from fancyfolders.ui.components.noneditableline import NonEditableLine


class SetLocationPanel(InstructionPanel):
    """Represents the 2nd instruction panel, containing fields to gather user input relating
    to where the folder will be generated
    """

    existingFolderFilepath = None
    newLocationFilepath = os.path.join(
        os.path.join(os.path.expanduser("~")), "Desktop")

    def __init__(self, update: Callable[[], None]):
        super().__init__(2, (72, 140, 161),
                         "Set folder to change, or location to make new folder",
                         extra_spacing=True)

        self.callback = update

        # Folder to change field
        self.existingFolderName = NonEditableLine("Drag folder above")

        # New folder output label, field, selector button
        self.newFolderLocation = NonEditableLine("")
        self.newFolderLocation.setCursor(Qt.PointingHandCursor)
        self.newFolderLocation.mousePressEvent = lambda _: self._openFilePicker()

        # Radio buttons
        self.radiobuttons = QButtonGroup(self)

        existingFolderLayout = QHBoxLayout()
        existingFolderLayout.addWidget(CustomLabel(
            "Change existing folder:", is_bold=False))
        existingFolderLayout.addWidget(self.existingFolderName)
        self.existingFolderRadio = ContainerRadioButton(
            existingFolderLayout, self.radiobuttons, self, update)

        newLocationLayout = QHBoxLayout()
        newLocationLayout.setAlignment(Qt.AlignVCenter)
        newLocationLayout.addWidget(CustomLabel(
            "Make a new folder in:", is_bold=False))
        newLocationLayout.addWidget(self.newFolderLocation)
        self.newLocationRadio = ContainerRadioButton(
            newLocationLayout, self.radiobuttons, self, update, is_default=True)

        container = QVBoxLayout()
        container.addWidget(self.existingFolderRadio)
        container.addWidget(self.newLocationRadio)

        self._updateUI()

        # Add main container to instruction panel
        self.addLayout(container)

    def _openFilePicker(self):
        """Opens a file picker window to select an output directory for new folders."""
        filePickerDialog = QFileDialog(self)
        filePickerDialog.setFileMode(QFileDialog.Directory)
        filePickerDialog.setAcceptMode(QFileDialog.AcceptOpen)

        if filePickerDialog.exec():
            path = filePickerDialog.selectedFiles()[0]
            self.setNewFolderLocationFilepath(path)

        self.callback()

    def _updateUI(self):
        """Updates the UI to reflect the data that was set
        """
        # Enable the existing folder filepath option if it is set
        self.existingFolderRadio.setEnabled(
            self.existingFolderFilepath is not None)
        if self.existingFolderFilepath is not None:
            print(os.path.basename(self.existingFolderFilepath))
            print(self.existingFolderFilepath)

        # Update the folder names in the fields based on the stored filepaths
        self.existingFolderName.setText(
            None if self.existingFolderFilepath is None else
            os.path.basename(self.existingFolderFilepath))
        self.newFolderLocation.setText(
            os.path.basename(self.newLocationFilepath))

    def setExistingFolderFilepath(self, filepath: Optional[str]):
        """Sets the filepath to an existing folder that the user wishes
        to have the icon set.

        Args:
            filepath (Optional[str]): Filepath, or None to remove previous filepath
        """
        self.existingFolderFilepath = filepath
        self.existingFolderRadio.setChecked(filepath is not None)
        self._updateUI()

    def setNewFolderLocationFilepath(self, filepath: str):
        """Sets the filepath to the location in which the new folder
        will be generated in.

        Args:
            filepath (str): Filepath
        """
        self.newLocationFilepath = filepath
        self.newLocationRadio.setChecked(True)
        self._updateUI()

    def getOutputInfo(self) -> tuple[bool, str]:
        """Returns a filepath and whether the filepath represents an existing folder
        or a location to generate a new folder. True corresponds to a new location.

        Raises:
            ValueError: Thrown if the checked button was not one of the two radio buttons

        Returns:
            tuple[bool, str]: (Is the filepath a new location?, Filepath)
        """
        if self.existingFolderRadio.isChecked():
            return (False, self.existingFolderFilepath)
        elif self.newLocationRadio.isChecked():
            return (True, self.newLocationFilepath)
        else:
            raise ValueError("Invalid checked button")
