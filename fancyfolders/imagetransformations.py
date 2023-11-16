import math
from colorsys import hsv_to_rgb, rgb_to_hsv
from typing import Callable, cast

from PIL import ImageFont, ImageDraw, ImageFilter, ImageChops, Image

from fancyfolders.constants import (
    BACKUP_FONTS, ICON_BOX_SCALING_FACTOR, FOLDER_SHADOW_INCREASE_FACTOR,
    INNER_SHADOW_BLUR, INNER_SHADOW_COLOUR_SCALING_FACTOR, INNER_SHADOW_Y_OFFSET,
    OUTER_HIGHLIGHT_BLUR, OUTER_HIGHLIGHT_Y_OFFSET, FolderStyle, IconGenerationMethod, SFFont)
from fancyfolders.utilities import (
    clamp, divided_colour, get_font_location, get_first_font_installed,
    hsv_to_rgb_int, internal_resource_path, rgb_int_to_hsv)


def generate_folder_icon(folder_style: FolderStyle = FolderStyle.big_sur_light,
                         generation_method: IconGenerationMethod = IconGenerationMethod.NONE,
                         icon_scale=1.0, tint_colour: tuple[int, int, int] = None,
                         text: str = None, font_style=SFFont.heavy, image: Image.Image = None,
                         keep_going: Callable[[], bool] = lambda: True) -> Image.Image:
    """Generates a folder icon image based on the given parameters.

    Returns a PIL Image file representing the folder icon. This function takes
    a long time to complete. A callback function may be passed which checks
    whether the execution should continue, will throw a TaskExitedException
    if this callback function returns false.


    :param folder_style: The macOS folder style
    :param generation_method: Whether to generate the folder without any icon,
        with a text based icon, with a symbol icon, or with an image
    :param icon_scale:
    :param tint_colour:
    :param text: Text or symbol to use as the icon
    :param font_style:
    :param image: Dragged image to use as the icon
    :param keep_going:
    :return: The PIL Image
    :raises TaskExitedException: The worker is requesting to cancel this method.
    """

    from fancyfolders.threadsafefoldergeneration import TaskExitedException

    def exit_check() -> None:
        """Exits the folder generation if requested externally"""
        if not keep_going():
            raise TaskExitedException

    # -------------------------------------------------------------------------
    # Get base folder image and its size
    folder_image = Image.open(internal_resource_path(
        "assets/" + folder_style.filename()))
    size = folder_style.size()
    exit_check()

    # -------------------------------------------------------------------------
    # Darken shadow to match default macOS folders
    folder_image = _increased_shadow(
        folder_image, factor=FOLDER_SHADOW_INCREASE_FACTOR)
    exit_check()

    # -------------------------------------------------------------------------
    # Generate mask image based on icon generation method
    mask_image = None
    if generation_method is IconGenerationMethod.NONE:
        if tint_colour is None:
            return folder_image
        return adjusted_colours(folder_image, folder_style.base_colour(), tint_colour)
    elif generation_method is IconGenerationMethod.IMAGE:
        mask_image = _generate_mask_from_image(image)
    elif generation_method is IconGenerationMethod.TEXT:
        mask_image = _generate_mask_from_text(text, size, font_style)
    exit_check()

    # -------------------------------------------------------------------------
    # Bounding box to place icon
    bounding_box_percentages = (0.086, 0.29, 0.914, 0.777)
    bounding_box = cast(
        tuple[int, int, int, int],
        tuple(int(size * percent) for percent in bounding_box_percentages))
    new_bounding_box = scaled_box(
        bounding_box, icon_scale * ICON_BOX_SCALING_FACTOR, (size, size))
    exit_check()

    # -------------------------------------------------------------------------
    # Fit the icon mask within the bounding box
    formatted_mask = Image.new("L", (size, size), "black")
    scaled_image, paste_box = _resize_image_in_box(
        mask_image, new_bounding_box)
    formatted_mask.paste(scaled_image, paste_box, scaled_image)
    exit_check()

    # -------------------------------------------------------------------------
    # Generate the center colour to be a desired colour after the multiply filter
    center_colour = divided_colour(
        folder_style.base_colour(), folder_style.icon_colour())
    exit_check()

    # -------------------------------------------------------------------------
    # Calculate shadow colour to be slightly darker than the center colour
    center_hue, center_sat, center_val = rgb_int_to_hsv(center_colour)
    shadow_hsv_colour = (center_hue, center_sat, center_val *
                         INNER_SHADOW_COLOUR_SCALING_FACTOR)
    shadow_colour = hsv_to_rgb_int(shadow_hsv_colour)
    exit_check()

    # -------------------------------------------------------------------------
    # Create shadow insert image
    shadow_image = Image.composite(
        Image.new("RGB", formatted_mask.size, center_colour),
        Image.new("RGB", formatted_mask.size, shadow_colour),
        formatted_mask)
    exit_check()

    shadow_image = shadow_image.filter(
        ImageFilter.GaussianBlur(INNER_SHADOW_BLUR))

    exit_check()
    shadow_image = ImageChops.offset(
        shadow_image, 0, math.floor(size * INNER_SHADOW_Y_OFFSET))

    exit_check()
    shadow_image.putalpha(formatted_mask)
    shadow_insert = ImageChops.multiply(folder_image, shadow_image)

    exit_check()

    # -------------------------------------------------------------------------
    # Create highlight insert image
    highlight_image = Image.composite(
        Image.new("RGBA", formatted_mask.size, "#131313"),
        Image.new("RGBA", formatted_mask.size, "black"),
        formatted_mask)
    exit_check()

    highlight_image = highlight_image.filter(
        ImageFilter.GaussianBlur(OUTER_HIGHLIGHT_BLUR))
    exit_check()

    highlight_image = ImageChops.offset(
        highlight_image, 0, math.floor(size * OUTER_HIGHLIGHT_Y_OFFSET))
    exit_check()

    highlight_image.putalpha(0)
    highlight_insert = ImageChops.add(folder_image, highlight_image)
    exit_check()

    # -------------------------------------------------------------------------
    # Combine the two
    result = Image.alpha_composite(highlight_insert, shadow_insert)
    exit_check()

    # -------------------------------------------------------------------------
    # Apply tint colour if specified, return result
    if tint_colour is None:
        return result
    return adjusted_colours(result, folder_style.base_colour(), tint_colour)


def _generate_mask_from_text(text, image_size, font_style=SFFont.heavy):
    """Generates an image mask from the specified text and font parameters.

    :param text: Text to display
    :param image_size: Size of the image in pixels
    :param font_style: Font weight to use
    :return: PIL Image (L) mask, white subject on black background
    """

    # TODO: maybe add advanced features:
    #  add multiline support
    #  add text aligning
    #  add letter size independent mode (lowercase letters not same height as uppercase)

    # Get the font path, locally first then check system
    font_filepath = get_first_font_installed(
        [font_style.filename()] + BACKUP_FONTS, include_internal=True)

    font = ImageFont.truetype(font_filepath, int(image_size / 2))

    text_draw_options = {
        "text": text,
        "anchor": "mm",
        "align": "center",
        "spacing": int(image_size / 8),
        "font": font
    }

    # Determine the exact size of the temporary image necessary to draw the complete
    # text with the specified options, avoids an unnecessarily large buffer image
    temp_draw = ImageDraw.Draw(Image.new("L", (0, 0)))
    text_bbox = temp_draw.textbbox((0, 0), **text_draw_options)
    text_size = (text_bbox[2] + abs(text_bbox[0]),
                 text_bbox[3] + abs(text_bbox[1]))
    text_center = (abs(text_bbox[0]), abs(text_bbox[1]))

    text_image = Image.new("L", text_size)
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text(text_center, **text_draw_options, fill="white")

    return text_image


def _generate_mask_from_image(image: Image.Image) -> Image.Image:
    """Generates an image mask from the specified PIL image.

    :param image: PIL image (RGB / RGBA) to display
    :return: PIL Image (L) mask, white subject on black background
    """
    white_background = Image.new("L", image.size, "white")
    mask = image if image.mode in ["RGBA", "RGBa"] else None
    white_background.paste(image, mask)
    white_background = _normalized_image(white_background)

    return ImageChops.invert(white_background)


def adjusted_colours(image: Image.Image, base_colour: tuple[float, float, float],
                     tint_colour: tuple[float, float, float]) -> Image.Image:
    """Changes the colours across the specified image by an amount that would
    shift the 'base colour' to the 'tint colour.'

    :param image: PIL Image (RGB/RGBA)
    :param base_colour: Starting base colour
    :param tint_colour: Final tint colour
    :return: PIL Image (RGB/RGBA)
    """
    start_hue, start_sat, start_val = rgb_int_to_hsv(base_colour)
    final_hue, final_sat, final_val = rgb_int_to_hsv(tint_colour)

    hue_offset = final_hue - start_hue
    sat_factor = final_sat / start_sat
    val_factor = final_val / start_val

    # sat_offset = final_sat - start_sat
    # val_offset = final_val - start_val

    def adjust_pixel_colour(r, g, b):
        h, s, v = rgb_to_hsv(r, g, b)

        h = (h + hue_offset) % 1.0
        s = clamp(s * sat_factor, 0.0, 1.0)
        v = clamp(v * val_factor, 0.0, 1.0)
        # s = clamp(s + sat_offset, 0.0, 1.0)
        # v = clamp(v + val_offset, 0.0, 1.0)

        return hsv_to_rgb(h, s, v)

    return image.filter(ImageFilter.Color3DLUT.generate(4, adjust_pixel_colour, 3))


def _increased_shadow(folder_image, factor) -> Image.Image:
    """Returns a new image with a more intense shadow by increasing the
    opacity of pixels with transparency.

    :param folder_image: Image to increase shadow on
    :param factor: Scalar value to increase opacity by
    :return: New image
    """
    r, g, b, a = folder_image.split()
    a = a.point(lambda x: min(int(x * factor), 255))

    return Image.merge("RGBA", (r, g, b, a))


def _normalized_image(image: Image.Image, steepness=0.18) -> Image.Image:
    """Produces a normalised PIL image mask.

    Normalises the pixel data from the grayscale image to 0 - 255 and applies a sigmoid function
    to bring values closer to the extremes (0 or 255).

    :param image: PIL Image (L)
    :param steepness: Intensity of sigmoid curve, smaller values lead to
        less separated colours
    :return: PIL Image (L) that has been normalised
    """
    min_value, max_value = image.getextrema()

    def sigmoid_normalize(value):
        normalized_value = int((value - min_value) * 255 / (max_value - min_value))
        return 255 / (1 + math.exp(-steepness * (normalized_value - 127)))

    try:
        return Image.eval(image, sigmoid_normalize)
    except ZeroDivisionError:
        # Image was completely flat, already "normalized"
        return image


def _resize_image_in_box(image: Image.Image, box: tuple[int, int, int, int]) \
        -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Returns the image, scaled into the bounding box with the same aspect
    ratio, from the center

    :param image: PIL Image
    :param box: Bounding box to insert image into: x1, y1, x2, y2
    :return: Scaled PIL image, New bounding box to insert into
    """
    top_point, bottom_point = box[0:2], box[2:4]
    box_size = (bottom_point[0] - top_point[0], bottom_point[1] - top_point[1])

    downscale_ratio = min(box_size[0] / image.size[0], box_size[1] / image.size[1])
    scaled_image = image.resize((int(image.width * downscale_ratio),
                                 int(image.height * downscale_ratio)))

    starting_x = top_point[0] + int((box_size[0] - scaled_image.size[0]) / 2)
    starting_y = top_point[1] + int((box_size[1] - scaled_image.size[1]) / 2)

    new_bounding_box = (starting_x, starting_y,
                        starting_x + scaled_image.size[0],
                        starting_y + scaled_image.size[1])

    return scaled_image, new_bounding_box


def scaled_box(box: tuple[int, int, int, int], scale: float,
               max_size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Returns the box scaled from the center by a constant amount along the
    diagonal, clipped into the region from (0,0) to max_size

    :param box: Box to scale: x1, y1, x2, y2
    :param scale: Constant scalar
    :param max_size: Maximum size to clip scaled box to: width, height
    :return: Scaled box
    """
    top_point, bottom_point = box[0:2], box[2:4]
    center = (int((bottom_point[0] + top_point[0]) / 2),
              int((bottom_point[1] + top_point[1]) / 2))

    # Scaled offsets from the center point (along the diagonals)
    top_offset = (int((top_point[0] - center[0]) * scale),
                  int((top_point[1] - center[1]) * scale))
    bottom_offset = (int((bottom_point[0] - center[0]) * scale),
                     int((bottom_point[1] - center[1]) * scale))

    # Re-add offsets to the center point to get absolute position
    new_top_point = (max(0, center[0] + top_offset[0]),
                     max(0, center[1] + top_offset[1]))
    new_bottom_point = (min(max_size[0], center[0] + bottom_offset[0]),
                        min(max_size[1], center[1] + bottom_offset[1]))

    return new_top_point + new_bottom_point
