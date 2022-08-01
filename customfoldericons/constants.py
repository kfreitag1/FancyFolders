from enum import Enum

class FolderStyle(Enum):
  big_sur_light = 1
  big_sur_dark = 2
  catalina = 3

  def filename(self):
    return {
      FolderStyle.big_sur_light: "big_sur_light.png",
      FolderStyle.big_sur_dark: "big_sur_dark.png",
      FolderStyle.catalina: "catalina.png"
    }[self]

  def size(self):
    return {
      FolderStyle.big_sur_light: 1024,
      FolderStyle.big_sur_dark: 1024,
      FolderStyle.catalina: 1024,
    }[self]

  def icon_box_percentages(self):
    return {
      FolderStyle.big_sur_light: (0.086, 0.29, 0.914, 0.777),
      FolderStyle.big_sur_dark: (0.086, 0.29, 0.914, 0.777),
      FolderStyle.catalina: (0.086, 0.29, 0.914, 0.777), # may need different ones
    }[self]

  def base_colour(self):
    return {
      FolderStyle.big_sur_light: (116, 208, 251),
      FolderStyle.big_sur_dark: (96, 208, 255),
      FolderStyle.catalina: (120, 210, 251),
    }[self]

  def icon_colour(self):
    return {
      FolderStyle.big_sur_light: (63, 170, 229),
      FolderStyle.big_sur_dark: (53, 160, 225),
      FolderStyle.catalina: (63, 170, 229),  # Not set properly
    }[self]

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
      SFFont.semibold: "SF-Pro-Text-semibold.otf",
      SFFont.bold: "SF-Pro-Text-Bold.otf",
      SFFont.heavy: "SF-Pro-Text-Heavy.otf",
      SFFont.black: "SF-Pro-Text-Black.otf",
    }[self]