from colorsys import hsv_to_rgb, rgb_to_hsv
import math
from PIL import ImageFont, Image, ImageDraw, ImageFilter, ImageChops
from fancyfolders.constants import BACKUP_FONTS, ICON_BOX_SCALING_FACTOR, FOLDER_SHADOW_INCREASE_FACTOR, INNER_SHADOW_BLUR, INNER_SHADOW_COLOUR_SCALING_FACTOR, INNER_SHADOW_Y_OFFSET, OUTER_HIGHLIGHT_BLUR, OUTER_HIGHLIGHT_Y_OFFSET, FolderStyle, IconGenerationMethod, SFFont

from fancyfolders.utilities import clamp, dividedColour, getFontLocation, get_first_font_installed, hsvToRgbInt, internal_resource_path, rgbIntToHsv


def generate_folder_icon(folderStyle: FolderStyle = FolderStyle.big_sur_light,
                         generationMethod: IconGenerationMethod = IconGenerationMethod.NONE,
                         previewSize=None, iconScale=1.0, tintColour=None, text=None,
                         fontStyle=SFFont.heavy, image=None):
    """Generates a folder icon PIL image based on the specified generation method 
    and other parameters. Can be generated from either text or an input image.

    Args:
        folder_style (FolderStyle, optional): The base folder to use. 
          Defaults to FolderStyle.big_sur_light.
        generation_method (IconGenerationMethod, optional): The method to generate the folder icon. 
          Defaults to IconGenerationMethod.NONE.
        preview_size (int, optional): The size of the image to generate, useful for speeding up 
          preview images. If None then uses the maximum size of the base folder image. 
          Defaults to None.
        icon_scale (float, optional): Scale of the icon within, or exceeding, 
          the bounding region. Defaults to 1.0.
        tint_colour ((int * 3), optional): (r, g, b); The colour to tint the whole folder icon. 
          Defaults to None.
        text (str, optional): The text to display on the folder if using the Text generation method. 
          Defaults to None.
        font_style (SFFont, optional): The specified font size to use for generating the  
          text-based icon. Defaults to SFFont.heavy.
        image (Image, optional): PIL Image to generate the icon if using the Image generation method. 
          Defaults to None.

    Returns:
        Image: PIL Image of the resulting folder icon
    """

    # Get base folder image
    folderImage = Image.open(internal_resource_path(
        "assets/" + folderStyle.filename()))

    # Default size is the folder size, otherwise use the specified preview size
    if previewSize:
        size = previewSize
        folderImage = folderImage.resize((size, size))
    else:
        size = folderStyle.size()

    # Darken shadow to match default macOS folders
    folderImage = _increasedShadow(
        folderImage, factor=FOLDER_SHADOW_INCREASE_FACTOR)

    # Generate mask image based on icon generation method
    maskImage = None

    if generationMethod is IconGenerationMethod.NONE:
        if tintColour is None:
            return folderImage
        return adjustedColours(folderImage, folderStyle.baseColour(), tintColour)

    elif generationMethod is IconGenerationMethod.IMAGE:
        maskImage = _generateMaskFromImage(image)

    elif generationMethod is IconGenerationMethod.TEXT or generationMethod is IconGenerationMethod.SYMBOL:
        maskImage = _generateMaskFromText(text, size, fontStyle)

    # Bounding box to place icon
    boundingBoxPercentages = (0.086, 0.29, 0.914, 0.777)
    boundingBox = tuple(int(size * percent)
                        for percent in boundingBoxPercentages)
    newBoundingBox = scaledBox(
        boundingBox, iconScale * ICON_BOX_SCALING_FACTOR, (size, size)
    )

    # Fit the icon mask within the bounding box
    formattedMask = Image.new("L", (size, size), "black")
    scaledImage, pasteBox = _resizeImageInBox(
        maskImage, newBoundingBox)
    formattedMask.paste(scaledImage, pasteBox, scaledImage)

    # Generate the center colour to be a desired colour after the multiply filter
    centerColour = dividedColour(
        folderStyle.baseColour(), folderStyle.icon_colour())

    # Calculate shadow colour to be slightly darker than the center colour
    centerHue, centerSat, centerVal = rgbIntToHsv(centerColour)
    shadowHsvColour = (centerHue, centerSat, centerVal *
                       INNER_SHADOW_COLOUR_SCALING_FACTOR)
    shadowColour = hsvToRgbInt(shadowHsvColour)

    # Create shadow insert image
    shadowImage = Image.composite(
        Image.new("RGB", formattedMask.size, centerColour),
        Image.new("RGB", formattedMask.size, shadowColour),
        formattedMask
    )
    shadowImage = shadowImage.filter(
        ImageFilter.GaussianBlur(INNER_SHADOW_BLUR))
    shadowImage = ImageChops.offset(
        shadowImage, 0, math.floor(size * INNER_SHADOW_Y_OFFSET))
    shadowImage.putalpha(formattedMask)
    shadowInsert = ImageChops.multiply(folderImage, shadowImage)

    # Create highlight insert image
    highlightImage = Image.composite(
        Image.new("RGBA", formattedMask.size, "#131313"),
        Image.new("RGBA", formattedMask.size, "black"),
        formattedMask
    )
    highlightImage = highlightImage.filter(
        ImageFilter.GaussianBlur(OUTER_HIGHLIGHT_BLUR))
    highlightImage = ImageChops.offset(
        highlightImage, 0, math.floor(size * OUTER_HIGHLIGHT_Y_OFFSET))
    highlightImage.putalpha(0)
    highlightInsert = ImageChops.add(folderImage, highlightImage)

    # Combine the two
    result = Image.alpha_composite(highlightInsert, shadowInsert)

    # Apply tint colour if specified
    if tintColour is None:
        return result
    return adjustedColours(result, folderStyle.baseColour(), tintColour)


def _generateMaskFromText(text, image_size, fontStyle=SFFont.heavy):
    """Generates an image mask from the specified text and font parameters. To be used
    in downstream icon generation.

    Args:
        text (str): Text to display
        image_size (int): Size of the image in pixels
        font_style (SFFont, optional): Font weight to use. Defaults to SFFont.heavy.

    Returns:
        Image : PIL Image (L) mask, white subject on black background
    """
    # TODO add multiline support
    # TODO add text aligning
    # TODO add letter size independant mode (make lowercase letters not same height as uppercase)

    # Dissallow really long text entries, greater than 25 characters
    text = text[0:25]

    # Get the font path, either installed or the local backup
    fontPath = getFontLocation(
        fontStyle.filename(), includeInternal=False)
    if fontPath is None:
        fontPath = get_first_font_installed(
            [fontStyle.filename()] + BACKUP_FONTS, includeinternal=True)

    font = ImageFont.truetype(fontPath, int(image_size/2))

    textDrawOptions = {
        "text": text,
        "anchor": "mm",
        "align": "center",
        "spacing": int(image_size / 8),
        "font": font
    }

    # Determine the exact size of the temporary image necessary to draw the complete
    # text with the specified options, avoids an unnecessarily large buffer image

    tempDraw = ImageDraw.Draw(Image.new("L", (0, 0)))
    textBbox = tempDraw.textbbox((0, 0), **textDrawOptions)
    textSize = (textBbox[2] + abs(textBbox[0]),
                textBbox[3] + abs(textBbox[1]))
    textCenter = (abs(textBbox[0]), abs(textBbox[1]))

    textImage = Image.new("L", textSize)
    textDraw = ImageDraw.Draw(textImage)
    textDraw.text(textCenter, **textDrawOptions, fill="white")

    return textImage


def _generateMaskFromImage(image: Image):
    """Generates an image mask from the specified PIL image. To be used
    in downstream icon generation.

    Args:
        image (Image): PIL image (RGB / RGBA) to display

    Returns:
        Image: PIL Image (L) mask, white subject on black background
    """
    whiteBackground = Image.new("L", image.size, "white")
    mask = image if image.mode in ["RGBA", "RGBa"] else None
    whiteBackground.paste(image, mask)
    whiteBackground = _normalizedImage(whiteBackground)

    return ImageChops.invert(whiteBackground)


def adjustedColours(image: Image, baseColour, tintColour):
    """Changes the colours across the specified image by an ammount that would shift the
    'base colour' to the 'tint colour.'

    Args:
        image (Image): PIL Image (RGB / RGBA)
        base_colour (_type_): _description_
        tint_colour (_type_): _description_

    Returns:
        _type_: _description_
    """
    startHue, startSat, startVal = rgbIntToHsv(baseColour)
    finalHue, finalSat, finalVal = rgbIntToHsv(tintColour)

    hueOffset = finalHue - startHue
    satFactor = finalSat / startSat
    valFactor = finalVal / startVal
    # sat_offset = final_sat - start_sat
    # val_offset = final_val - start_val

    def adjustPixelColour(r, g, b):
        h, s, v = rgb_to_hsv(r, g, b)

        h = (h + hueOffset) % 1.0
        s = clamp(s * satFactor, 0.0, 1.0)
        v = clamp(v * valFactor, 0.0, 1.0)
        # s = clamp(s + sat_offset, 0.0, 1.0)
        # v = clamp(v + val_offset, 0.0, 1.0)

        return hsv_to_rgb(h, s, v)

    return image.filter(ImageFilter.Color3DLUT.generate(4, adjustPixelColour, 3))


def _increasedShadow(folderImage, factor):
    """Returns a new image with a more intense shadow by increasing the opacity of pixels
    with tranparency

    Args:
        folder_image (Image): Image to increase shadow on
        factor (float): Scalar value to increase opacity by

    Returns:
        Image: New Image
    """
    r, g, b, a = folderImage.split()
    a = a.point(lambda x: min(int(x * factor), 255))

    return Image.merge("RGBA", (r, g, b, a))


def _normalizedImage(image: Image, steepness=0.18):
    """Normalizes the pixel data from the grayscale image to 0 - 255 and applies a sigmoid function
    to bring values closer to the extremes (0 or 255).

    Args:
        image (Image): PIL Image (L)
        steepness (float, optional): Intensity of sigmoid curve, smaller values lead to
          less separated colours. Defaults to 0.12.

    Returns:
        Image: PIL Image (L) that has been normalized
    """
    minValue, maxValue = image.getextrema()

    def sigmoidNormalize(value):
        normalized_value = int((value-minValue)*255/(maxValue-minValue))
        return 255/(1 + math.exp(-steepness * (normalized_value - 127)))

    try:  # Avoids division by zero error on completely flat images
        return Image.eval(image, sigmoidNormalize)
    except:
        return image


def _resizeImageInBox(image: Image, box):
    """Returns the image scaled into the bounding box with the same aspect ratio, 
    from the center

    Args:
        image (Image): PIL Image
        box (int * 4): Bounding box to insert image into: x1, y1, x2, y2

    Returns:
        Image, (int * 4): Scaled image, New bounding box to insert into
    """
    topPoint, bottomPoint = box[0:2], box[2:4]
    boxSize = (bottomPoint[0] - topPoint[0], bottomPoint[1] - topPoint[1])

    downscaleRatio = min(
        boxSize[0] / image.size[0], boxSize[1] / image.size[1])
    scaledImage = image.resize(
        (int(image.width * downscaleRatio), int(image.height * downscaleRatio)))

    startingX = topPoint[0] + int((boxSize[0] - scaledImage.size[0]) / 2)
    startingY = topPoint[1] + int((boxSize[1] - scaledImage.size[1]) / 2)

    newBox = (
        startingX, startingY,
        startingX + scaledImage.size[0],
        startingY + scaledImage.size[1]
    )

    return (scaledImage, newBox)


def scaledBox(box, scale, maxSize):
    """Returns the box scaled from the center by a constant amount along the diagonal,
    clipped into the region from (0,0) to max_size

    Args:
        box (int/float * 4): Box to scale: x1, y1, x2, y2
        scale (float): Constant scalar
        max_size (int, int): Maximum size to clip scaled box to

    Returns:
        (int * 4): Scaled box
    """
    topPoint, bottomPoint = box[0:2], box[2:4]
    center = (int((bottomPoint[0] + topPoint[0])/2),
              int((bottomPoint[1] + topPoint[1])/2))

    # Scaled offsets from the center point (along the diagonals)
    topOffset = (int((topPoint[0] - center[0])*scale),
                 int((topPoint[1] - center[1])*scale))
    bottomOffset = (int(
        (bottomPoint[0] - center[0])*scale), int((bottomPoint[1] - center[1])*scale))

    # Re-add offsets to the center point to get absolute position
    newTopPoint = (max(0, center[0] + topOffset[0]),
                   max(0, center[1] + topOffset[1]))
    newBottomPoint = (min(maxSize[0], center[0] + bottomOffset[0]),
                      min(maxSize[1], center[1] + bottomOffset[1]))

    return (*newTopPoint, *newBottomPoint)
