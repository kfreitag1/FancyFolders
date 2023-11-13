from uuid import UUID
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from PIL.Image import Image

from fancyfolders.constants import FolderStyle
from fancyfolders.imagetransformations import generate_folder_icon


class TaskExitedException(Exception):
    pass


class FolderGeneratorSignals(QObject):
    """Represents the completion signal for a FolderGeneratorWorker
    """
    completed = Signal(UUID, Image, FolderStyle)


class FolderGeneratorWorker(QRunnable):
    """Represents an asynchronous worker object that generates a new folder icon
    """

    def __init__(self, uuid: UUID, folder_style: FolderStyle, **kwargs) -> None:
        """Create a new folder generator worker with a unique ID, and the
        keyword arguments needed for the folder generation method.

        Args:
            uuid (UUID): Unique ID for this worker
            folder_style (FolderStyle): FolderStyle of the folder to generate
        """
        super().__init__()
        self.signals = FolderGeneratorSignals()
        self.uuid = uuid
        self.folderStyle = folder_style
        self.kwargs = kwargs
        self.keepGoing = True

    @Slot()
    def run(self):
        """Generates the folder icon and emits the resulting image
        """
        try:
            folder_image: Image = generate_folder_icon(
                folderStyle=self.folderStyle, keepGoing=self._getKeepGoing,
                **self.kwargs)
            self.signals.completed.emit(self.uuid, folder_image,
                                        self.folderStyle)
        except TaskExitedException:
            # print("NOT RETURNING... " + str(self.uuid))
            pass
        except Exception:
            raise ValueError("Folder generation had an unexpected error")

    @Slot()
    def stop(self):
        """Sets the task to be stopped whenever the folder generation method
        checks.
        """
        self.keepGoing = False
        # print("I AM STOPPING!! " + str(self.uuid))

    def _getKeepGoing(self) -> bool:
        return self.keepGoing
