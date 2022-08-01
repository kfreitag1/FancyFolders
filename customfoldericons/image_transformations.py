import math
from PIL import ImageFont, Image, ImageDraw, ImageFilter, ImageChops
from customfoldericons.constants import BACKUP_FONTS, ICON_BOX_SCALING_FACTOR, SHADOW_INCREASE_FACTOR, FolderStyle, SFFont

from customfoldericons.utilities import divided_colour, get_first_font_installed, resource_path

def generate_mask_from_text(text, font_style = SFFont.heavy, folder_style = FolderStyle.big_sur_light):
  if text.strip() == "": return None

  folder_size = folder_style.size()

  font_filename = get_first_font_installed([font_style.filename()] + BACKUP_FONTS)
  print("first font filename", font_filename)
  font = ImageFont.truetype(font_filename, int(folder_size/2))

  text_draw_options = {
    "text": text,
    "anchor": "mm",
    "align": "center",
    "spacing": int(folder_size / 8),
    "font": font
  }
  
  temp_draw = ImageDraw.Draw(Image.new("L", (0,0)))
  text_bbox = temp_draw.textbbox((0, 0), **text_draw_options)
  text_size = (text_bbox[2] + abs(text_bbox[0]), text_bbox[3] + abs(text_bbox[1]))
  text_center = (abs(text_bbox[0]), abs(text_bbox[1]))

  text_image = Image.new("L", text_size)
  text_draw = ImageDraw.Draw(text_image)
  text_draw.text(text_center, **text_draw_options, fill="white")

  # text_draw.rectangle(text_draw.textbbox((size[0]/2, size[1]/2), text, anchor="mm", font=font) , outline="red")
  # text_draw.line( [mask_image.width/2, 0, mask_image.width/2, mask_image.height] , width=2, fill="red")

  return text_image


def generate_mask_from_image(image: Image):
  image = image.convert("L")
  image = normalized_image(image)
  return ImageChops.invert(image)


def generate_folder_icon(folder_style: FolderStyle, mask_image: Image = None, icon_scale=1.0, shadow_colour="#78b4cc"):
  # TODO make shadows and highlights independant
  # TODO make shadow and center color based on single final colour
  folder_image = Image.open(resource_path("assets/" + folder_style.filename()))
  folder_image = increased_shadow(folder_image, factor=SHADOW_INCREASE_FACTOR)

  if mask_image is None: return folder_image

  folder_size = folder_style.size()

  bounding_box_percentages = (0.086, 0.29, 0.914, 0.777)
  bounding_box = tuple(int(folder_size * percent) for percent in bounding_box_percentages)
  new_bounding_box = scaled_box(
    bounding_box, icon_scale * ICON_BOX_SCALING_FACTOR, (folder_size, folder_size)
  )

  formatted_mask = Image.new("L", (folder_size, folder_size), "black")

  scaled_image, paste_box = resize_image_in_box(mask_image, new_bounding_box)
  formatted_mask.paste(scaled_image, paste_box, scaled_image)

  # formatted_mask.show()

  # draw = ImageDraw.Draw(formatted_mask)
  # draw.rectangle(bounding_box, outline="red")
  # draw.rectangle(new_bounding_box, outline="green")

  # formatted_mask.show()

  center_colour = divided_colour(folder_style.base_colour(), folder_style.icon_colour())

  shadow_image = Image.composite(
    Image.new("RGB", formatted_mask.size, center_colour),
    Image.new("RGB", formatted_mask.size, shadow_colour),
    formatted_mask
  )
  shadow_image = shadow_image.filter(ImageFilter.GaussianBlur(3))
  shadow_image = ImageChops.offset(shadow_image, 0, 3)

  shadow_image.putalpha(formatted_mask)
  # shadow_image.show()

  shadow_insert = ImageChops.multiply(folder_image, shadow_image)
  # shadow_insert.show()



  highlight_image = Image.composite(
    Image.new("RGBA", formatted_mask.size, "#131313"),
    Image.new("RGBA", formatted_mask.size, "black"),
    formatted_mask
  )
  highlight_image = highlight_image.filter(ImageFilter.GaussianBlur(6))
  highlight_image = ImageChops.offset(highlight_image, 0, 8)
  # highlight_image.show()
  highlight_image.putalpha(0)
  # highlight_image.show()

  highlight_insert = ImageChops.add(folder_image, highlight_image)
  # highlight_insert.show()


  # icon_insert = ImageChops.offset(
  #   ImageChops.multiply(folder_image, logo_image), 
  #   int(logo_offset[0] * formatted_mask.size[0]), int(logo_offset[1] * formatted_mask.size[1])
  # )

  return Image.alpha_composite(highlight_insert, shadow_insert)

def increased_shadow(folder_image, factor):
  r, g, b, a = folder_image.split()
  a = a.point(lambda x: min(int(x * factor), 255))
  return Image.merge("RGBA", (r, g, b, a))

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