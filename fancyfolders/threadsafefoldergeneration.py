from uuid import UUID
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from PIL.Image import Image

from fancyfolders.constants import FolderStyle
from fancyfolders.imagetransformations import generate_folder_icon


class TaskExitedException(Exception):
    pass


class FolderGeneratorSignals(QObject):
    """The completion signal for a FolderGeneratorWorker"""
    completed = Signal(UUID, Image, FolderStyle)


class FolderGeneratorWorker(QRunnable):
    """An asynchronous worker object that generates a new folder icon"""

    def __init__(self, uuid: UUID, folder_style: FolderStyle, **kwargs) -> None:
        """Create a new folder generator worker with a unique ID, and the
        keyword arguments needed for the folder generation method

        :param uuid: Unique ID for this worker
        :param folder_style: FolderStyle of the folder to generate
        :param kwargs: Keyword arguments to pass to the folder generation method
        """
        super().__init__()
        self.signals = FolderGeneratorSignals()
        self.uuid = uuid
        self.folder_style = folder_style
        self.kwargs = kwargs
        self.keep_going = True

    @Slot()
    def run(self):
        """Generates the folder icon and emits the resulting image"""
        try:
            folder_image: Image = generate_folder_icon(
                folder_style=self.folder_style, keep_going=self._should_continue,
                **self.kwargs)
            self.signals.completed.emit(self.uuid, folder_image,
                                        self.folder_style)
        except TaskExitedException:
            pass
        except Exception:
            raise ValueError("Folder generation had an unexpected error")

    @Slot()
    def stop(self):
        """Stops the current folder generation task"""
        self.keep_going = False

    def _should_continue(self) -> bool:
        return self.keep_going
