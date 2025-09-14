from PyQt6.QtWidgets import (QMainWindow, QGraphicsView, QGraphicsScene, QDockWidget, QInputDialog, QSplitter, QFileDialog, QMessageBox)
from PyQt6.QtGui import QBrush, QColor, QPixmap, QPainter, QPen
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtSvg import QSvgGenerator
from metadata import MetadataPanel
from models.threat_model import create_threat_model_from_shapes, quick_threat_analysis
import math

from models.shape_item import ShapeItem
from models.connector_item import ConnectorItem, ConnectorManager
from ui.toolbar import ToolbarManager
from utils.file_manager import FileManager
from config import (BACKGROUND_COLOR, GRID_COLOR, GRID_SIZE, DEFAULT_SHAPE_WIDTH, DEFAULT_CIRCLE_SIZE, DEFAULT_SHAPE_HEIGHT
)
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DiagramEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene()
        #coordinates
        self.scene_width = 2000
        self.scene_height = 1500 
        self.scene.setSceneRect(-self.scene_width//2, -self.scene_height//2, self.scene_width, self.scene_height)        
        self.view = QGraphicsView(self.scene)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.toolbar_manager = ToolbarManager(self)
        self.file_manager = FileManager(self)
        self.connector_manager = ConnectorManager(self.scene)
        self.grid_snapping_enabled = False
        self.shapes = []
        self.connectors = []
        self.current_tool = "select"
        self.pending_connector = None
        self.grid_enabled = True
        self.selected_shape = None
        self.resizing = False
        self.setup_ui()
        self.setup_connections()


    def setup_ui(self):
        self.setWindowTitle("Threat Modeling Diagram App")
        self.resize(1000, 800)
        self.setCentralWidget(self.view)
        self.setup_background()
        self.toolbar_manager.create_toolbar()
        self.setup_top_toolbar()
        self.setup_metadata_panel()

    def setup_main_layout(self):
       from ui.shape_palette import ShapePalette
       main_splitter = QSplitter(Qt.Orientation.Horizontal)
       self.shape_pallete = ShapePalette()
       self.shape_palette.shape_selected.connect(self.on_shape_selected)
       self.shape_palette.setMinimumWidth(200)
       self.shape_palette.setMaximumWidth(300)
       main_splitter.addWidget(self.shape_palette)
       main_splitter.addWidget(self.view)
       main_splitter.setSizes([200, 800])
       main_splitter.setStretchFactor(0, 0)
       main_splitter.setStretchFactor(1, 1)
       self.setCentralWidget(main_splitter)
    
    def on_shape_selected(self, category, shape_type):
        print(f"Shape selected: {shape_type} from {category}")
        self.current_category = category
        self.set_tool(shape_type)

        if hasattr(self, 'toolbar_manager'):
            self.toolbar_manager.set_tool(shape_type)


    def setup_background(self):
        self.view.setBackgroundBrush(QBrush(BACKGROUND_COLOR))
        self.draw_grid_background()
    
    def setup_top_toolbar(self):
        top_toolbar = self.addToolBar("Main Actions")
        top_toolbar.setMovable(True)
        save_action = top_toolbar.addAction("💾 Save")
        save_action.triggered.connect(self.file_manager.save_diagram)
        load_action = top_toolbar.addAction("📁 Load")
        load_action.triggered.connect(self.file_manager.load_diagram)
        export_action = top_toolbar.addAction("📤 Export")
        export_action.triggered.connect(self.export_diagram)
        grid_action = top_toolbar.addAction("🌐 Grid")
        grid_action.triggered.connect(self.toggle_grid)
        snap_action = top_toolbar.addAction("🫰 Snap")
        snap_action.triggered.connect(self.toggle_grid_snapping)
        props_action = top_toolbar.addAction("🤔 Properties")
        props_action.triggered.connect(self.toolbar_manager.toggle_properties_panel)

    def setup_metadata_panel(self):
        self.meta_panel = MetadataPanel(self)
        self.meta_panel.metadata_changed.connect(self.on_metadata_changed)
        dock = QDockWidget("Shape Properties", self)
        dock.setWidget(self.meta_panel)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        dock.setMinimumHeight(400)
        dock.setMaximumHeight(800)
        dock.setMinimumWidth(350)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.properties_dock = dock
        dock.setVisible(False)

    def setup_connections(self):
        self.scene.selectionChanged.connect(self.on_selection_changed)
    
    def draw_grid_background(self):
        if self.grid_enabled:
            pixmap = QPixmap(GRID_SIZE, GRID_SIZE)
            pixmap.fill(BACKGROUND_COLOR)
            painter = QPainter(pixmap)
            pen = QPen(GRID_COLOR, 1)
            painter.setPen(pen)
            painter.drawLine(0, 0, GRID_SIZE, 0)
            painter.drawLine(0, 0, 0, GRID_SIZE)
            painter.end()
            self.view.setBackgroundBrush(QBrush(pixmap))
        else:
            self.view.setBackgroundBrush(QBrush(BACKGROUND_COLOR))
    
    def toggle_grid(self):
        self.grid_enabled = not self.grid_enabled
        self.draw_grid_background()

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        self.pending_connector = None
        print(f"Tool switched to: {tool_name}!")

    #metadata shtuff
    def on_selection_changed(self):
        selected_items = self.scene.selectedItems()
        if selected_items and isinstance(selected_items[0], ShapeItem):
            print(f"Shape selected: {selected_items[0]}")
            self.update_metadata(selected_items[0])
        else:
            print("No shape selected!")
            self.update_metadata(None)

    def clear_metadata_panel(self):
        if hasattr(self, 'meta_panel') and self.meta_panel:
            self.meta_panel.clear_all()

    def update_metadata(self, shape):
        print(f"update_metadata called with: {shape}")
        self.selected_shape = shape
        if not shape:
            self.clear_metadata_panel()
            return
        
        shape_metadata = getattr(shape, 'metadata', {})
        if hasattr(self, 'meta_panel') and self.meta_panel:
            self.meta_panel.set_metadata(shape_metadata)
            
            if not shape_metadata.get('basic', {}).get('id'):
                import uuid
                if not hasattr(shape, 'metadata'):
                    shape.metadata = {}
                if 'basic' not in shape.metadata:
                    shape.metadata['basic'] = {}
                shape.metadata['basic']['id'] = str(uuid.uuid4())[:8]
                self.meta_panel.id_edit.setText(shape.metadata['basic']['id'])
            
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not shape_metadata.get('basic', {}).get('created'):
                if not hasattr(shape, 'metadata'):
                    shape.metadata = {}
                if 'basic' not in shape.metadata:
                    shape.metadata['basic'] = {}
                shape.metadata['basic']['created'] = current_time
                self.meta_panel.created_date_edit.setText(current_time)
            
            if not hasattr(shape, 'metadata'):
                shape.metadata = {}
            if 'basic' not in shape.metadata:
                shape.metadata['basic'] = {}
            shape.metadata['basic']['modified'] = current_time
            self.meta_panel.modified_date_edit.setText(current_time)

    def on_metadata_changed(self, metadata):
        if hasattr(self, 'selected_shape') and self.selected_shape:
            if not hasattr(self.selected_shape, 'metadata'):
                self.selected_shape.metadata = {}
            self.selected_shape.metadata.update(metadata)
            print(f"Updated metadata for shape: {self.selected_shape}")


    def set_shape_label(self, text):
        if self.selected_shape:
            self.selected_shape.label = text
            self.selected_shape.update()
    
    def set_shape_description(self, text):
        if self.selected_shape:
            self.selected_shape.description = text
    


    #Mouse event stuff
    def mousePressEvent(self, event):
        print(f"Mouse pressed! Current tool: {self.current_tool}")
        if event.button() == Qt.MouseButton.LeftButton:
            view_pos = self.view.mapFromParent(event.pos())
            pos = self.view.mapToScene(view_pos)
            if self.grid_snapping_enabled:
                pos = self.snap_to_grid(pos)
            item = self.scene.itemAt(pos, self.view.transform())
            print(f"Raw item at position: {item}")
            all_items = self.scene.items(pos)
            print(f"All items at position: {all_items}")

            if hasattr(item, 'parentItem') and item.parentItem():
                item = item.parentItem()
                print(f"Using parent item instead: {item}")
            
            threat_modeling_shapes = {
                "user": ("circle", 80,80, QColor(135, 206, 250)),
                "process": ("rect", 100, 60, QColor(144, 238, 144)),
                "datastore": ("rect", 120, 40, QColor(255, 182, 193)),
                "external": ("rect", 90, 70, QColor(255, 255, 224)),
                "threat": ("diamond", 80, 80, QColor(255, 99, 71)),
                "boundary": ("rect", 150, 100, QColor(211, 211, 211)),
                "decision": ("diamond", 70, 70, QColor(255, 215, 0)),
                "decision": ("diamond", 70, 70, QColor(255, 215, 0)),  # Fix typo
                "network": ("hexagon", 90, 90, QColor(175, 238, 238)),
                "server": ("rect", 90, 70, QColor(152, 251, 152)),
                "database": ("rect", 100, 60, QColor(255, 182, 193)),
            }

            if self.current_tool in threat_modeling_shapes:
                shape_type, width, height, color = threat_modeling_shapes[self.current_tool]
                shape = ShapeItem(shape_type, pos.x() - width//2, pos.y() - height//2, width, height)
                shape.color = color
                shape.shape_category = getattr(self, 'current category', 'threat_modeling')
                shape.shape_subtype = self.current_tool
                # No automatic label
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
                # 
            elif self.current_tool == "rect":
                shape = ShapeItem("rect", pos.x() - 50, pos.y() - 30, 100, 60)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "circle":
                shape = ShapeItem("circle", pos.x() - 30, pos.y() - 30, 60, 60)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "diamond":
                shape = ShapeItem("diamond", pos.x() - 40, pos.y() - 40, 80, 80)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "hexagon":
                shape = ShapeItem("hexagon", pos.x() - 45, pos.y() - 45, 90, 90)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "triangle":
                shape = ShapeItem("triangle", pos.x() - 40, pos.y() - 40, 80, 80)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "star":
                shape = ShapeItem("star", pos.x() - 45, pos.y() - 45, 90, 90)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "arrow":
                shape = ShapeItem("arrow", pos.x() - 50, pos.y() - 30, 100, 60)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "cloud":
                shape = ShapeItem("cloud", pos.x() - 60, pos.y() - 40, 120, 80)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "cylinder":
                shape = ShapeItem("cylinder", pos.x() - 50, pos.y() - 40, 100, 80)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            # Flow et UML shapes
            elif self.current_tool == "start_end":
                shape = ShapeItem("start_end", pos.x() - 40, pos.y() - 25, 80, 50)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "document":
                shape = ShapeItem("document", pos.x() - 50, pos.y() - 35, 100, 70)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "data":
                shape = ShapeItem("data", pos.x() - 45, pos.y() - 30, 90, 60)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "manual_input":
                shape = ShapeItem("manual_input", pos.x() - 50, pos.y() - 30, 100, 60)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "predefined":
                shape = ShapeItem("predefined", pos.x() - 55, pos.y() - 30, 110, 60)
                self.scene.addItem(shape)
                self.shapes.append(shape)
                self.update_metadata(shape)
            elif self.current_tool == "connector":
                print(f"In connector mode, item clicked: {item}, type: {type(item)}")
                if isinstance(item, ShapeItem):
                    if self.pending_connector is None:
                        self.pending_connector = item
                        item.set_connection_pending(True)
                    else:
                        conn = self.connector_manager.create_connector(self.pending_connector, item)
                        self.connecters_append(conn)
                        self.pending_connector.set_connection_pending(False)
                        self.scene.addItem(conn)
                        self.pending_connector = None
                        self.set_tool("select")
                        if hasattr(self, 'toolbar_manager'):
                            self.toolbar_manager.set_tool("select")
            elif self.current_tool == "select":
            #    print(f"In select mode, clicked on: {item}")
                self.scene.clearSelection()

                if item is not None and isinstance(item,ShapeItem):
                    item.setSelected(True)
                    self.update_metadata(item)
                else:
                    self.update_metadata(None)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event): # press t to make a label, press other buttons to do other shit
        if event.key() == Qt.Key.Key_T:
            items = self.scene.selectedItems()
            if items:
                shape = items[0]
                text, ok = QInputDialog.getText(self, "Enter Label", "Label:")
                if ok and text:
                    shape.label = text
                    shape.update()
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene.selectedItems():
                self.scene.removeItem(item)
                if isinstance(item, ShapeItem):
                    self.shapes.remove(item)
                elif isinstance(item, ConnectorItem):
                    self.connectors.remove(item)
        super().keyPressEvent(event)
    def export_diagram(self):
        file_path, file_filter = QFileDialog.getSaveFileName(
            self, "Export Diagram", "threat_model", "PNG Image (*.png);SVG Vector (*.svg);PDF Document (*.pdf);JPEG Image (*.jpg)"
        )
        if file_path:
            try:
                file_ext = file_path.split('.') [-1].lower()
                if file_ext == 'png':
                    self.export_to_png(file_path)
                elif file_ext == 'jpg' or file_ext == 'jpeg':
                    self.export_to_jpg(file_path)
                elif file_ext == 'svg':
                    self.export_to_svg(file_path)
                elif file_ext == 'pdf':
                    self.export_to_pdf(file_path)
                else:
                    QMessageBox.warning(self, "Error!", "This file format is not supported!")
                    return
                QMessageBox.information(self, "Export finished!", f"Diagram exported to {file_path}!")
            except Exception as e:
                QMessageBox.critical(self, "Error!!", f"Failed to export diagam:\n{str(e)}!!!")
    
    def export_to_png(self, file_path):
        scene_rect = self.scene.itemsBoundingRect()
        padding = 20
        export_rect = scene_rect.adjusted(-padding, -padding, padding, padding)
        pixmap = QPixmap(int(export_rect.width()), int(export_rect.height()))
        pixmap.fill()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, QRectF(), export_rect)
        painter.end()
        pixmap.save(file_path, "PNG")

    def export_to_jpg(self, file_path):
        scene_rect = self.scene.itemsBoundingRect()
        padding = 20
        export_rect = scene_rect.adjusted(-padding, -padding, padding, padding)
        pixmap = QPixmap(int(export_rect.width()), int(export_rect.height()))
        pixmap.fill()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, QRectF(), export_rect)
        painter.end()
        pixmap.save(file_path, "JPG")
    

    def export_to_svg(self, file_path):
        scene_rect = self.scene.itemsBoundingRect()
        padding = 20
        export_rect = scene_rect.adjusted(-padding, -padding, padding, padding)
        svg_gen = QSvgGenerator()
        svg_gen.setFileName(file_path)
        svg_gen.setSize(export_rect.size().toSize())
        svg_gen.setViewBox(QRectF(0, 0, export_rect.width(), export_rect.height()))
        svg_gen = QSvgGenerator()
        painter = QPainter(svg_gen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, QRectF(), export_rect)
        painter.end()


    def export_to_pdf(self, file_path):
        scene_rect = self.scene.itemsBoundingRect()
        padding = 20
        export_rect = scene_rect.adjusted(-padding, -padding, padding, padding)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPrinter.PageSize.A4)
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter)
        painter.end()
    
    def run_threat_analysis(self):
        threats, summary = quick_threat_analysis(self.shapes, self.connectors)
        self.threats_panel.update_threats(threats)
        return threats    
    def toggle_grid_snapping(self):
        self.grid_snapping_enabled = not self.grid_snapping_enabled
        print(f"Grid snapping {'enabled' if self.grid_snapping_enabled else 'disabled'}")

    def snap_to_grid(self, pos):
        if self.grid_snapping_enabled:
            grid_x = round(pos.x() / GRID_SIZE) * GRID_SIZE
            grid_y = round(pos.y() / GRID_SIZE) * GRID_SIZE
            return QPointF(grid_x, grid_y)
        return pos
    