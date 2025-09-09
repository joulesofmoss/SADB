import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
#directory
SAVE_DIR = "diagrams"
os.makedirs(SAVE_DIR, exist_ok=True)
#UI
DEFAULT_SHAPE_WIDTH = 100
DEFAULT_SHAPE_HEIGHT = 60
DEFAULT_CIRCLE_SIZE = 60
HANDLE_SIZE = 10
GRID_SIZE = 50
#Colours
BACKGROUND_COLOR = QColor(0, 0, 0)
GRID_COLOR = QColor(40, 40, 40)
DEFAULT_SHAPE_COLOR = QColor(Qt.GlobalColor.lightGray)
CONNECTOR_COLOR = QColor(Qt.GlobalColor.white)
PENDING_COLOR = QColor(Qt.GlobalColor.red)