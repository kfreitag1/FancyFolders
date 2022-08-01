import os
import sys

def resource_path(relative_path):
    """ Get absolute path to internal resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# COLOUR UTILITIES

def divided_colour(starting_colour, final_colour):
  colour_channels = zip(starting_colour, final_colour)
  return tuple([min(max(int(((255 * final) / start)), 0), 255) for start, final in colour_channels])

# FONT UTILITIES

def get_first_font_installed(font_list):
  possible_font_locations = [
    "/System/Library/Fonts/",
    "/Library/Fonts/",
    os.path.join(os.path.join(os.path.expanduser("~")), "Library/Fonts/")
  ]
  for font in font_list:
    for location in possible_font_locations:
      if font in os.listdir(location):
        return font
  return "ERROR ERROR NO FONT"

# MATH UTILITIES

def interpolate_int_to_float_with_midpoint(value: int, pre_min: int, pre_max: int, post_min: float, post_mid: float, post_max: float):
  pre_mid = int((pre_max - pre_min)/2) + 1

  if value == pre_mid:
    return post_mid
  elif value < pre_mid:
    return interpolate(value, pre_min, pre_mid, post_min, post_mid)
  elif value > pre_mid:
    return interpolate(value, pre_mid, pre_max, post_mid, post_max)


def interpolate(value, pre_min, pre_max, post_min, post_max):
  return ((post_max - post_min) * value + pre_max * post_min - pre_min * post_max) / (pre_max - pre_min)
