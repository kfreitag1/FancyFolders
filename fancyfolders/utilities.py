from colorsys import hsv_to_rgb, rgb_to_hsv
from io import BytesIO
import os
import sys
import Cocoa

#######################
# COLOUR UTILITIES
#######################


def dividedColour(starting_colour, final_colour):
    colour_channels = zip(starting_colour, final_colour)
    return tuple([clamp(int(((255 * final) / start)), 0, 255) for start, final in colour_channels])


def rgbIntToHsv(rgb_colour):
    float_colours = [colour / 255 for colour in rgb_colour]
    return rgb_to_hsv(*float_colours)


def hsvToRgbInt(hsv_colour):
    float_colours = hsv_to_rgb(*hsv_colour)
    return tuple([int(colour * 255) for colour in float_colours])

#######################
# FILESYSTEM UTILITIES
#######################


def getFontLocation(font_pathname, includeInternal=False):
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
    if includeInternal:
        possible_font_locations.insert(
            0, internal_resource_path("assets/fonts"))

    for location in possible_font_locations:
        if font_pathname in os.listdir(location):
            return os.path.join(location, font_pathname)
    return None


def get_first_font_installed(font_list, includeinternal=True):
    """Returns the first font in the specified font list that is installed on the system,
    otherwise returns None
    """
    for font in font_list:
        font_path = getFontLocation(font, includeinternal)
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


def set_folder_icon(pil_image, path):
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


def generateUniqueFolderName(directory: str):
    index = 1
    while True:
        new_folder_name = "untitled folder" + \
            ("" if index == 1 else " {}".format(index))
        path = os.path.join(directory, new_folder_name)

        if not os.path.exists(path):
            os.mkdir(path)
            break
        index += 1

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
