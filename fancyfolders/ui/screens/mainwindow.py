from copy import deepcopy
import logging
import os
import time
from typing import Optional
from uuid import UUID
import uuid
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QMenuBar, QVBoxLayout, QWidget
from PIL.Image import Image

from fancyfolders.constants import DEFAULT_FONT, ICON_SCALE_SLIDER_MAX, FolderStyle, IconGenerationMethod, SFFont
from fancyfolders.imagetransformations import generate_folder_icon
from fancyfolders.ui.components.composite.colourpalette import ColourPalette
from fancyfolders.ui.components.composite.folderstyledropdown import FolderStyleDropdown
from fancyfolders.ui.components.composite.saveiconpanel import SaveIconPanel
from fancyfolders.ui.components.composite.scalethicknesssliders import ScaleThicknessSliders
from fancyfolders.ui.components.composite.seticontextpanel import SetIconTextPanel
from fancyfolders.ui.components.composite.setlocationpanel import SetLocationPanel

from fancyfolders.ui.screens.aboutpanel import AboutPanel

from fancyfolders.utilities import generateUniqueFolderName, set_folder_icon
from fancyfolders.ui.components.centrefoldericon import CenterFolderIcon, CenterFolderIconContainer


class FolderGeneratorWorker(QRunnable):
    """Represents an asyncronous worker object that generates a new folder icon
    """

    def __init__(self, uuid: UUID, folderStyle: FolderStyle, **kwargs) -> None:
        """Create a new folder generator worker with a unique ID, and the keyword
        arguments needed for the folder generation method.

        Args:
            uuid (UUID): Unique ID for this worker
            folderStyle (FolderStyle): FolderStyle of the folder to generate
        """
        super().__init__()
        self.signals = self.FolderGeneratorSignals()
        self.uuid = uuid
        self.folderStyle = folderStyle
        self.kwargs = kwargs

    @Slot()
    def run(self):
        """Generates the folder icon and emits the resulting image
        """
        folderImage: Image = generate_folder_icon(
            folderStyle=self.folderStyle, **self.kwargs)
        self.signals.completed.emit(self.uuid, folderImage, self.folderStyle)

    class FolderGeneratorSignals(QObject):
        """Represents the completion signal for a FolderGeneratorWorker
        """
        completed = Signal(UUID, Image, FolderStyle)


class MainWindow(QMainWindow):
    """Represents the main window of the application, containing all user input fields and
    the folder icon display.
    """

    # Need to keep track of these variables, can't dynamically grab them like the others
    generationMethod = IconGenerationMethod.NONE
    symbolText: str = ""
    iconImage: Image = None

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)

        # Dropdown to select folder style
        self.folderStyleDropdown = FolderStyleDropdown(
            FolderStyle.big_sur_light, lambda: self.update(True))
        main_layout.addWidget(self.folderStyleDropdown)

        # Folder icon + drag and drop area
        self.centreImage = CenterFolderIconContainer()
        self.centreImage.dragEnterEvent = self.unified_drag_enter
        self.centreImage.dropEvent = self.unified_drop
        main_layout.addWidget(self.centreImage)

        # Folder icon colour palette
        self.colourPalette = ColourPalette(lambda: self.update(True))
        main_layout.addLayout(self.colourPalette)

        # Icon scale and font weight slider container
        self.scaleThicknessSliders = ScaleThicknessSliders(
            lambda: self.update(True))
        main_layout.addLayout(self.scaleThicknessSliders)

        # Main controls panels
        self.setIconPanel = SetIconTextPanel(
            lambda: self.update(True, IconGenerationMethod.TEXT))
        main_layout.addWidget(self.setIconPanel)
        self.setLocationPanel = SetLocationPanel(self.update)
        main_layout.addWidget(self.setLocationPanel)
        self.saveIconPanel = SaveIconPanel()
        main_layout.addWidget(self.saveIconPanel)

        # Set up menu bar
        self._init_menu_bar()

        # Display main widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        main_widget.setFocus()

        # Initialize local storage of values and update folder icon
        self.update(True, IconGenerationMethod.NONE)

    def _init_menu_bar(self):
        """TODO
        """
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.menu = self.menu_bar.addMenu("About")

        def _open_about_panel():
            about_panel = AboutPanel()
            about_panel.exec()

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(_open_about_panel)
        self.menu.addAction(self.about_action)

    def update(self, generateFolder: bool = False,
               newGenerationMethod: Optional[IconGenerationMethod] = None):
        """Called on any update of any one of the user input fields or data sources. Generates the
        folder icon based on the new data, if selected.

        Args:
            generateFolder (bool, optional): Whether to generate the folder icon. Defaults to False.
            generationMethod (Optional[IconGenerationMethod], optional): The new icon generation 
                method to use. Defaults to None (aka, no change).
        """

        # Set the generation method if specified
        if newGenerationMethod is not None:
            self.generationMethod = newGenerationMethod

        # Get updated variables for all options
        folderStyle = self.folderStyleDropdown.getFolderStyle()
        tintColour = self.colourPalette.getColour()
        iconScale = self.scaleThicknessSliders.getScale()
        iconThickness = self.scaleThicknessSliders.getThickness()
        iconText = self.setIconPanel.getIconText()
        # makeNewFolder, outputFilepath = self.setLocationPanel.getOutputInfo() TODO

        # Check that there is text if in TEXT or SYMBOL mode, otherwise set to NONE mode
        if (self.generationMethod is IconGenerationMethod.TEXT and not iconText) or (
                self.generationMethod is IconGenerationMethod.SYMBOL and not self.symbolText):
            self.generationMethod = IconGenerationMethod.NONE

        # Set text to be either the dragged symbol text or the typed text
        text = self.symbolText if self.generationMethod is IconGenerationMethod.SYMBOL else iconText

        # Asynchronously generate new folder icon
        if generateFolder:
            # Keep track of unique ID for this task to only display latest one
            folderGenerationTaskUUID = uuid.uuid4()

            # Create new worker task to generate folder icon
            # Ensure all parameters are immutable for thread safety
            worker = FolderGeneratorWorker(
                folderGenerationTaskUUID, folderStyle=folderStyle,
                generationMethod=self.generationMethod, previewSize=None, iconScale=iconScale,
                tintColour=tintColour, text=text, fontStyle=iconThickness,
                image=deepcopy(self.iconImage))

            # Connect completion callback to the centreImage object, and set it to
            # receive the result of this task using its unique ID
            worker.signals.completed.connect(self.centreImage.receiveImageData)
            self.centreImage.setReadyToReceive(folderGenerationTaskUUID)

            QThreadPool.globalInstance().start(worker)

    # def clear_icon(self):
    #     """Clears the current icon"""
    #     self.icon_generation_method = IconGenerationMethod.NONE
    #     self.icon_image = None
    #     self.icon_text = None
    #     self.icon_scale = 1
    #     self.icon_font_style = DEFAULT_FONT

    #     self.icon_input_field.setText("")
    #     self.scale_slider.setValue(int((ICON_SCALE_SLIDER_MAX - 1)/2) + 1)
    #     self.font_weight_slider.setValue(self.icon_font_style.value)

    #     self.update_preview_folder_image()

    # EVENT HANDLERS

    def unified_drag_enter(self, event: QDragEnterEvent):
        """Accepts all items dragged onto the main window"""
        event.acceptProposedAction()

    def unified_drop(self, event: QDropEvent):
        """Called when a text/symbol/image/folder is dropped onto one of the components
        in the main window. If the dropped item is a folder, set the output folder location. If
        it is a text/symbol/image/image-file, generate a folder icon and update the UI.

        Args:
            event (QDropEvent): Drop event
        """

        data = event.mimeData()

        # Dragged data is an image
        if data.hasFormat("application/x-qt-image"):
            self.iconImage = Image.fromqimage(data.imageData())
            self.update(True, IconGenerationMethod.IMAGE)
            # self.update_preview_folder_image()
            event.accept()

        # Dragged item could be a file or directory
        elif data.hasFormat("text/uri-list"):
            url = data.urls()[0]

            if url.scheme() == "file":
                path = url.toLocalFile()

                # Dragged item is a directory (folder)
                if os.path.isdir(path):
                    self.setLocationPanel.setExistingFolderFilepath(
                        os.path.dirname(path))
                    # self.set_output_folder(path)
                    event.accept()

                # Dragged item is a file, which could be an image
                elif os.path.isfile(path):
                    try:
                        self.iconImage = Image.open(path)
                        self.update(True, IconGenerationMethod.IMAGE)
                        # self.update_preview_folder_image()
                        event.accept()
                    except:
                        logging.exception(
                            "Dragged item is not an image file, or could not open")

        # Dragged item includes text (SF Symbol)
        elif data.hasFormat("text/plain"):
            self.symbolText = data.text()
            self.update(True, IconGenerationMethod.SYMBOL)
            # self.update_preview_folder_image()
            event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Clears the focus on any focussed input field when clicking anywhere on the window.

        Args:
            event (QMouseEvent): Mouse click event to pass through
        """

        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.clearFocus()

        # Let mouce click event bubble through
        super().mousePressEvent(event)

    ##############################
    # FOLDER GENERATION METHODS
    ##############################

    # def generate_and_save_folder(self):
    #     """Generates the folder icon using the local option variables and saves it to
    #     the specified folder, or a new folder if none is provided.
    #     """
    #     # TODO check if image has already been created for the UI, just use this, if not then can
    #     # generate the folder icon, or wait for it to be completed on the other thread

    #     # Only set folder icon to specific folder once
    #     path = self.output_folder
    #     self.set_output_folder(None)

    #     # If there is no specific path, generate a new folder
    #     if path is None:
    #         path = generateUniqueFolderName(self.output_location_directory)

    #     # Operation takes a long time, set cursor to waiting
    #     # TODO find a way to make a nicer cursor
    #     self.setCursor(Qt.BusyCursor)

    #     # Set folder icon to the highest resolution image
    #     high_resolution_image = self.generate_folder_image()
    #     self.centreImage.set_image(high_resolution_image)
    #     set_folder_icon(high_resolution_image, path)

    #     # Operation is finished, set cursor to normal
    #     self.unsetCursor()

    #     # DEV IMAGE SAVE
    #     # high_resolution_image.save(os.path.join(self.output_location_directory, "imageoutput-" + str(randint(1, 99999)) + ".png"))
