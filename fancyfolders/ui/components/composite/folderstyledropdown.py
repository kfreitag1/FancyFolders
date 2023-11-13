from typing import Callable

from PySide6.QtWidgets import QComboBox

from fancyfolders.constants import FolderStyle


class FolderStyleDropdown(QComboBox):
    """Represents a dropdown to select one of the folder styles
    (macOS versions)
    """

    def __init__(self, default_style: FolderStyle,
                 on_change: Callable[[], None]) -> None:
        """Constructs a new folder style dropdown

        :param default_style: Default folder style choice
        :param on_change: Callback to run whenever a selection is made
        """
        super().__init__()

        # All possible folder styles
        self.addItems([style.display_name() for style in FolderStyle])

        # Set default
        self.setCurrentIndex(default_style.value)

        # Setup callback on change
        self.currentIndexChanged.connect(lambda _: on_change())

    def get_folder_style(self) -> FolderStyle:
        return FolderStyle(self.currentIndex())
