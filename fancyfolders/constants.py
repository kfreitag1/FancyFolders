from enum import Enum

######################
# CONSTANTS
######################

# UI

PREVIEW_IMAGE_SIZE = 350

ICON_SCALE_SLIDER_MAX = 31
MAXIMUM_ICON_SCALE_VALUE = 1.5
MINIMUM_ICON_SCALE_VALUE = 0.1

# Icon Generation

FOLDER_SHADOW_INCREASE_FACTOR = 1.9
INNER_SHADOW_COLOUR_SCALING_FACTOR = 0.9

INNER_SHADOW_BLUR = 3
INNER_SHADOW_Y_OFFSET = 0.00293  # Percentage of height
OUTER_HIGHLIGHT_BLUR = 6
OUTER_HIGHLIGHT_Y_OFFSET = 0.00782  # Percentage of height

ICON_BOX_SCALING_FACTOR = 0.84

BACKUP_FONTS = ["SFNS.ttf", "System San Francisco Text Medium.ttf"]


######################
# TYPES
######################

class IconGenerationMethod(Enum):
  NONE = 0
  IMAGE = 1
  TEXT = 2

class FolderStyle(Enum):
  big_sur_light = 0
  big_sur_dark = 1
  catalina = 2

  def filename(self):
    """Filename of the icon in the assets folder"""
    return {
      FolderStyle.big_sur_light: "big_sur_light.png",
      FolderStyle.big_sur_dark: "big_sur_dark.png",
      FolderStyle.catalina: "catalina.png"
    }[self]

  def display_name(self):
    """Name to display to the user"""
    return {
      FolderStyle.big_sur_light: "Big Sur - Light",
      FolderStyle.big_sur_dark: "Big Sur - Dark",
      FolderStyle.catalina: "Catalina",
    }[self]

  def size(self):
    """Size of the folder in pixels, 
    1 dimension is specified because the image is a square
    """
    return {
      FolderStyle.big_sur_light: 1024,
      FolderStyle.big_sur_dark: 1024,
      FolderStyle.catalina: 1024,
    }[self]

  def icon_box_percentages(self):
    """Size of the rect in percentages which contains the region to draw the icon

    Returns:
        (float * 4): (x1, y1, x2, y2); Coordinate percentages
    """
    return {
      FolderStyle.big_sur_light: (0.086, 0.29, 0.914, 0.777),
      FolderStyle.big_sur_dark: (0.086, 0.29, 0.914, 0.777),
      FolderStyle.catalina: (0.0668, 0.281, 0.9332, 0.770),
    }[self]

  def preview_crop_percentages(self):
    """Minimum size of the rect in percentages which contains the 
    folder for displaying in the preview image

    Returns:
        (float * 4): (x1, y1, x2, y2); Coordinate percentages
    """
    return {
      FolderStyle.big_sur_light: (0, 0.0888, 1.0, 0.9276),
      FolderStyle.big_sur_dark: (0, 0.0888, 1.0, 0.9276),
      FolderStyle.catalina: (0, 0.0972, 1.0, 0.896),
    }[self]

  def base_colour(self):
    """The average colour of the folder where the icon is to be drawn

    Returns:
        (int * 3): (r, g, b); Colour
    """
    return {
      FolderStyle.big_sur_light: (116, 208, 251),
      FolderStyle.big_sur_dark: (96, 208, 255),
      FolderStyle.catalina: (120, 210, 251),
    }[self]

  def icon_colour(self):
    """The average colour of the icon in default macOS folders

    Returns:
        (int * 3): (r, g, b); Colour
    """
    return {
      FolderStyle.big_sur_light: (63, 170, 229),
      FolderStyle.big_sur_dark: (53, 160, 225),
      FolderStyle.catalina: (63, 170, 229),  # TODO set properly
    }[self]

class TintColour(Enum):
  """Default colour palette for folder tints"""
  red = (255, 154, 162)
  melon = (255, 183, 178)
  orange = (255, 218, 193)
  yellow = (255, 236, 209)
  green = (226, 240, 203)
  teal = (181, 234, 215)
  purple = (199, 206, 234)
  white = (250, 249, 246)
  cream = (255,250,240)

class SFFont(Enum):
  ultralight = 1
  thin = 2
  regular = 3
  medium = 4
  semibold = 5
  bold = 6
  heavy = 7
  black = 8

  def filename(self):
    return {
      SFFont.ultralight: "SF-Pro-Text-Ultralight.otf",
      SFFont.thin: "SF-Pro-Text-Thin.otf",
      SFFont.regular: "SF-Pro-Text-Regular.otf",
      SFFont.medium: "SF-Pro-Text-Medium.otf",
      SFFont.semibold: "SF-Pro-Text-Semibold.otf",
      SFFont.bold: "SF-Pro-Text-Bold.otf",
      SFFont.heavy: "SF-Pro-Text-Heavy.otf",
      SFFont.black: "SF-Pro-Text-Black.otf",
    }[self]

  # def backup_font_filename(self):