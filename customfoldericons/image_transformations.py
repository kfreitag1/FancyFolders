import enum
import math
from sys import maxsize
from PIL import ImageFont, Image, ImageDraw, ImageFilter, ImageChops, ImageColor
from PySide6.QtCore import QSize

from customfoldericons.utilities import resource_path

class FolderStyle(enum.Enum):
  big_sur_light = "big_sur_light.png"
  big_sur_dark = "big_sur_dark.png"
  catalina = "catalina.png"

def generate_folder_icon_from_text(text, folder_style = FolderStyle.big_sur_light, **options):
  base_folder_image = Image.open(resource_path("assets/" + folder_style.value))

  folder_size = base_folder_image.size
  buffer_size = (folder_size[0] * 3, folder_size[1] * 2)


  # TODO: add option to change font
  font = ImageFont.truetype("SF-Pro-Text-Regular.otf", int(folder_size[0]/2))

  text_image = Image.new("L", buffer_size)
  text_draw = ImageDraw.Draw(text_image)

  text_draw.text((buffer_size[0]/2, buffer_size[1]/2), text, fill="white", anchor="mm", font=font)
  text_bbox = text_draw.textbbox((buffer_size[0]/2, buffer_size[1]/2), text, anchor="mm", font=font)

  text_image = text_image.crop(text_bbox)
  
  # text_draw.rectangle(text_draw.textbbox((size[0]/2, size[1]/2), text, anchor="mm", font=font) , outline="red")
  # text_draw.line( [mask_image.width/2, 0, mask_image.width/2, mask_image.height] , width=2, fill="red")

  return _generate_folder_icon(base_folder_image, text_image, **options)


def generate_folder_icon_from_image(image: Image, folder_style = FolderStyle.big_sur_light, **options):
  base_folder_image = Image.open(resource_path("assets/" + folder_style.value))
  
  image = image.convert("L")
  image = normalized_image(image)
  image = ImageChops.invert(image)

  return _generate_folder_icon(base_folder_image, image, **options)


def _generate_folder_icon(folder_image: Image, mask_image: Image, icon_scale=0.9, shadow_color="#adbfc7", center_color="#c5dbe3"):
  folder_size = folder_image.size

  bounding_box_percentages = (0.086, 0.29, 0.914, 0.777)
  bounding_box = tuple(int(folder_size[0] * percent) for percent in bounding_box_percentages)
  new_bounding_box = scaled_box(bounding_box, icon_scale, folder_size)

  formatted_mask = Image.new("L", folder_size, "black")

  scaled_image, paste_box = resize_image_in_box(mask_image, new_bounding_box)
  formatted_mask.paste(scaled_image, paste_box, scaled_image)

  # draw = ImageDraw.Draw(formatted_mask)
  # draw.rectangle(bounding_box, outline="red")
  # draw.rectangle(new_bounding_box, outline="green")

  # formatted_mask.show()

  logo_image = Image.composite(
    Image.new("RGB", formatted_mask.size, center_color),
    Image.new("RGB", formatted_mask.size, shadow_color),
    formatted_mask
  )

  blur_filter = ImageFilter.GaussianBlur(3)
  logo_image = logo_image.filter(blur_filter)
  logo_image = ImageChops.offset(logo_image, 2)

  logo_image.putalpha(formatted_mask)

  # icon_insert = ImageChops.offset(
  #   ImageChops.multiply(folder_image, logo_image), 
  #   int(logo_offset[0] * formatted_mask.size[0]), int(logo_offset[1] * formatted_mask.size[1])
  # )
  icon_insert = ImageChops.multiply(folder_image, logo_image)

  folder_image.alpha_composite(icon_insert)

  return folder_image


def normalized_image(image: Image, steepness=0.15):
  """Normalizes the pixel data from the grayscale image to 0 - 255 and applies a sigmoid function
  to bring values closer to the extremes (0 or 255).

  Args:
      image (Image): PIL Image, grayscale (mode "L")
      steepness (float, optional): Intensity of sigmoid curve, smaller values lead to
        less separated colours. Defaults to 0.15.

  Returns:
      Image: Normalized image
  """
  min_value, max_value = image.getextrema()

  def sigmoid_normalize(value):
    normalized_value = int((value-min_value)*255/(max_value-min_value))
    return 255/(1 + math.exp(-steepness * (normalized_value - 127)))

  try: # Avoids division by zero error on completely flat images
    return Image.eval(image, sigmoid_normalize)
  except:
    return image


def resize_image_in_box(image: Image, box):
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