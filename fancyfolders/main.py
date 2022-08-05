from io import BytesIO
import logging
import os
from random import randint
from PySide6.QtCore import  Qt
from PySide6.QtGui import  QDragEnterEvent, QDropEvent, QFont, QMouseEvent
from PySide6.QtWidgets import QApplication, QButtonGroup, QColorDialog, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
from PIL import Image
import Cocoa

from fancyfolders.constants import ICON_SCALE_SLIDER_MAX, MAXIMUM_ICON_SCALE_VALUE, MINIMUM_ICON_SCALE_VALUE, PREVIEW_IMAGE_SIZE, FolderStyle, IconGenerationMethod, SFFont, TintColour
from fancyfolders.image_transformations import generate_folder_icon
from fancyfolders.utilities import interpolate_int_to_float_with_midpoint
from fancyfolders.widgets import CenterFolderIcon, ColourRadioButton, HorizontalSlider, NonEditableLine, TickStyle


class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    ##############################
    # ICON GENERATION VARIABLES
    ##############################

    self.icon_generation_method = IconGenerationMethod.NONE
    self.icon_text = None
    self.icon_image = None

    self.icon_tint_colour = None  # None = none, otherwise tuple of rgb int
    self.icon_font_style = SFFont.bold
    self.icon_scale = 1

    self.folder_style = FolderStyle.big_sur_light

    self.output_folder = None
    self.output_location_directory = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")


    ##############################
    # GUI LAYOUT
    ##############################

    # Dropdown to select folder style

    self.folder_style_dropdown = QComboBox()
    self.folder_style_dropdown.addItems([style.display_name() for style in FolderStyle])
    self.folder_style_dropdown.setCurrentIndex(self.folder_style.value)
    self.folder_style_dropdown.currentIndexChanged.connect(self.select_folder_style)

    # Icon preview label

    title_label = QLabel("Folder Icon Preview")
    title_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-size: 20px; font-style: italic; font-family: Georgia, 'Times New Roman';")

    # Folder icon + drag and drop area

    self.center_image = CenterFolderIcon()
    self.center_image.dragEnterEvent = self.unified_drag_enter
    self.center_image.dropEvent = self.unified_drop

    # Folder icon colour palette

    self.colour_button_group = QButtonGroup()
    colour_pallete_layout = QHBoxLayout()

    colour_buttons = []

    colour_buttons.append(ColourRadioButton(default=True))
    for tint_colour in TintColour:
      colour_buttons.append(ColourRadioButton(colour=tint_colour.value))
    colour_buttons.append(ColourRadioButton(multicolour=True))

    for colour_button in colour_buttons:
      if not colour_button.is_multicolour:
        colour_button.clicked.connect(self.select_colour)
      self.colour_button_group.addButton(colour_button)
      colour_pallete_layout.addWidget(colour_button)

    colour_buttons[0].setChecked(True)
    colour_buttons[-1].clicked.connect(self.choose_custom_colour)

    # Icon scale label

    scale_label = QLabel("Icon scale")
    scale_label.setAlignment(Qt.AlignHCenter)
    scale_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

    # Font weight label

    font_weight_label = QLabel("Symbol thickness")
    font_weight_label.setAlignment(Qt.AlignHCenter)
    font_weight_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

    # Icon scale and font weight label container

    scale_font_weight_label_container = QHBoxLayout()
    scale_font_weight_label_container.addWidget(scale_label)
    scale_font_weight_label_container.addWidget(font_weight_label)

    # Icon scale slider

    self.scale_slider = HorizontalSlider(ICON_SCALE_SLIDER_MAX, int((ICON_SCALE_SLIDER_MAX - 1)/2) + 1, TickStyle.CENTER)
    self.scale_slider.valueChanged.connect(self.icon_scale_changed)

    # Font weight slider

    self.font_weight_slider = HorizontalSlider(len(SFFont), self.icon_font_style.value, TickStyle.EACH)
    self.font_weight_slider.valueChanged.connect(self.font_weight_changed)

    # Icon scale and font weight slider container

    scale_font_weight_layout = QHBoxLayout()
    scale_font_weight_layout.addWidget(self.scale_slider)
    scale_font_weight_layout.addWidget(self.font_weight_slider)

    # Text icon input

    self.icon_input_field = QLineEdit()
    self.icon_input_field.setMaxLength(100)
    self.icon_input_field.setPlaceholderText("Drag symbol/image above or type text")
    self.icon_input_field.setAlignment(Qt.AlignCenter)
    self.icon_input_field.setFont(QFont("SF Pro Rounded"))
    self.icon_input_field.textChanged.connect(self.icon_text_changed)
    self.icon_input_field.dragEnterEvent = self.unified_drag_enter
    self.icon_input_field.dropEvent = self.unified_drop

    # Save icon
    
    # TODO make custom class - larger and different colour

    self.generate_button = QPushButton("Save icon")
    self.generate_button.clicked.connect(self.generate_and_save_folder)

    # Text input and save icon container

    input_generate_layout = QHBoxLayout()
    input_generate_layout.addWidget(self.icon_input_field, 1)
    input_generate_layout.addSpacing(8)
    input_generate_layout.addWidget(self.generate_button)

    # Folder to change field

    self.folder_replacement_field = NonEditableLine("Drag folder above to change its icon")
    self.folder_replacement_field.dragEnterEvent = self.unified_drag_enter
    self.folder_replacement_field.dropEvent = self.unified_drop

    # New folder output label, field, selector button

    folder_output_label = QLabel("Or make new folder in:")
    self.folder_output_path = NonEditableLine("")
    self.folder_output_path.setMinimumWidth(50)
    self.folder_output_picker_button = QPushButton("...")
    self.folder_output_picker_button.clicked.connect(self.open_output_location_directory)

    # New folder output container

    folder_output_layout = QHBoxLayout()
    folder_output_layout.addWidget(folder_output_label)
    folder_output_layout.addSpacing(8)
    folder_output_layout.addWidget(self.folder_output_path)
    folder_output_layout.addSpacing(8)
    folder_output_layout.addWidget(self.folder_output_picker_button)

    #####################
    # Main layout
    #####################

    main_layout = QVBoxLayout()
    main_layout.setSpacing(0)
    main_layout.addWidget(self.folder_style_dropdown)
    main_layout.addSpacerItem(QSpacerItem(0,15))
    main_layout.addWidget(title_label)
    main_layout.addWidget(self.center_image)
    main_layout.addSpacerItem(QSpacerItem(0, 5))
    main_layout.addLayout(colour_pallete_layout)
    main_layout.addSpacerItem(QSpacerItem(0, 10))
    main_layout.addLayout(scale_font_weight_label_container)
    main_layout.addLayout(scale_font_weight_layout)
    # main_layout.addSpacerItem(QSpacerItem(0, 15))
    main_layout.addLayout(input_generate_layout)
    main_layout.addSpacerItem(QSpacerItem(0, 15))
    main_layout.addWidget(self.folder_replacement_field)
    main_layout.addLayout(folder_output_layout)
    # inputs_layout.addLayout(advanced_options)

    # Display main widget

    main_widget = QWidget()
    main_widget.setLayout(main_layout)
    self.setCentralWidget(main_widget)

    # Other initializers

    main_widget.setFocus()
    self.set_output_location_directory(self.output_location_directory)
    self.update_preview_folder_image()


  def select_colour(self):
    """Called when a new colour is selected from the colour palette. Extracts
    the colour data, updates the tint colour variable, and updates the UI.
    """
    self.icon_tint_colour = self.sender().colour
    self.update_preview_folder_image()


  def choose_custom_colour(self):
    """Opens the colour picker window when a custom colour is requested. Sets the tint
    colour to the chosen colour and updates the UI.
    """
    colour_dialog = QColorDialog()
    if colour_dialog.exec():
      colour = colour_dialog.currentColor()
      self.icon_tint_colour = (colour.red(), colour.green(), colour.blue())
      self.update_preview_folder_image()


  def select_folder_style(self, index):
    """Called when a new folder style is selected from the dropdown. Updates the
    folder style variable and updates the UI.

    Args:
        index (int): Index of the FolderStyle in the dropdown
    """
    self.folder_style = FolderStyle(index)
    self.update_preview_folder_image()


  def update_preview_folder_image(self):
    """Generates the preview image with reduced size to speed up the operation,
    and displays it in the UI.
    """
    # Default size is maximum resolution
    preview_size = None

    if self.icon_generation_method is IconGenerationMethod.TEXT:
      if len(self.icon_text) > 1:
        preview_size = PREVIEW_IMAGE_SIZE
    elif self.icon_generation_method is IconGenerationMethod.IMAGE:
      preview_size = PREVIEW_IMAGE_SIZE
      
    image = self.generate_folder_image(size=preview_size)
    self.center_image.set_image(image)


  def open_output_location_directory(self):
    """Opens a file picker window to select an output directory for new folders."""
    file_picker = QFileDialog(self)
    file_picker.setFileMode(QFileDialog.Directory)
    file_picker.setAcceptMode(QFileDialog.AcceptOpen)

    if file_picker.exec():
      path = file_picker.selectedFiles()[0]
      self.set_output_location_directory(path)


  def icon_text_changed(self, text):
    """Called when the icon text field is updated with a new string. Generates a 
    new text-based folder icon.

    Args:
        text (str): Icon text
    """
    # If the string is blank, can use the NONE generation method 
    if text.strip() == "":
      self.icon_generation_method = IconGenerationMethod.NONE
    else:
      self.icon_generation_method = IconGenerationMethod.TEXT
      self.icon_text = text

    self.update_preview_folder_image()


  def icon_scale_changed(self, value):
    """Called when the icon scale slider is updated. Adjusts the icon scale variable
    and generates a new folder preview icon.

    Args:
        value (int): Value of the icon scale slider.
    """
    # Converts the integer slider value to a floating point scalar, making
    # sure that the center of the slider is mapped to a value of 1.0 (no scale)
    self.icon_scale = interpolate_int_to_float_with_midpoint(
      value, 1, ICON_SCALE_SLIDER_MAX, MINIMUM_ICON_SCALE_VALUE, 1.0, MAXIMUM_ICON_SCALE_VALUE
    )
    self.update_preview_folder_image()


  def font_weight_changed(self, value):
    """Called when the font weight slider is updated. Adjusts the font weight variable
    and generates a new folder preview icon.

    Args:
        value (int): Value of the font weight slider.
    """
    self.icon_font_style = SFFont(value)
    self.update_preview_folder_image()


  def set_output_folder(self, path):
    """Sets the path of the folder to change the icon of and updates the UI.

    Args:
        path (str): Path of the folder.
    """
    self.output_folder = path
    self.folder_replacement_field.setText(path)


  def set_output_location_directory(self, path):
    """Sets the output location for generating new folders and updates the UI.

    Args:
        path (str): Path of the new folder output directory
    """
    self.output_location_directory = path
    self.folder_output_path.setText(os.path.basename(path))


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
      self.icon_generation_method = IconGenerationMethod.IMAGE
      self.icon_image = Image.fromqimage(data.imageData())
      self.update_preview_folder_image()
      event.accept()

    # Dragged item could be a file or directory
    elif data.hasFormat("text/uri-list"):
      url = data.urls()[0]

      if url.scheme() == "file":
        path = url.toLocalFile()

        # Dragged item is a directory (folder)
        if os.path.isdir(path):
          self.set_output_folder(path)
          event.accept()

        # Dragged item is a file, which could be an image
        elif os.path.isfile(path):
          try:
            self.icon_generation_method = IconGenerationMethod.IMAGE
            self.icon_image = Image.open(path)
            self.update_preview_folder_image()
            event.accept()
          except:
            logging.exception("Dragged item is not an image file, or could not open")

    # Dragged item includes text (SF Symbol)
    elif data.hasFormat("text/plain"):
      self.icon_generation_method = IconGenerationMethod.TEXT
      self.icon_text = data.text()
      self.update_preview_folder_image()
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

  def generate_folder_image(self, size=None):
    """Generates a folder icon using the local option variables and a specified
    size parameter. Calls the generation method in the image transformation library.

    Args:
        size (int, optional): Size to make the folder icon. If None, use the maximum size.

    Returns:
        Image: PIL Image of the folder icon
    """
    return generate_folder_icon(
      folder_style=self.folder_style,
      preview_size=size,
      generation_method=self.icon_generation_method, 
      icon_scale=self.icon_scale, 
      tint_colour=self.icon_tint_colour, 
      text=self.icon_text, 
      font_style=self.icon_font_style, 
      image=self.icon_image
    )


  def generate_and_save_folder(self):
    """Generates the folder icon using the local option variables and saves it to
    the specified folder, or a new folder if none is provided.
    """

    # Only set folder icon to specific folder once
    path = self.output_folder
    self.set_output_folder(None)

    # If there is no specific path, generate a new folder
    if path is None:
      index = 1
      while True:
        new_folder_name = "untitled folder" + ("" if index == 1 else " {}".format(index))
        path = os.path.join(self.output_location_directory, new_folder_name)

        if not os.path.exists(path): 
          os.mkdir(path)
          break
        index += 1

    # Operation takes a long time, set cursor to waiting
    # TODO find a way to make a nicer cursor
    self.setCursor(Qt.BusyCursor)

    # Set folder icon to the highest resolution image
    high_resolution_image = self.generate_folder_image()
    self.center_image.set_image(high_resolution_image)
    self.set_folder_icon(high_resolution_image, path)

    # Operation is finished, set cursor to normal
    self.unsetCursor()

    # DEV IMAGE SAVE
    # high_resolution_image.save(os.path.join(self.output_location_directory, "imageoutput-" + str(randint(1, 99999)) + ".png"))


  def set_folder_icon(self, pil_image, path):
    """Sets the icon of the file/directory at the specified path to the provided image
    using the native macOS API, interfaced through PyObjC.

    Args:
        pil_image (Image): PIL Image to set the icon to
        path (str): Absolute path to the file/directory
    """

    # Need to first save the image data to a bytes buffer in PNG format
    # for the PyObjC API method
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    
    ns_image = Cocoa.NSImage.alloc().initWithData_(buffered.getvalue())
    Cocoa.NSWorkspace.sharedWorkspace().setIcon_forFile_options_(ns_image, path, 0)


##############################
# START APPLICATION
##############################

app = QApplication()

window = MainWindow()
window.show()

app.exec()