from enum import Enum
from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QPaintEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLayout, QLineEdit, QRadioButton, QSizePolicy, QSlider, QVBoxLayout, QWidget
from PIL.ImageQt import ImageQt

from fancyfolders.constants import VERSION, FolderStyle, TintColour
from fancyfolders.utilities import internal_resource_path


class CenterFolderIcon(QLabel):
  """Displays the preview folder image and scales it when the size of the widget changes.
  """

  MINIMUM_SIZE = (400, 340)

  def __init__(self):
    super().__init__()

    self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.setMinimumSize(*self.MINIMUM_SIZE)
    self.setAcceptDrops(True)

  def set_image(self, image, folder_style=FolderStyle.big_sur_light):
    """Sets the image on the display.

    Args:
        image (Image): PIL Image to display
        folder_style (FolderStyle, optional): The folder style of the image to set in order to 
          crop away any extra space. Defaults to FolderStyle.big_sur_light.
    """
    crop_rect_percentages = folder_style.preview_crop_percentages()
    crop_rect = QRect()
    crop_rect.setCoords(*tuple(int(image.size[0] * percent) for percent in crop_rect_percentages))
    
    # Remove any unnecessary blank space on the image to avoid weird UI layout
    cropped_image = ImageQt(image).copy(crop_rect)

    self.pixmap = QPixmap(cropped_image)
    self.update()

  def paintEvent(self, _: QPaintEvent) -> None:
    """Custom paint event to scale the image when the size of the widget changes.
    """
    dpi_ratio = self.devicePixelRatio()
    self.pixmap.setDevicePixelRatio(dpi_ratio)

    size = QSize(int(self.size().width() * dpi_ratio), int(self.size().height() * dpi_ratio))
    painter = QPainter(self)
    point = QPoint(0,0)

    scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    point.setX(int((size.width() - scaledPix.width())/(2 * dpi_ratio)))
    point.setY(int((size.height() - scaledPix.height())/(2 * dpi_ratio)))

    painter.drawPixmap(point, scaledPix)
    painter.end()

class ColourRadioButton(QRadioButton):
  """Custom button to be used in the colour palette selector for folder tint.
  """

  BORDER_RADIUS = 5.0
  ACTIVE_BORDER_WIDTH = 3.0
  INACTIVE_BORDER_WIDTH = 2.0

  INACTIVE_BORDER_COLOUR = (212, 212, 212)
  ACTIVE_BORDER_COLOUR = (100, 198, 237)
  
  EMPTY_FILL_COLOUR = (255, 255, 255)

  def __init__(self, colour=None, default=False, multicolour=False, *args, **kwargs):
    """Initializes the ColourRadioButton

    Args:
        colour ((int * 3), optional): (r, g, b); Colour to set. If None, requires another option.
        default (bool, optional): Whether the button represents the default colour option, aka no 
          colour. Defaults to False.
        multicolour (bool, optional): Whether the button represents the custom colour selection
          option. Defaults to False.
    """
    super().__init__(*args, **kwargs)

    self.colour = colour
    self.is_default = default
    self.is_multicolour = multicolour

    self.setMinimumHeight(30)

  def hitButton(self, point: QPoint) -> bool:
    """Changes the area where the button is clickable.
    """
    return self._get_center_square().contains(point)

  def paintEvent(self, _: QPaintEvent) -> None:
    """Custom paint event to draw the colour button using either the colour, or
    special style as specified in the init.
    """
    center_rect = self._get_center_square()

    border_width = self.ACTIVE_BORDER_WIDTH if self.isChecked() else self.INACTIVE_BORDER_WIDTH
    border_colour = self.ACTIVE_BORDER_COLOUR if self.isChecked() else self.INACTIVE_BORDER_COLOUR

    fill_colour = self.colour if self.colour is not None else self.EMPTY_FILL_COLOUR

    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)

    outline_pen = QPen()
    outline_pen.setWidth(border_width)
    outline_pen.setColor(QColor.fromRgb(*border_colour))
    
    fill_brush = QBrush()
    fill_brush.setColor(QColor.fromRgb(*fill_colour))
    fill_brush.setStyle(Qt.SolidPattern)

    painter.setPen(outline_pen)
    painter.setBrush(fill_brush)

    border_offset = border_width * 0.8
    painter.drawRoundedRect(
      center_rect.adjusted(border_offset, border_offset, -border_offset, -border_offset), 
      self.BORDER_RADIUS - border_offset, self.BORDER_RADIUS - border_offset
    )

    # Draw custom features for the default option
    if self.is_default:
      dash_pen = QPen()
      dash_pen.setColor(QColor.fromRgb(*self.INACTIVE_BORDER_COLOUR))
      dash_pen.setCapStyle(Qt.RoundCap)
      dash_pen.setWidth(3)
      
      painter.setPen(dash_pen)

      start_point = center_rect.topLeft() + QPoint(8, 8)
      end_point = center_rect.bottomRight() + QPoint(-8, -8)

      painter.drawLine(start_point, end_point)

    # Draw custom feature for the custom colour option
    if self.is_multicolour:
      center_point = center_rect.center()
      rainbow_gradient = QConicalGradient(center_point, 0)
      rainbow_gradient.setColorAt(0.0, QColor(*TintColour.red.value))
      rainbow_gradient.setColorAt(0.2, QColor(*TintColour.yellow.value))
      rainbow_gradient.setColorAt(0.5, QColor(*TintColour.orange.value))
      rainbow_gradient.setColorAt(0.8, QColor(*TintColour.purple.value))
      rainbow_gradient.setColorAt(1.0, QColor(*TintColour.red.value))

      rainbow_pen = QPen(rainbow_gradient, 5.0)

      painter.setPen(rainbow_pen)
      painter.setBrush(Qt.NoBrush)

      painter.drawEllipse(center_point + QPoint(1, 1), 6, 6)

    painter.end()

  def _get_center_square(self):
    """Returns the square contained within the center of the widget size. Assumes that 
    the width is greater than the height.

    Returns:
        QRect: Rect containing the center square
    """
    size = self.size()

    width_adjustment = (size.width() - size.height()) / 2
    total_rect = QRect(QPoint(0, 0), size)
    
    return total_rect.adjusted(width_adjustment, 0, -width_adjustment, 0)

class NonEditableLine(QLineEdit):
  def __init__(self, placeholder_text):
    super().__init__()

    self.setPlaceholderText(placeholder_text)

    self.setReadOnly(True)
    self.setAlignment(Qt.AlignCenter)
  
  def set_text(self, text):
    self.text = text

class TickStyle(Enum):
  NONE = 0
  CENTER = 1
  EACH = 2

class HorizontalSlider(QSlider):
  def __init__(self, max_ticks, start_value=0, tick_style = TickStyle.NONE):
    super().__init__(Qt.Horizontal)

    self.setMinimum(1)
    self.setMaximum(max_ticks)
    self.setMinimumHeight(50)
    self.setValue(start_value)
    self.setTracking(True)

    self.setTickPosition(QSlider.NoTicks if tick_style is TickStyle.NONE else QSlider.TicksBelow)

    if tick_style is TickStyle.CENTER:
      self.setTickInterval(max_ticks + 1)
    elif tick_style is TickStyle.EACH:
      self.setTickInterval(1)

class AboutPanel(QDialog):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("About Fancy Folders")

    app_icon_image = QPixmap(internal_resource_path("assets/app_icon.png"))
    dpi_ratio = self.devicePixelRatio()
    app_icon_image.setDevicePixelRatio(dpi_ratio)

    size = QSize(int(100 * dpi_ratio), int(100 * dpi_ratio))

    self.icon = QLabel()
    self.icon.setPixmap(app_icon_image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    self.icon.setMinimumWidth(200)
    # self.icon.setScaledContents(True)

    self.version_string = QLabel("Version " + VERSION)
    self.version_string.setAlignment(Qt.AlignCenter)

    layout = QVBoxLayout()
    layout.setSizeConstraint(QLayout.SetFixedSize)
    layout.addWidget(self.icon, alignment=Qt.AlignCenter)
    layout.addWidget(self.version_string, alignment=Qt.AlignCenter)
    self.setLayout(layout)

