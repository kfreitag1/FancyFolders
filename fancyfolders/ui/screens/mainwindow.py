import logging
import os
import uuid
from copy import deepcopy
from typing import Optional

from PIL.Image import Image
from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtGui import QAction, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QMenuBar, QVBoxLayout, QWidget

from fancyfolders.constants import FolderStyle, IconGenerationMethod
from fancyfolders.threadsafefoldergeneration import FolderGeneratorWorker
from fancyfolders.ui.components.centrefoldericon import CentreFolderIconContainer
from fancyfolders.ui.components.composite.colourpalette import ColourPalette
from fancyfolders.ui.components.composite.folderstyledropdown import FolderStyleDropdown
from fancyfolders.ui.components.composite.saveiconpanel import SaveIconPanel
from fancyfolders.ui.components.composite.scalethicknesssliders import ScaleThicknessSliders
from fancyfolders.ui.components.composite.seticontextpanel import SetIconTextPanel
from fancyfolders.ui.components.composite.setlocationpanel import SetLocationPanel
from fancyfolders.ui.screens.aboutpanel import AboutPanel


class MainWindow(QMainWindow):
    """Represents the main window of the application, containing all user
    input fields and the folder icon display.
    """

    # Need to keep track of these folder icon generation variables,
    # can't dynamically grab them like the others
    generation_method = IconGenerationMethod.NONE
    symbol_text: str = ""
    icon_image: Image = None

    stop_all_previous_workers_signal = Signal()

    def __init__(self) -> None:
        super().__init__()

        # Common thread pool to run folder generation in
        self.thread_pool = QThreadPool(self)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)

        # Dropdown to select folder style
        self.folder_style_dropdown = FolderStyleDropdown(
            FolderStyle.big_sur_light, lambda: self.update_folder_generation_variables(True))
        main_layout.addWidget(self.folder_style_dropdown)

        # Folder icon + drag and drop area
        self.centre_image = CentreFolderIconContainer()
        self.centre_image.dragEnterEvent = lambda e: e.acceptProposedAction()
        self.centre_image.dropEvent = self.unified_drop
        main_layout.addWidget(self.centre_image)

        # Folder icon colour palette
        self.colour_palette = ColourPalette(lambda: self.update_folder_generation_variables(True))
        main_layout.addLayout(self.colour_palette)

        # Icon scale and font weight slider container
        self.scale_thickness_sliders = ScaleThicknessSliders(
            lambda: self.update_folder_generation_variables(True))
        main_layout.addLayout(self.scale_thickness_sliders)

        # Main controls panels
        self.set_icon_panel = SetIconTextPanel(
            lambda: self.update_folder_generation_variables(True, IconGenerationMethod.TEXT))
        main_layout.addWidget(self.set_icon_panel)
        self.set_location_panel = SetLocationPanel(self.update_folder_generation_variables)
        main_layout.addWidget(self.set_location_panel)
        self.save_icon_panel = SaveIconPanel()
        main_layout.addWidget(self.save_icon_panel)

        # Set up menu bar
        self._init_menu_bar()

        # Display main widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        main_widget.setFocus()

        # Initialize local storage of values and update folder icon
        self.update_folder_generation_variables(True, IconGenerationMethod.NONE)

    def _init_menu_bar(self) -> None:
        """Initializes the menu bar for the application. Contains one button
        to access the 'about panel'
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

    def update_folder_generation_variables(
            self, generate_folder: bool = False,
            new_generation_method: Optional[IconGenerationMethod] = None) -> None:
        """Called on any update of any one of the user input fields or data
        sources. Generates the folder icon based on the new data, if selected

        :param generate_folder: Whether to generate the folder icon
        :param new_generation_method: The new icon generation method to use.
            Defaults to None (a.k.a. no change)
        """
        # Set the generation method if specified
        if new_generation_method is not None:
            self.generation_method = new_generation_method

        # Get updated variables for all options
        folder_style = self.folder_style_dropdown.get_folder_style()
        tint_colour = self.colour_palette.get_colour()
        icon_scale = self.scale_thickness_sliders.get_scale()
        icon_thickness = self.scale_thickness_sliders.get_thickness()
        icon_text = self.set_icon_panel.get_icon_text()
        # makeNewFolder, outputFilepath = self.setLocationPanel.getOutputInfo() TODO

        # Check that there is text if in TEXT or SYMBOL mode, otherwise set to NONE mode
        if (self.generation_method is IconGenerationMethod.TEXT and not icon_text) or (
                self.generation_method is IconGenerationMethod.SYMBOL and not self.symbol_text):
            self.generation_method = IconGenerationMethod.NONE

        # Set text to be either the dragged symbol text or the typed text
        text = self.symbol_text if self.generation_method is IconGenerationMethod.SYMBOL else icon_text

        # Asynchronously generate new folder icon
        if generate_folder:
            # Keep track of unique ID for this task to only display latest one
            folder_generation_task_uuid = uuid.uuid4()

            # Create new worker task to generate folder icon
            # Ensure all parameters are immutable for thread safety
            worker = FolderGeneratorWorker(
                folder_generation_task_uuid, folder_style=folder_style,
                generation_method=self.generation_method, icon_scale=icon_scale,
                tint_colour=tint_colour, text=text, font_style=icon_thickness,
                image=deepcopy(self.icon_image))

            # Connect completion callback to the centreImage object, and set it to
            # receive the result of this task using its unique ID
            worker.signals.completed.connect(self.centre_image.receive_image_data)
            self.centre_image.set_ready_to_receive(folder_generation_task_uuid)

            # Stop all other folder generation tasks and make this one stop too in the future
            self.stop_all_previous_workers_signal.emit()
            self.stop_all_previous_workers_signal.connect(worker.stop)

            # Start task
            self.thread_pool.start(worker)

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

    def unified_drop(self, event: QDropEvent) -> None:
        """Called when a text/symbol/image/folder is dropped onto one of the
        components in the main window. If the dropped item is a folder, set
        the output folder location. If it is a text/symbol/image/image-file,
        generate a folder icon and update the UI

        :param event: Drop event
        """

        data = event.mimeData()

        # Dragged data is an image
        if data.hasFormat("application/x-qt-image"):
            self.icon_image = Image.fromqimage(data.imageData())
            self.update_folder_generation_variables(
                True, IconGenerationMethod.IMAGE)
            event.accept()

        # Dragged item could be a file or directory
        elif data.hasFormat("text/uri-list"):
            url = data.urls()[0]

            if url.scheme() == "file":
                path = url.toLocalFile()

                # Dragged item is a directory (folder)
                if os.path.isdir(path):
                    self.set_location_panel.set_existing_folder_filepath(
                        os.path.dirname(path))
                    event.accept()

                # Dragged item is a file, which could be an image
                elif os.path.isfile(path):
                    try:
                        self.icon_image = Image.open(path)
                        self.update_folder_generation_variables(
                            True, IconGenerationMethod.IMAGE)
                        event.accept()
                    except Exception:
                        logging.exception(
                            "Dragged item is not an image file, or could not open")

        # Dragged item includes text (SF Symbol)
        elif data.hasFormat("text/plain"):
            self.symbol_text = data.text()
            self.update_folder_generation_variables(True, IconGenerationMethod.SYMBOL)
            event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Clears the focus on any focussed input field when clicking anywhere
        on the window

        :param event: Mouse click event to pass through
        """
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.clearFocus()

        # Let mouse click event bubble through
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
