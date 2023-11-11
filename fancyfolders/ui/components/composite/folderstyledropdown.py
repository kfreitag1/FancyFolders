from typing import Callable, Optional
from PySide6.QtWidgets import QComboBox, QWidget

from fancyfolders.constants import FolderStyle


class FolderStyleDropdown(QComboBox):
    def __init__(self, default_style: FolderStyle, on_change: Callable[[int], None]) -> None:
        super().__init__()

        # All possible folder styles
        self.addItems([style.display_name() for style in FolderStyle])

        # Set default
        self.setCurrentIndex(default_style.value)

        # Setup callback on new selection
        self.currentIndexChanged.connect(on_change)

    def getFolderStyle(self) -> FolderStyle:
        return self.currentIndex()
