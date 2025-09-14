from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget, QListWidgetItem, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen

class ShapePalette(QWidget):
    shape_selected = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_category = "processes"
        self.setup_ui()
        self.populate_shapes()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        title=QLabel("Shape Palette")
        title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px;")
        layout.addWidget(title)
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Processes", "Data Stores", "External Entities", "Data Flows", "Trust Boundaries", "Threats"
        ])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)
        self.shape_list = QListWidget()
        self.shape_list.itemClicked.connect(self.on_shape_clicked)
        layout.addWidget(self.shape_list)
        layout.addStretch()
        self.setLayout(layout)
        self.setMaximumWidth(200)
    def populate_shapes(self):
        self.shape_list.clear()
        # AHHHHHHHHHHHHHHHHHHHHHH
        shapes = {
            "Processes": [
                ("process", "Process/Function"),
                ("web_service", "Web Service"),
                ("database_process", "Database Process"),
                ("user_process", "User Process")
            ],
            "Data Stores": [
                ("database", "Database"),
                ("file_system", "File System"),
                ("cache", "Cache"),
                ("log_store", "Log Store")
            ],
            "External Entities": [
                ("user", "User/Actor"),
                ("external_system", "External System"),
                ("third_party", "Third Party Service"),
                ("admin", "Administrator")
            ],
            "Trust Boundaries": [
                ("trust_boundary", "Trust Boundary"),
                ("network_boundary", "Network Boundary"),
                ("process_boundary", "Process Boundary")
            ],
            "Threats": [
                ("threat", "Generic Threat"),
                ("vulnerability", "Vulnerability"),
                ("attack_vector", "Attack Vector"),
                ("risk", "Risk")
            ]
        }
        current_shapes = shapes.get(self.category_combo.currentText(), [])
        for shape_type, display_name in current_shapes:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, shape_type)
            icon = self.create_shape_icon(shape_type)
            item.setIcon(icon)
            self.shape_list.addItem(item)
    
    def create_shape_icon(self, shape_type):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if shape_type in ["process", "web_service", "database_process", "user_process"]:
            painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawEllipse(4, 4, 24, 24)
        if shape_type in ["user", "external_system", "third_party", "admin"]:
            painter.setBrush(QBrush(Qt.GlobalColor.yellow))
            painter.setPen(QPen(Qt.GlobalColor.yellow))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(4, 4, 24, 24)
        elif shape_type in ["threat", "vulnerability", "attack_vector", "risk"]:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            points = [
                (16, 4),
                (28, 16),
                (16, 28),
                (4, 16)
            ]
            from PyQt6.QtGui import QPolygon
            from PyQt6.QtCore import QPoint
            polygon = QPolygon([QPoint(x, y) for x, y in points])
            painter.drawPolygon(polygon)
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(4, 4, 24, 24)
        painter.end()
        return QIcon(pixmap)
    
    def on_category_changed(self, category):
        self.current_category = category.lower().replace(" ", "_")
        self.populate_shapes()
    
    def on_shape_clicked(self, item):
        shape_type = item.data(Qt.ItemDataRole.UserRole)
        category = self.current_category
        self.shape_selected.emit(category, shape_type)

        print(f"Selected: {shape_type} from category: {category}")