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
    @gui_safe_execute
    def save_diagram(self, *args, **kwargs): # savin'
        self.logger.info("Starting diagram savin!")
        path, _ = QFileDialog.getSaveFileName(self.main_window, "Save Diagram", SAVE_DIR, "JSON Files (*.json)")
        if not path:
            self.logger.info("Cancelled!")
            return
        try:
            validate_file_path(path, "write")
        except Exception as e:
             self.logger.error(f"Invalid save path: {e}")
             QMessageBox.warning(self.main_window, "Invalid Path", str(e))
             return
        
        with FileOperationHandler("save diagram", path):
             with PerformanceMonitor("diagram serialization", self.logger):
                  data = {
                       "shapes": [],
                       "connectors": [],
                       "metadata": {
                            "version": "1.0",
                            "created_at": str(datetime.now()),
                            "shape_count": len(self.main_window.shapes),
                            "connectors_count": len(getattr(self.main_window, 'connectors', []))
                       }
                  }

                  for i, shape in enumerate(self.main_window.shapes):
                       try:
                            rect = shape.sceneBoundingRect()
                            shape_data = {
                                 "type": getattr(shape, 'item_type', 'rect'),
                                 "x": rect.x(),
                                 "y": rect.y(),
                                 "width":rect.width() ,
                                 "height": rect.height(),
                                 "label": getattr(shape,'label', ''),
                                 "colour": shape.colour.name() if hasattr(shape, 'color') else '#ffffff',
                                 "metadata": getattr(shape, 'metadata', {}),
                                 "shape_category": getattr(shape, 'shape_category', ''),
                                 "shape_subtype": getattr(shape, 'shape_subtype', ''),
                            }
                            data["shapes"].append(shape_data)
                            self.logger.debug(f"Serialized shape {i}: {shape_data['type']}")
                       except Exception as e:
                            self.logger.error(f"Failed to serialize shape {i}: {e}")
                            continue
                  connectors = getattr(self.main_window, 'connectors', []) # something something cereal
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
    @gui_safe_execute
    def load_diagram(self, *args, **kwargs): #loadin'
        self.logger.info("Starting to load!")
        path, _=QFileDialog.getOpenFileName(
             self.main_window, "Load Diagram", SAVE_DIR, "JSON Files (*.json)"
        )
        if not path:
             self.logger.info("Load operation cancelled by user")
             return
        with FileOperationHandler("load diagram", path):
             try:
                  validate_file_path(path, "read")
             except Exception as e:
                  self.logger.error(f"Cannot read file: {e}")
                  return
             with PerformanceMonitor("diagram loading", self.logger):
                  with erorrHandler("clearing existing diagram", self.logger):
                       self.main_window.scene.clear()
                       self.main_window.shapes.clear()
                       if hasattr(self.main_window, 'connectors'):
                            self.main_window.connectors.clear()
                    
                  try:
                       with open(path, 'r', encoding='utf-8') as f:
                         data=json.load(f)
                  except json.JSONDecodeError as e:
                       raise ValueError(f"Invalid JSON file: {e}")
                  if not isinstance(data, dict):
                       raise ValueError("Invalid file format: not a JSON object")

                  if "shapes" not in data:
                       raise ValueError ("Invalid file format: missing 'shapes' key")
                  loaded_shapes = []
                  for i, shape_data in enumerate(data["shapes"]):
                       try: 
                            width=shape_data.get("width", shape_data.get("w", 100))
                            height=shape_data.get("height", shape_data.get("h", 60))
                            shape=ShapeItem(
                                 shape_data.get("type", "rect"),
                                 shape_data["x"], shape_data["y"],
                                 width, height
                            )
                            if "label" in shape_data:
                                 shape.label = shape_data["label"]
                            if "color" in shape_data:
                                 shape.color = QColor(shape_data["color"])
                            if "metadata" in shape_data:
                                 shape.metadata = shape_data["metadata"]
                            if "shape_category" in shape_data:
                                 shape.shape_category = shape_data["shape_category"]
                            if "shape_subtype" in shape_data:
                                 shape.shape_subtype = shape_data["shape_subtype"]
                            self.main_window.scene.addItem(shape)
                            loaded_shapes.append(shape)
                            self.logger.debug(f"Loaded shape {i}: {shape_data.get('type', 'rect')}")
                       except Exception as e:
                            self.logger.error(f"Failed to load shape {i}: {e}")
                            continue
                  self.main_window.shapes = loaded_shapes
                  if "connectors" in data:
                       loaded_connectors = []
                       for i, conn_data in enumerate(data["connectors"]):
                            try:
                                 if isinstance(conn_data, list) and len(conn_data) >=2:
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
                                      conn.metadata = metadata
                                      self.main_window.scene.addItem(conn)
                                      loaded_connectors.append(conn)
                                      self.logger.debug(f"Loaded connector {i}")
                                 else:
                                      self.logger.warning(f"Connector {i} references invalid shape indices: {start_idx}, {end_idx}")
                            except Exception as e:
                                 self.logger.error(f"Failed to load connector {i}: {e}")
                                 continue
                            if not hasattr(self.main_window, 'connectors'):
                                 self.main_window.connectors = []
                            self.main_window.connectors = loaded_connectors

                            if loaded_shapes and hasattr(self.main_window, 'update_metadata'):
                                 self.main_window.update_metadata(None)
                            self.logger.info(f"Diagram loaded successfully from {path}!")
                            shapes_count = len(data.get("connectors", []))
                            connectors_count = len(data.get("connectors", []))
                            QMessageBox.information(
                                 self.main_window,
                                 "Success",
                                 f"Diagram loaded from {os.path.basename(path)}\n"
                                 f"Loaded {shapes_count} shapes and {connectors_count} connectors"
                            )
    def export_metadata_report(self, file_path):
          with FileOperationHandler("export metadata report", file_path):
               report_data = {
                    "diagram_info": {
                         "total_shapes": len(self.main_window.shapes),
                         "total_connectors": len(getattr(self.main_window, 'connectors', [])),
                         "generated_at": str(datetime.now()),
               },
               "shapes": []
          }
               for i, shape in enumerate(self.main_window.shapes):
                    shape_report = {
                         "id": i,
                         "type": getattr(shape, 'item_type', 'unknown'),
                         "label": getattr(shape, 'label', ''),
                         "position": {
                              "x": shape.sceneBoundingRect().x(),
                              "y": shape.sceneBoundingRect().y(),
                         },
                         "metadata": getattr(shape, 'metadata', {})
                    }
                    report_data["shapes"].append(shape_report)
               with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
               self.logger.info(f"Metadata report exported to {file_path}")