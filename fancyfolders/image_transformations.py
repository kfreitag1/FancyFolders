from colorsys import hsv_to_rgb, rgb_to_hsv
import math
from PIL import ImageFont, Image, ImageDraw, ImageFilter, ImageChops
from fancyfolders.constants import BACKUP_FONTS, ICON_BOX_SCALING_FACTOR, FOLDER_SHADOW_INCREASE_FACTOR, INNER_SHADOW_BLUR, INNER_SHADOW_COLOUR_SCALING_FACTOR, INNER_SHADOW_Y_OFFSET, OUTER_HIGHLIGHT_BLUR, OUTER_HIGHLIGHT_Y_OFFSET, FolderStyle, IconGenerationMethod, SFFont

from fancyfolders.utilities import clamp, divided_colour, get_font_location, get_first_font_installed, hsv_to_rgb_int, internal_resource_path, rgb_int_to_hsv

def generate_folder_icon(folder_style: FolderStyle = FolderStyle.big_sur_light, generation_method: IconGenerationMethod = IconGenerationMethod.NONE, preview_size = None, icon_scale = 1.0, tint_colour = None, text = None, font_style = SFFont.heavy, image = None):
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
  folder_image = Image.open(internal_resource_path("assets/" + folder_style.filename()))

  # Default size is the folder size, otherwise use the specified preview size
  if preview_size:
    size = preview_size
    folder_image = folder_image.resize((size, size))
  else:
    size = folder_style.size()

  # Darken shadow to match default macOS folders
  folder_image = _increased_shadow(folder_image, factor=FOLDER_SHADOW_INCREASE_FACTOR)

  # Generate mask image based on icon generation method
  mask_image = None

  if generation_method == IconGenerationMethod.NONE:
    if tint_colour is None: 
      return folder_image
    return adjusted_colours(folder_image, folder_style.base_colour(), tint_colour)

  elif generation_method == IconGenerationMethod.IMAGE:
    mask_image = _generate_mask_from_image(image)

  elif generation_method == IconGenerationMethod.TEXT:
    mask_image = _generate_mask_from_text(text, size, font_style)

  # Bounding box to place icon
  bounding_box_percentages = (0.086, 0.29, 0.914, 0.777)
  bounding_box = tuple(int(size * percent) for percent in bounding_box_percentages)
  new_bounding_box = scaled_box(
    bounding_box, icon_scale * ICON_BOX_SCALING_FACTOR, (size, size)
  )

  # Fit the icon mask within the bounding box
  formatted_mask = Image.new("L", (size, size), "black")
  scaled_image, paste_box = _resize_image_in_box(mask_image, new_bounding_box)
  formatted_mask.paste(scaled_image, paste_box, scaled_image)

  # Generate the center colour to be a desired colour after the multiply filter
  center_colour = divided_colour(folder_style.base_colour(), folder_style.icon_colour())
  
  # Calculate shadow colour to be slightly darker than the center colour
  center_hue, center_sat, center_val = rgb_int_to_hsv(center_colour)
  shadow_hsv_colour = (center_hue, center_sat, center_val * INNER_SHADOW_COLOUR_SCALING_FACTOR)
  shadow_colour = hsv_to_rgb_int(shadow_hsv_colour)

  # Create shadow insert image
  shadow_image = Image.composite(
    Image.new("RGB", formatted_mask.size, center_colour),
    Image.new("RGB", formatted_mask.size, shadow_colour),
    formatted_mask
  )
  shadow_image = shadow_image.filter(ImageFilter.GaussianBlur(INNER_SHADOW_BLUR))
  shadow_image = ImageChops.offset(shadow_image, 0, math.floor(size * INNER_SHADOW_Y_OFFSET))
  shadow_image.putalpha(formatted_mask)
  shadow_insert = ImageChops.multiply(folder_image, shadow_image)

  # Create highlight insert image
  highlight_image = Image.composite(
    Image.new("RGBA", formatted_mask.size, "#131313"),
    Image.new("RGBA", formatted_mask.size, "black"),
    formatted_mask
  )
  highlight_image = highlight_image.filter(ImageFilter.GaussianBlur(OUTER_HIGHLIGHT_BLUR))
  highlight_image = ImageChops.offset(highlight_image, 0, math.floor(size * OUTER_HIGHLIGHT_Y_OFFSET))
  highlight_image.putalpha(0)
  highlight_insert = ImageChops.add(folder_image, highlight_image)

  # Combine the two
  result = Image.alpha_composite(highlight_insert, shadow_insert)

  # Apply tint colour if specified
  if tint_colour is None: 
    return result
  return adjusted_colours(result, folder_style.base_colour(), tint_colour)


def _generate_mask_from_text(text, image_size, font_style = SFFont.heavy):
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
  font_path = get_font_location(font_style.filename(), include_internal=False)
  if font_path is None:
    font_path = get_first_font_installed([font_style.filename()] + BACKUP_FONTS, include_internal=True)

  font = ImageFont.truetype(font_path, int(image_size/2))

  text_draw_options = {
    "text": text,
    "anchor": "mm",
    "align": "center",
    "spacing": int(image_size / 8),
    "font": font
  }
  
  # Determine the exact size of the temporary image necessary to draw the complete
  # text with the specified options, avoids an unnecessarily large buffer image

  temp_draw = ImageDraw.Draw(Image.new("L", (0,0)))
  text_bbox = temp_draw.textbbox((0, 0), **text_draw_options)
  text_size = (text_bbox[2] + abs(text_bbox[0]), text_bbox[3] + abs(text_bbox[1]))
  text_center = (abs(text_bbox[0]), abs(text_bbox[1]))

  text_image = Image.new("L", text_size)
  text_draw = ImageDraw.Draw(text_image)
  text_draw.text(text_center, **text_draw_options, fill="white")

  return text_image


def _generate_mask_from_image(image: Image):
  """Generates an image mask from the specified PIL image. To be used
  in downstream icon generation.

  Args:
      image (Image): PIL image (RGB / RGBA) to display

  Returns:
      Image: PIL Image (L) mask, white subject on black background
  """
  white_background = Image.new("L", image.size, "white")
  mask = image if image.mode in ["RGBA", "RGBa"] else None
  white_background.paste(image, mask)
  white_background = _normalized_image(white_background)

  return ImageChops.invert(white_background)


def adjusted_colours(image: Image, base_colour, tint_colour):
  """Changes the colours across the specified image by an ammount that would shift the
  'base colour' to the 'tint colour.'

  Args:
      image (Image): PIL Image (RGB / RGBA)
      base_colour (_type_): _description_
      tint_colour (_type_): _description_

  Returns:
      _type_: _description_
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




def _increased_shadow(folder_image, factor):
  """Returns a new image with a more intense shadow by increasing the opacity of pixels
  with tranparency

  Args:
      folder_image (Image): Image to increase shadow on
      factor (float): Scalar value to increase opacity by

  Returns:
      Image: New Image
  """
  r, g, b, a = folder_image.split()
  a = a.point(lambda x: min(int(x * factor), 255))

  return Image.merge("RGBA", (r, g, b, a))


def _normalized_image(image: Image, steepness=0.18):
  """Normalizes the pixel data from the grayscale image to 0 - 255 and applies a sigmoid function
  to bring values closer to the extremes (0 or 255).

  Args:
      image (Image): PIL Image (L)
      steepness (float, optional): Intensity of sigmoid curve, smaller values lead to
        less separated colours. Defaults to 0.12.

  Returns:
      Image: PIL Image (L) that has been normalized
  """
  min_value, max_value = image.getextrema()

  def sigmoid_normalize(value):
    normalized_value = int((value-min_value)*255/(max_value-min_value))
    return 255/(1 + math.exp(-steepness * (normalized_value - 127)))

  try: # Avoids division by zero error on completely flat images
    return Image.eval(image, sigmoid_normalize)
  except:
    return image


def _resize_image_in_box(image: Image, box):
  """Returns the image scaled into the bounding box with the same aspect ratio, 
  from the center

  Args:
      image (Image): PIL Image
      box (int * 4): Bounding box to insert image into: x1, y1, x2, y2

  Returns:
      Image, (int * 4): Scaled image, New bounding box to insert into
  """
  top_point, bottom_point = box[0:2], box[2:4]
  box_size = (bottom_point[0] - top_point[0], bottom_point[1] - top_point[1])

  downscale_ratio = min(box_size[0] / image.size[0], box_size[1] / image.size[1])
  scaled_image = image.resize((int(image.width * downscale_ratio), int(image.height * downscale_ratio)))

  starting_x = top_point[0] + int((box_size[0] - scaled_image.size[0]) / 2)
  starting_y = top_point[1] + int((box_size[1] - scaled_image.size[1]) / 2)

  new_box = (
    starting_x, starting_y,
    starting_x + scaled_image.size[0],
    starting_y + scaled_image.size[1]
  )

  return (scaled_image, new_box)


def scaled_box(box, scale, max_size):
  """Returns the box scaled from the center by a constant amount along the diagonal,
  clipped into the region from (0,0) to max_size

  Args:
      box (int/float * 4): Box to scale: x1, y1, x2, y2
      scale (float): Constant scalar
      max_size (int, int): Maximum size to clip scaled box to

  Returns:
      (int * 4): Scaled box
  """
  top_point, bottom_point = box[0:2], box[2:4]
  center = (int((bottom_point[0] + top_point[0])/2), int((bottom_point[1] + top_point[1])/2))

  # Scaled offsets from the center point (along the diagonals)
  top_offset = (int((top_point[0] - center[0])*scale), int((top_point[1] - center[1])*scale))
  bottom_offset = (int((bottom_point[0] - center[0])*scale), int((bottom_point[1] - center[1])*scale))

  # Re-add offsets to the center point to get absolute position
  new_top_point = (max(0, center[0] + top_offset[0]), max(0, center[1] + top_offset[1]))
  new_bottom_point = (min(max_size[0], center[0] + bottom_offset[0]), min(max_size[1], center[1] + bottom_offset[1]))

  return (*new_top_point, *new_bottom_point)