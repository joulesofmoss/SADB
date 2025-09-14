from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem,QGraphicsTextItem, QInputDialog, QColorDialog, QMenu
)
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF
from config import HANDLE_SIZE, DEFAULT_SHAPE_COLOR, PENDING_COLOR
from models.connector_item import ConnectorItem
import sys, os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (GRID_SIZE)
from errorLogging import getLogger, safe_execute, erorrHandler

class ConnectionPoint:
    def __init__(self, x, y, direction="auto"):
        self.x = x
        self.y = y
        self.direction = direction

    def get_absolute_pos(self, shape_rect):
        return QPointF(
            shape_rect.x() + self.x * shape_rect.width(),
            shape_rect.y() + self.y * shape_rect.height()
        )

class ShapeItem(QGraphicsItem): #THE CIRCLE GOES IN... THE SQUARE HOLE!
    def __init__(self, item_type, x, y, w, h):
        super().__init__()
        self.logger = getLogger("shape_item")
#        with erorrHandler
        self.selected = False
        self.handle_size = 14
        self.resizing = False
        self.resize_handle = -1
        self.item_type = item_type
        self.w, self.h = w, h
        self.label="" # no default label
        self.color = QColor(Qt.GlobalColor.white)

        self.metadata = {
            'description': '',
            'security_level':'Medium',
            'data_classification': 'Internal',
            'protocols': [],
            'ports': [],
            'trust_level': 'Trusted',
        }
        self.connection_points = self.create_connection_points()
        self.connection_pending = False


        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

        self.text_item = QGraphicsTextItem(self.label, parent=self)
        self.update_text_position()
    
    def create_connection_points(self):
        if self.item_type in ["rect", "process", "datastore", "external", "server", "database"]:
            return [
                ConnectionPoint(0.5, 0, "top"),
                ConnectionPoint(1, 0.5, "right"),
                ConnectionPoint(0.5, 1, "bottom"),
                ConnectionPoint(0, 0.5, "left")
            ]
        elif self.item_type in ["circle", "user"]:
            return [
                ConnectionPoint(0.5, 0.15, "top"),
                ConnectionPoint(0.85, 0.5, "right"),
                ConnectionPoint(0.5, 0.85, "bottom"),
                ConnectionPoint(0.15, 0.5, "left")
            ]
        elif self.item_type in ["diamond", "threat", "decision"]:
            return [
                ConnectionPoint(0.5, 0, "top"),
                ConnectionPoint(1, 0.5, "right"),
                ConnectionPoint(0.5, 1, "bottom"),
                ConnectionPoint(0, 0.5, "left")
            ]
        elif self.item_type in ["hexagon", "network"]:
            return [
                ConnectionPoint(0.75, 0.05, "top"),
                ConnectionPoint(0.95, 0.35, "right"),
                ConnectionPoint(0.95, 0.65, "right"),
                ConnectionPoint(0.76, 0.85, "bottom"),
                ConnectionPoint(0.25, 0.95, "bottom"),
                ConnectionPoint(0.05, 0.35, "left"),
                ConnectionPoint(0.25, 0.05, "top"),
            ]
        elif self.item_type == "arrow":
            return [
                ConnectionPoint(0, 0.5, "left"),
                ConnectionPoint(1, 0.5, "right")
            ]
        elif self.item_type == "star":
            points = []
            for i in range(10):
                angle = i * math.pi/5
                if i % 2 == 0:
                    points.append(ConnectionPoint(
                        0.5 + 0.4 *math.cos(angle - math.pi/2),
                        0.5 + 0.4 * math.sin(angle - math.pi / 2),
                        "auto"
                    ))
            return points
        else:
            return [
                ConnectionPoint(0.5, 0, "top"),
                ConnectionPoint(1, 0.5, "right"),
                ConnectionPoint(0.5, 1, "bottom"),
                ConnectionPoint(0, 0.5, "left")
            ]
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if self.scene().views():
                editor = self.scene().views()[0].parent()
                if getattr(editor, "grid_snapping_enabled", False):
                    grid = GRID_SIZE
                    new_x = round(value.x() / grid) * grid
                    new_y = round(value.y() / grid) * grid
                    return QPointF(new_x, new_y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.selected = value
            self.update()
        if self.scene() and hasattr(self.scene(), 'views') and self.scene().views():
            main_window = self.scene().views()[0].parent()
            if hasattr(main_window, 'connector_manager'):
                main_window.connector_manager.update_connectors_for_shape(self)
        return super().itemChange(change, value)


    def get_best_connection_point(self, target_point):
        rect = self.boundingRect()
        center = rect.center()

        if isinstance(target_point, QPointF):
            target_local = self.mapFromScene(target_point) if self.scene() else target_point
        else:
            target_local = self.mapFromScene(target_point.sceneBoundingRect().center()) if self.scene() else target_point.sceneBoundingRect().center()

        dx = target_local.x() - center.x()
        dy = target_local.y() - center.y()

        if dx == 0 and dy == 0:
            return center
        
        if abs(dx) / rect.width() > abs(dy) / rect.height(): #hori
            x = center.x() + (rect.width() / 2 if dx > 0 else -rect.width() / 2)
            y = center.y() + dy * (rect.width() / 2) / abs(dx)
        else: # verti
            x = center.x() + dx * (rect.height() / 2) / abs(dy)
            y = center.y() + (rect.height() / 2 if dy > 0 else -rect.height() / 2)
        return QPointF(x, y)
    
    def update_path(self):
        if not self.start_shape or not self.end_shape:
            return
        start_point = self.start_shape.get_best_connection_point(self.end_shape.sceneBoundingRect().center())
        end_point = self.end_shape.get_best_connection_point(self.start_shape.sceneBoundingRect().center())

        path = QPainterPath()
        if self.connector_type == "line":
            self.create_straight_line(path, start_point, end_point)
        elif self.connector_type == "elbow":
            self.create_elbow_line(path, start_point, end_point)
        elif self.connector_type == "curved":
            self.create_curved_line(path, start_point, end_point)
        elif self.connector_type == "arrow":
            self.create_arrow_line(path, start_point, end_point)
        self.setPath(path)

    def update_text_position(self):
        if self.text_item:
            text_rect = self.text_item.boundingRect()
            x = (self.w - text_rect.width()) / 2
            y = (self.h - text_rect.height()) / 2
            self.text_item.setPos(x, y)

    def create_diamond(self):
        polygon = QPolygonF()
        polygon.append(QPointF(self.w, self.h/2))
        polygon.append(QPointF(self.w/2, self.h))
        polygon.append(QPointF(0, self.h/2))
        return polygon
    
    def create_triangle(self):
        polygon = QPolygonF()
        polygon.append(QPointF(self.w/2, 0))
        polygon.append(QPointF(self.w, self.h))
        polygon.append(QPointF(0, self.h))
        return polygon

    def create_hexagon(self):
        polygon = QPolygonF()
        center_x, center_y = self.w/2, self.h/2
        radius = min(self.w, self.h) / 2
        for i in range(6):
            angle = i*math.pi / 3
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            polygon.append(QPointF(x, y))
        return polygon
    def create_star(self):
        polygon = QPolygonF()
        center_x, center_y = self.w/2, self.h/2
        outer_radius = min(self.w, self.h) / 2.2
        inner_radius = outer_radius * 0.4

        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            if i % 2 == 0:
                x = center_x + outer_radius * math.cos(angle)
                y = center_y + outer_radius * math.sin(angle)
            else:
                x = center_x + inner_radius * math.cos(angle)
                y = center_y + inner_radius * math.sin(angle)
            polygon.append(QPointF(x, y))
        return polygon
    
    def create_arrow(self):
        polygon = QPolygonF()
        h_third = self.h / 3
        w_80 = self.w * 0.8

        polygon.append(QPointF(0, h_third))
        polygon.append(QPointF(w_80, h_third))
        polygon.append(QPointF(w_80, 0))
        polygon.append(QPointF(self.w, self.h/2))
        polygon.append(QPointF(w_80, self.h))
        polygon.append(QPointF(w_80, 2*h_third))
        polygon.append(QPointF(0, 2*h_third))
        return polygon

    def create_cloud(self):
        path = QPainterPath()
        w, h = self.w, self.h
        path.addEllipse(w*0.2, h*0.3, w*0.3, h*0.4)
        path.addEllipse(w*0.35, h*0.2, w*0.3, h*0.5)
        path.addEllipse(w*0.5, h*0.3, w*0.3, h*0.4)
        path.addEllipse(w*0.25, h*0.45, w*0.5, h*0.3)

        return path
    
    def create_cylinder(self):
        path = QPainterPath()
        ellipse_height = self.h * 0.2
        path.addEllipse(0, 0, self.w, ellipse_height)
        path.addEllipse(0, self.h - ellipse_height, self.w, ellipse_height)
        path.addRect(0, ellipse_height/2, self.w, self.h - ellipse_height)
        return path

    def paint(self, painter, option, widget=None):
        pen_color = Qt.GlobalColor.red if self.connection_pending else Qt.GlobalColor.black
        pen_width = 4 if self.connection_pending else 2
        painter.setPen(QPen(pen_color, pen_width))
        painter.setBrush(QBrush(self.color))
        shape_rect = self.boundingRect()
        if self.item_type == "rect":
            painter.drawRect(shape_rect)
        elif self.item_type == "circle":
            painter.drawEllipse(shape_rect)
        elif self.item_type == "diamond":
            polygon = self.create_diamond()
            painter.drawPolygon(polygon)
        elif self.item_type == "triangle":
            polygon = self.create_triangle()
            painter.drawPolygon(polygon)
        elif self.item_type == "hexagon":
            polygon = self.create_hexagon()
            painter.drawPolygon(polygon)   
        elif self.item_type == "star":
            polygon = self.create_star()
            painter.drawPolygon(polygon)
        elif self.item_type == "arrow":
            polygon = self.create_arrow()
            painter.drawPolygon(polygon)
        elif self.item_type == "cloud":
            path = self.create_cloud()
            painter.drawPath(path)
        elif self.item_type == "cylinder":
            path = self.create_cylinder()
            painter.drawPath(path)
        elif self.item_type == "server":
            painter.drawRect(shape_rect)
        elif self.item_type == "database":
            path = self.create_cylinder() 
            painter.drawPath(path)
        elif self.item_type == "network":
            painter.drawEllipse(shape_rect)
        elif self.item_type == "user":
            painter.drawEllipse(shape_rect) 
        elif self.item_type == "process":
            painter.drawRect(shape_rect)
        elif self.item_type == "datastore":
            path = self.create_cylinder()
            painter.drawPath(path)
        elif self.item_type == "external":
            painter.drawRect(shape_rect)
        elif self.item_type == "threat":
            polygon = self.create_diamond()
            painter.drawPolygon(polygon)
        elif self.item_type == "boundary":
            painter.drawRect(shape_rect)
        elif self.item_type == "decision":
            polygon = self.create_diamond()
            painter.drawPolygon(polygon)
        elif self.item_type == "start_end":
            painter.drawEllipse(shape_rect)
        elif self.item_type == "document":
            painter.drawRect(shape_rect)
        elif self.item_type == "data":
            painter.drawRect(shape_rect)
        elif self.item_type == "manual_input":
            painter.drawRect(shape_rect)
        elif self.item_type == "predefined":
            painter.drawRect(shape_rect)
        if self.label:
            painter.setPen(Qt.GlobalColor.black)
            for i, label in enumerate(self.label):
                painter.drawText(self.boundingRect().adjusted(0, i*20, 0, 0), Qt.AlignmentFlag.AlignTop, self.label)


        if self.isSelected() and hasattr(self, 'show_connection_points') and self.show_connection_points:
            self.draw_connection_points(painter)

        if self.isSelected:
            self.draw_resize_handle(painter)

    def draw_connection_points(self, painter):
        painter.setPen(QPen(Qt.GlobalColor.blue, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.lightGray))

        shape_rect = self.boundingRect()
        for point in self.connection_points:
            abs_pos = point.get_absolute_pos(shape_rect)
            painter.drawEllipse(int(abs_pos.x() - 3), int(abs_pos.y() - 3), 6, 6)


    def contextMenuEvent(self, event):
        menu = QMenu()
        color_action = menu.addAction("Change Color")
        metadata_action = menu.addAction("Edit Properties")
        connection_action = menu.addAction("Show Connection Points")
        action = menu.exec(event.screenPos())

        if action == color_action:
            color = QColorDialog.getColor()
            if color.isValid():
                self.color = color
                self.update()
        elif action == metadata_action:
            self.edit_metadata()
        elif action == connection_action:
            self.show_connection_points = not getattr(self, 'show_connection_points', False)
            self.update()
    def mouseDoubleClickEvent(self, event):
        text, ok = QInputDialog.getText(None, "Edit Label", "Text:", text=self.label)
        if ok:
            self.label = text
            self.update()
    def mouseMoveEvent(self, event): 
        if self.resizing and self.resize_handle != -1:
            self.resize_shape(event.pos())
            self.update()
            return
        if getattr(self, 'move_connected_shapes', False) and hasattr(self, 'scene') and self.scene():
            main_window = self.scene().views()[0].parent()
            if hasattr(main_window, 'connector_manager'):
                connectors = main_window.connector_manager.get_connectors_for_shape(self)
                connected_shapes = set()
                for conn in connectors:
                    other_shape = conn.get_other_shape(self)
                    if other_shape:
                        connected_shapes.add(other_shape)
                old_pos = self.pos()
                super().mouseMoveEvent(event)
                new_pos = self.pos()
                delta = new_pos - old_pos
                for shape in connected_shapes:
                    shape.setPos(shape.pos() + delta)
                return
        super().mouseMoveEvent(event)

    def edit_metadata(self):
        pass # SOON TM

    def is_on_resize_handle(self, pos):
        handle_size = 14
        for i in range(8):
            if self.get_handle_rect(i).contains(pos):
                return True
        return False
    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)
    
    def get_handle_at(self, pos):
        for i in range(8):
            if self.get_handle_rect(i).contains(pos):
                return i
        return -1
    
    def get_handle_rect(self, handle_index):
        handle_size = self.handle_size
        half = handle_size / 2
        rect = self.boundingRect()

        if handle_index == 0:
            return QRectF(rect.left() - half, rect.top() - half, handle_size, handle_size)
        if handle_index == 1:
            return QRectF(rect.right() - half, rect.top() - half, handle_size, handle_size)
        elif handle_index == 2:
            return QRectF(rect.left() - half, rect.bottom() - half, handle_size, handle_size)
        elif handle_index == 3:
            return QRectF(rect.right() - half, rect.bottom() - half, handle_size, handle_size)
        elif handle_index == 4:
            return QRectF(rect.center().x() - half, rect.top() - half, handle_size, handle_size)
        elif handle_index == 5:
            return QRectF(rect.center().x() - half, rect.bottom() - half, handle_size, handle_size)
        elif handle_index == 6:
            return QRectF(rect.left() - half, rect.center().y() - half, handle_size, handle_size)
        elif handle_index == 7:
            return QRectF(rect.right() - half, rect.center().y() - half, handle_size, handle_size)

    def draw_resize_handle(self, painter):
       if not self.isSelected():
           return
       painter.setPen(QPen(Qt.GlobalColor.blue, 1))
       painter.setBrush(QBrush(Qt.GlobalColor.white))
       
       h_size = self.handle_size
       rect = self.boundingRect()

       handles = [
        QRectF(rect.left() - h_size/2, rect.top() - h_size/2, h_size, h_size),
        QRectF(rect.right() - h_size/2, rect.top() - h_size/2, h_size, h_size),
        QRectF(rect.left() - h_size/2, rect.bottom() - h_size/2, h_size, h_size),
        QRectF(rect.right() - h_size/2, rect.bottom() - h_size/2, h_size, h_size),
        # Side handles
        QRectF(rect.center().x() - h_size/2, rect.top() - h_size/2, h_size, h_size),
        QRectF(rect.center().x() - h_size/2, rect.bottom() - h_size/2, h_size, h_size),
        QRectF(rect.left() - h_size/2, rect.center().y() - h_size/2, h_size, h_size),
        QRectF(rect.right() - h_size/2, rect.center().y() - h_size/2, h_size, h_size),
       ]
       for handle in handles:
           painter.drawRect(handle)

    def get_handle_positions(self):
        h_size = self.handle_size
        rect = self.boundingRect()
        handles = []

        handles.append(QRectF(-h_size/2, -h_size/2, h_size, h_size))
        handles.append(QRectF(self.w - h_size/2, -h_size/2, h_size, h_size))
        handles.append(QRectF(-h_size/2, self.h - h_size/2, h_size, h_size))
        handles.append(QRectF(self.w - h_size/2, self.h - h_size/2, h_size, h_size)) # THIS SHIT HURTS MY HANDS
        handles.append(QRectF(self.w/2 - h_size/2, -h_size/2, h_size, h_size)) #hopefully this stuff should make side panels please just work amen
        handles.append(QRectF(self.w/2 - h_size/2, self.h - h_size, h_size, h_size))
        handles.append(QRectF(-h_size/2, self.h/2 - h_size/2, h_size, h_size))
        handles.append(QRectF(self.w - h_size /2,self.h/2 - h_size/2, h_size, h_size))
        return handles #handle this
    def get_handle_at_pos(self, pos): #this doesnt have to be 2 classes i bet why did i make this two class
        if not self.selected:
            return -1
        handles = self.get_handle_positions()
        for i, handle_rect in enumerate(handles):
            if handle_rect.contains(pos):
                return i
        return -1
    def mousePressEvent(self, event):
        if self.scene() and self.scene().views():
            main_window = self.scene().views()[0].parent()
            if self.is_on_resize_handle(event.pos()):
                self.resizing = True
                self.resize_handle = self.get_handle_at(event.pos())
                self.resize_start_pos = event.pos()
                self.resize_orig_pos = self.pos()
                self.resize_orig_w = self.w
                self.resize_orig_h = self.h
                event.accept()
                return            
            if hasattr(main_window, 'current_tool') and main_window.current_tool == "connector":
                print("Shape clicked in connector mode!")
                if main_window.pending_connector is None:
                    print("Setting as first connector!")
                    main_window.pending_connector = self
                    self.set_connection_pending(True)
                else:
                    print("Making connection")
                    main_window.pending_connector.set_connection_pending(False)
                    if hasattr(main_window, 'connector_manager'):
                        conn = main_window.connector_manager.create_connector(main_window.pending_connector, self)
                        main_window.connectors.append(conn)
                    main_window.pending_connector = None
                    if hasattr(main_window, 'set_tool'):
                        main_window.set_tool("select")
                    if hasattr(main_window, 'toolbar_manager'):
                        main_window.toolbar_manager.set_tool("select")
                return
        if self.scene():
            for item in self.scene().items():
                if isinstance(item, ShapeItem) and item != self:
                    item.setSelected(False)
        
        if event.button() == Qt.MouseButton.LeftButton:
            modifiers = event.modifiers()
            if modifiers and Qt.KeyboardModifier.ControlModifier:
                self.move_connected_shapes = True
            else:
                self.move_connected_shapes = False
        super().mousePressEvent(event)
    

    def set_connection_pending(self, pending):
        self.connection_pending = pending
        self.update()
    
    def resize_shape(self, pos):
        min_size = 20
        delta_x = pos.x() - self.resize_start_pos.x()
        delta_y = pos.y() - self.resize_start_pos.y()

        self.prepareGeometryChange()

        new_x = self.resize_orig_pos.x()
        new_y = self.resize_orig_pos.y()
        new_w = self.resize_orig_w
        new_h = self.resize_orig_h

        if self.resize_handle == 0:
            new_w = max(min_size,self.resize_orig_w - delta_x)
            new_h = max(min_size, self.resize_orig_h - delta_y)
            if new_w > min_size:
                new_x = self.resize_orig_pos.x() + (self.resize_orig_w - new_w)
            if new_h > min_size:
                new_y = self.resize_orig_pos.y() + (self.resize_orig_h - new_h)
        elif self.resize_handle == 1:
                new_w = max(min_size, self.resize_orig_w + delta_x)
                new_h = max(min_size, self.resize_orig_h - delta_y)
                if new_h > min_size:
                    new_y = self.resize_orig_pos.y() + (self.resize_orig_h - new_h)
        elif self.resize_handle == 2:
                new_w = max(min_size, self.resize_orig_w - delta_x)
                new_h = max(min_size, self.resize_orig_h + delta_y)
                if new_w > min_size:
                    new_x = self.resize_orig_pos.x() + (self.resize_orig_w - new_w)
        elif self.resize_handle == 3:
                new_w = max(min_size, self.resize_orig_w + delta_x)
                new_h = max(min_size, self.resize_orig_h + delta_y)
        elif self.resize_handle == 4:
                new_h = max(min_size, self.resize_orig_h - delta_y)
                if new_h > min_size:
                    new_y = self.resize_orig_pos.y() + (self.resize_orig_h - new_h)
        elif self.resize_handle ==5:
                    new_h = max(min_size, self.resize_orig_h + delta_y)
        elif self.resize_handle == 6:
                    new_w = max(min_size, self.resize_orig_w - delta_x)
                    if new_w > min_size:
                        new_x = self.resize_orig_pos.x() + (self.resize_orig_w - new_w)
        elif self.resize_handle == 7:
                    new_w = max(min_size, self.resize_orig_w + delta_x)
        self.w = new_w
        self.h = new_h
        self.setPos(new_x, new_y)
        self.update_text_position()
        self.update()
        if self.scene() and hasattr(self.scene(), 'views') and self.scene().views():
            main_window = self.scene().views()[0].parent()
            if hasattr(main_window, 'connector_manager'):
                main_window.connector_manager.update_connectors_for_shape(self)     

             #please work
    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            self.resize_handle = -1
        self.move_connected_shapes = False
        return super().mouseReleaseEvent(event)
    def prepareGemoetryChange(self):
        super().prepareGeometryChange()
        if self.scene():
            self.scene().invalidate(self.sceneBoundingRect().adjusted(-10, -10, 10, 10))