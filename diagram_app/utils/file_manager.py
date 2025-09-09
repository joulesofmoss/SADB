import json
import sys
import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QColor
from config import SAVE_DIR
from models.shape_item import ShapeItem
from models.connector_item import ConnectorItem
from errorLogging import getLogger, FileOperationHandler, validate_file_path, gui_safe_execute
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from errorLogging import getLogger, FileOperationHandler, validate_file_path, gui_safe_execute, PerformanceMonitor, erorrHandler
from datetime import datetime


class FileManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = getLogger("file_manager")
#    @gui_safe_execute
    def save_diagram(self): # savin'
        self.logger.info("Starting diagram savin!")
        path, _ = QFileDialog.getSaveFileName(self.main_window, "Save Diagram", SAVE_DIR, "JSON Files (*.json)")
        if not path:
            self.logger.info("Cancelled!")
            return
        try:
            validate_file_path(path, "write")
        except Exception as e:
             self.logger.error(f"Invalid save path: {e}")
             return
        
        with FileOperationHandler("save diagram", path):
             with PerformanceMonitor("diagram serialization"):
                  data = {
                       "shapes": [],
                       "connectors": [],
                       "metadata": {
                            "version": "1.0",
                            "created_at": str(datetime.now()),
                            "shape_count": len(self.main_window.shapes),
                            "connector_count": len(self.main_window.connector)
                       }
                  }

                  for i, shape in enumerate(self.main_window.shapes):
                       try:
                            rect = shape.sceneBoundingRect()
                            shape_data = {
                                 "type": shape.item_type,
                                 "x": rect.x(), "y": rect.y(),
                                 "label": getattr(shape,'label', ''),
                                 "colour": shape.colour.name() if hasattr(shape, 'colour') else '#ffffff'
                            }
                            data["shapes"].append(shape_data)
                       except Exception as e:
                            self.logger.error(f"Failed to serialize shape {i}: {e}")
                            continue
                  for i, conn in enumerate(self.main_window.connectors):
                       try:
                            start_idx = self.main_window.shapes.index(conn.start_shape)
                            end_idx = self.main_window.shapes.index(conn.end_shape)
                            data["connectors"].append({
                                 "start": start_idx,
                                 "end": end_idx,
                                 "type": getattr(conn, 'connector_type', 'line'),
                                 "metadata": getattr(conn, 'metadata', {})
                            })
                       except ValueError as e:
                            self.logger.error(f"Failed to serialize connector {i}: shape not found in list")
                            continue
                       except Exception as e:
                            self.logger.error(f"Failed to serialize connector {i}: {e}")
                            continue
        with open(path, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Diagram saved successfully to {path}")
        QMessageBox.information(self.main_window, "Success", f"Diagram saved to {path}")  
#    @gui_safe_execute
    def load_diagram(self): #loadin'
        self.logger.info("Starting to load!")
        path, _=QFileDialog.getOpenFileName(
             self.main_window, "Load Diagram", SAVE_DIR, "JSON Files (*.json)"
        )
        if not path:
             self.logger.info("Load operation cancelled by user")
             return
        with FileOperationHandler("load diagram", path):
             validate_file_path(path, "read")

             with PerformanceMonitor("diagram loading"):
                  with erorrHandler("clearing existing diagram"):
                       self.main_window.scene.clear()
                       self.main_window.shapes.clear()
                       self.main_window.connectors.clear()
                    
                  with open(path, 'r', encoding='utf-8') as f:
                       data=json.load(f)

                  if not isinstance(data, dict):
                       raise ValueError("Invalid file format: not a JSON object")

                  if "shapes" not in data:
                       raise ValueError ("Invalid file format: missing 'shapes' key")
                  loaded_shapes = []
                  for i, shape_data in enumerate(data["shapes"]):
                       try:
                            shape=ShapeItem(
                                 shape_data["type"],
                                 shape_data["x"], shape_data["y"],
                                 shape_data["w"], shape_data["h"]
                            )
                            if "label" in shape_data:
                                 shape.label = shape_data["label"]
                            if "color" in shape_data:
                                 shape.color = QColor(shape_data["color"])
                            self.main_window.scene.addItem(shape)
                            loaded_shapes.append(shape)
                       except Exception as e:
                            self.logger.error(f"Failed to load shape {i}: {e}")
                  if "connectors" in data:
                       for i, conn_data in enumerate(data["connectors"]):
                            try:
                                 if isinstance(conn_data, list):
                                      start_idx, end_idx = conn_data
                                      conn_type = "line"
                                      metadata = {}
                                 else:
                                      start_idx = conn_data["start"]
                                      end_idx = conn_data["end"]
                                      conn_type = conn_data.get("type", "line")
                                      metadata = conn_data.get("metadata", {})
                                 if 0 <= start_idx < len(loaded_shapes) and 0 <= end_idx < len(loaded_shapes):
                                      conn = ConnectorItem(
                                           loaded_shapes[start_idx],
                                           loaded_shapes[end_idx],
                                           conn_type
                                      )
                                      conn.metada = metadata
                                      self.main_window.scene.addItem(conn)
                                      self.main_window.connectors.append(conn)
                                 else:
                                      self.logger.warning(f"Connector {i} references invalid shape indices")
                            except Exception as e:
                                 self.logger.error(f"Failed to load connector {i}: {e}")
                                 continue
                            self.logger.info(f"Diagram loaded successfully from {path}!")
                            QMessageBox.information(self.main_window, "Success", f"Diagram loaded from {path}!")