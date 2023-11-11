from colorsys import hsv_to_rgb, rgb_to_hsv
import os
import sys
from xml.etree.ElementInclude import include

#######################
# COLOUR UTILITIES
#######################


def divided_colour(starting_colour, final_colour):
    colour_channels = zip(starting_colour, final_colour)
    return tuple([clamp(int(((255 * final) / start)), 0, 255) for start, final in colour_channels])


def rgb_int_to_hsv(rgb_colour):
    float_colours = [colour / 255 for colour in rgb_colour]
    return rgb_to_hsv(*float_colours)


def hsv_to_rgb_int(hsv_colour):
    float_colours = hsv_to_rgb(*hsv_colour)
    return tuple([int(colour * 255) for colour in float_colours])

#######################
# FILESYSTEM UTILITIES
#######################


def get_font_location(font_pathname, include_internal=False):
    """Returns the path of the font if it is installed on the system. If not,
    returns None. May or may not include internal resources

    Args:
        font_pathname (str): Name of the font with .ttf or .otf
        include_internal (bool, optional): Whether to check internal resources or not. 
          Defaults to False.

    Returns:
        str / None: Path to the font, if found.
    """
    possible_font_locations = [
        "/System/Library/Fonts/",
        "/Library/Fonts/",
        os.path.join(os.path.join(os.path.expanduser("~")), "Library/Fonts/")
    ]
    if include_internal:
        possible_font_locations.insert(
            0, internal_resource_path("assets/fonts"))

    for location in possible_font_locations:
        if font_pathname in os.listdir(location):
            return os.path.join(location, font_pathname)
    return None


def get_first_font_installed(font_list, include_internal=True):
    """Returns the first font in the specified font list that is installed on the system,
    otherwise returns None
    """
    for font in font_list:
        font_path = get_font_location(font, include_internal)
        if font_path is not None:
            return font_path
    return None


def internal_resource_path(relative_path):
    """ Get absolute path to internal app resource, works for dev and for PyInstaller """

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#######################
# MATH UTILITIES
#######################


def clamp(n, min_value, max_value):
    return min(max(n, min_value), max_value)


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
