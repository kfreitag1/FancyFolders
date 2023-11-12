from typing import Callable, Optional
from PySide6.QtWidgets import QComboBox, QWidget

from fancyfolders.constants import FolderStyle


class FolderStyleDropdown(QComboBox):
    """Represents a dropdown to select one of the folder styles (macOS versions)
    """

    def __init__(self, defaultStyle: FolderStyle, onChange: Callable[[], None]) -> None:
        super().__init__()

        # All possible folder styles
        self.addItems([style.display_name() for style in FolderStyle])

        # Set default
        self.setCurrentIndex(defaultStyle.value)

        # Setup callback on change
        self.currentIndexChanged.connect(lambda _: onChange())

    def getFolderStyle(self) -> FolderStyle:
        return FolderStyle(self.currentIndex())
