from PIL import ImageFont, Image, ImageDraw, ImageFilter, ImageChops

from customfoldericons.utilities import resource_path

def generate_icon(folder_pathname, icon):
  font = ImageFont.truetype("SF-Pro-Display-Bold.otf", 160)
  inner_shadow = Image.new("RGB", (400, 400), "#adbfc7")
  mask_image = Image.new("L", (400,400))

  d = ImageDraw.Draw(inner_shadow)
  d.text((200, 200), "􀊱", fill="#c5dbe3", anchor="mm", font=font)

  d2 = ImageDraw.Draw(mask_image)
  d2.text((200, 200), "􀊱", fill="white", anchor="mm", font=font)

  blur_filter = ImageFilter.GaussianBlur(3)
  inner_shadow = inner_shadow.filter(blur_filter)
  # inner_shadow.show()
  inner_shadow = ImageChops.offset(inner_shadow, 2)
  # inner_shadow.show()

  inner_shadow.putalpha(mask_image)
  # inner_shadow.show()

  # merged = Image.composite(inner_shadow, Image.new("RGBA", (400,400), "white"), mask_image)

  folder_icon = Image.open(resource_path("assets/big_sur_dark.png"))
  folder_icon = folder_icon.resize((400,400))

  icon_insert = ImageChops.offset(ImageChops.multiply(folder_icon, inner_shadow), 0, 15)

  folder_icon.alpha_composite(icon_insert)

  return folder_icon