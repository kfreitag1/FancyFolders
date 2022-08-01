
import io
import os
import sys
from PIL import Image, ImageQt
from PySide6.QtCore import QBuffer

from PySide6.QtGui import QImage

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# COLOUR UTILITIES

def divide_colour(starting_colour, final_colour):
  pass

