from colorsys import hsv_to_rgb, rgb_to_hsv
from io import BytesIO
import os
import sys
from typing import cast

import Cocoa
from PIL.Image import Image


#######################
# COLOUR UTILITIES
#######################


def divided_colour(starting_colour: tuple[int, int, int],
                   final_colour: tuple[int, int, int]) -> tuple[int, int, int]:
    """Divides colours? TODO figure out what this is again

    :param starting_colour: Starting colour (r, g, b)
    :param final_colour: Final colour (r, g, b)
    :return: Divided colour (r, g, b)
    """
    colour_channels = zip(starting_colour, final_colour)
    return cast(tuple[int, int, int],
                tuple([clamp(int(((255 * final) / start)), 0, 255)
                       for start, final in colour_channels]))


def rgb_int_to_hsv(rgb_colour: tuple[int, int, int]) -> tuple[float, float, float]:
    """Converts an int based rgb colour to a float hsv

    :param rgb_colour: Colour to convert (r, g, b)
    :return: Converted colour (h, s, v)
    """
    float_colours = [colour / 255 for colour in rgb_colour]
    return rgb_to_hsv(*float_colours)


def hsv_to_rgb_int(hsv_colour: tuple[float, float, float]) -> tuple[int, int, int]:
    """Converts a float based hsv colour to an int rgb

    :param hsv_colour: Colour to convert (h, s, v)
    :return: Converted colour (r, g, b)
    """
    float_colours = hsv_to_rgb(*hsv_colour)
    return cast(tuple[int, int, int],
                tuple([int(colour * 255) for colour in float_colours]))


#######################
# FILESYSTEM UTILITIES
#######################

def get_internal_font_location(font_filename: str) -> str:
    base_pathname = internal_resource_path("assets/fonts")
    return os.path.join(base_pathname, font_filename)


def internal_resource_path(relative_path: str) -> str:
    """Get absolute path to internal app resource, works for dev and for
    the app created through PyInstaller

    :param relative_path: Relative filepath to resource
    :return: Absolute filepath to resource
    """

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = str(os.path.abspath("./.."))

    return os.path.join(base_path, relative_path)


def set_folder_icon(pil_image: Image, path: str) -> None:
    """Sets the icon of the file/directory at the specified path to the
    provided image using the native macOS API, interfaced through PyObjC

    :param pil_image: PIL Image of the folder icon to set
    :param path: Absolute path to the folder
    """
    # Need to first save the image data to a bytes buffer in PNG format
    # for the PyObjC API method
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")

    ns_image = Cocoa.NSImage.alloc().initWithData_(buffered.getvalue())
    Cocoa.NSWorkspace.sharedWorkspace().setIcon_forFile_options_(ns_image, path, 0)


def generate_unique_folder_filename(directory: str) -> str:
    """Generates a unique folder name in the 'untitled folder' format, in the
    specified directory. I.e. if the folder already exists, increment the number
    and try again

    :param directory: Directory to search for folders in
    :return: Unique folder name
    """
    index = 1
    while True:
        new_folder_name = "untitled folder" + \
            ("" if index == 1 else " {}".format(index))
        path = os.path.join(directory, new_folder_name)

        if not os.path.exists(path):
            os.mkdir(path)
            break
        index += 1
    return path

#######################
# MATH UTILITIES
#######################


def clamp(n, min_value, max_value):
    return min(max(n, min_value), max_value)


def interpolate_int_to_float_with_midpoint(
        value: int, pre_min: int, pre_max: int, post_min: float,
        post_mid: float, post_max: float) -> float:

    pre_mid = int((pre_max - pre_min)/2) + 1

    if value == pre_mid:
        return post_mid
    elif value < pre_mid:
        return interpolate(value, pre_min, pre_mid, post_min, post_mid)
    elif value > pre_mid:
        return interpolate(value, pre_mid, pre_max, post_mid, post_max)


def interpolate(value, pre_min, pre_max, post_min, post_max):
    return ((post_max - post_min) * value + pre_max * post_min - pre_min * post_max) / (pre_max - pre_min)
