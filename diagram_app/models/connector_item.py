from PyQt6.QtWidgets import QGraphicsItem,QGraphicsPathItem, QInputDialog
from PyQt6.QtGui import QPen, QPainter, QPolygonF, QColor, QPainterPath
from PyQt6.QtCore import Qt, QPointF
from config import CONNECTOR_COLOR
import math

class ConnectorItem(QGraphicsPathItem): #friendship with supergluing has ended, copying drawio bar for bar and just being worse is new best friend
    def __init__(self, start, end, connectorType="line"):
        super().__init__()
        self.start_shape = start
        self.end_shape=end
        self.connector_type = connectorType

        self.metadata = {
            'label': '',
            'data_flow': 'Bidirectional',
            'protocol': '',
            'encrypted': False,
            'authenticated': False,
            'data_type': '',
            'frequency': 'As needed'
        }

        self.line_width = 2
        self.line_color = QColor(Qt.GlobalColor.white)
        self.selected_color = QColor(Qt.GlobalColor.blue)

        self.setPen(QPen(self.line_color, self.line_width))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | 
            QGraphicsItem.GraphicsItemFlag.ItemIsFocusable # LINE BREAK, W
        )
        self.update_path()

    def update_path(self):
        if not self.start_shape or not self.end_shape:
            return

        start_center = self.start_shape.sceneBoundingRect().center()
        end_center = self.end_shape.sceneBoundingRect().center()
        start_point = self.get_connection_point(self.start_shape, self.end_shape)
        end_point = self.get_connection_point(self.end_shape, self.start_shape)
        start_scene = self.start_shape.mapToScene(start_point)
        end_scene = self.end_shape.mapToScene(end_point)
        start_local = self.mapFromScene(start_scene)
        end_local = self.mapFromScene(end_scene)

  

        path = QPainterPath()

        if self.connector_type == "line":
            self.create_straight_line(path, start_local, end_local)
        elif self.connector_type == "elbow":
            self.create_elbow_line(path, start_local, end_local)
        elif self.connector_type == "curved":
            self.create_curved_line(path, start_local, end_local)
        elif self.connector_type == "arrow":
            self.create_arrow_line(path, start_local, end_local)

        self.setPath(path)

    def get_connection_point(self, shape, target_center):

        if hasattr(shape, 'get_best_connection_point'):
            return shape.get_best_connection_point(target_center)
        else:
            return shape.boundingRect().center()
    def create_straight_line(self, path, start, end):
        path.moveTo(start)
        path.lineTo(end)

    def create_elbow_line(self,path,start,end):
        path.moveTo(start)

        dx=abs(end.x() - start.x())
        dy = abs(end.y() - start.y())

        if dx > dy: # horri
            mid_point = QPointF(end.x(), start.y())
        else: #verti
            mid_point = QPointF(start.x(), end.y())
        
        path.lineTo(mid_point)
        path.lineTo(end)

    def create_curved_line(self,path,start,end):
        path.moveTo(start)

        distance = ((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2) **0.5
        curve_factor = min(distance*0.3, 50)

        dx = end.x() - start.x()
        dy = end.y() - start.y()

        length = (dx ** 2 + dy ** 2) ** 0.5
        if length > 0:
            perp_x = -dy / length * curve_factor
            perp_y = dx / length * curve_factor
        else:
            perp_x = perp_y = 0
        
        mid_x = (start.x() + end.x()) / 2
        mid_y = (start.y() + end.y()) / 2

        control1 = QPointF(mid_x + perp_x, mid_y + perp_y)
        control2 = QPointF(mid_x + perp_x, mid_y + perp_y)

        path.cubicTo(control1, control2, end)
    
    def create_arrow_line(self,path,start,end):
        path.moveTo(start)
        path.lineTo(end)

        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrowhead_length = 15
        arrowhead_angle = math.pi / 6

        arrow_point1 = QPointF(
            end.x() - arrowhead_length * math.cos(angle - arrowhead_angle),
            end.y() - arrowhead_length * math.sin(angle - arrowhead_angle)
        )
        arrow_point2 = QPointF(
            end.x() - arrowhead_length * math.cos(angle + arrowhead_angle),
            end.y() - arrowhead_length * math.sin(angle + arrowhead_angle)
        )

        path.moveTo(end)
        path.lineTo(arrow_point1)
        path.moveTo(end)
        path.lineTo(arrow_point2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.isSelected():
            pen = QPen(self.selected_color, self.line_width + 1)
        else:
            pen = QPen(self.line_color, self.line_width)
        
        painter.setPen(pen)
        painter.drawPath(self.path())

        if self.metadata.get('label'):
            self.draw_label(painter)
        
        self.draw_data_flow_indicator(painter)

    def draw_label(self, painter):
        path = self.path()
        if path.length() > 0:
            midPoint = path.pointAtPercent(0.5)
            painter.setPen(QPen(Qt.GlobalColor.black))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            text = self.metadata['label']
            text_rect = painter.fontMetrics().boundingRect(text)
            text_rect.moveCenter(midPoint.toPoint())
            painter.fillRect(text_rect.adjusted(-2, -1, 2, 1), Qt.GlobalColor.white)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
    
    def draw_data_flow_indicator(self, painter):
        data_flow = self.metadata.get('data_flow', 'Bidirectional')
        path = self.path()
        if path.length() < 40:
            return # sub-40ers stay big buddy

        painter.setPen(QPen(self.line_color, 1))
        painter.setBrush(self.line_color)
        arrow_size = 8

        if data_flow in ("Forward", "Bidirectional"):
            point = path.pointAtPercent(0.75)
            angle = -math.radians(path.angleAtPercent(0.75))
            self.draw_small_arrow(painter, point, angle, arrow_size)
        
        if data_flow in ("Backward", "Bidirectional"):
            point = path.pointAtPercent(0.25)
            angle = -math.radians(path.angleAtPercent(0.25))
            self.draw_small_arrow(painter, point, angle, arrow_size)

    def draw_small_arrow(self, painter, point, angle, size):
            arrow_angle = math.pi / 6

            p1 = QPointF(
                point.x() + size * math.cos(angle - arrow_angle),
                point.y() + size * math.sin(angle - arrow_angle)
            )
            p2 = QPointF(
                point.x() + size * math.cos(angle + arrow_angle),
                point.y() + size * math.sin(angle + arrow_angle)
            )
            arrow = QPolygonF([point, p1, p2])
            painter.drawPolygon(arrow)

    def edit_properties(self):
            text, ok = QInputDialog.getText(
                None, "Connector Properties", "Label:", text=self.metadata.get('label', '')
            )
            if ok:
                self.metadata['label'] = text
                self.update()
        
    def mouseDoubleClickEvent(self, event):
            self.edit_properties()

    def context_menu_event(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()

        type_menu = menu.addMenu("Connector Type")
        type_actions = {
            "Straight Line": "line",
            "Elbow": "elbow",
            "Curved": "curved",
            "Arrow": "arrow"
        }

        for name, conn_type in type_actions.items():
            action = type_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(self.connector_type == conn_type)
            action.triggered.connect(lambda checked, t=conn_type: self.set_connector_type(t))
        menu.addSeparator()

        flow_menu = menu.addMenu("Data Flow")
        flow_actions = ["Forward", "Backward", "Bidirectional", "None"]

        

        for flow in flow_actions:
            action = flow_menu.addAction(flow)
            action.setCheckable(True)
            action.setChecked(self.metadata.get('data_flow') == flow)
            action.triggered.connect(lambda checked, f=flow: self.set_data_flow(f))
        menu.addSeparator()

        props_action = menu.addAction("Edit Properties")
        props_action.triggered.connect(self.edit_properties)
        delete_action = menu.addAction("Delete connector")
        delete_action.triggered.connect(self.delete_connector)
        menu.exec(event.screenPos())

    def set_connector_type(self, conn_type):
        self.connector_type = conn_type
        self.update_path()
    
    def set_data_flow(self, flow):
        self.metadata['data_flow'] = flow
        self.update()
    
    def delete_connector(self):
        if self.scene():
            self.scene().removeItem(self)

            if hasattr(self.scene(), 'views') and self.scene().views():
                main_window = self.scene().views()[0].parent()
                if hasattr(main_window, 'connectors') and self in main_window.connectors:
                    main_window.connectors.remove(self)

    def update_position(self):
        self.update_path()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.update_path()
        return super().itemChange(change, value)
    def get_metadata_summary(self):
        summary = []
        if self.metadata.get('label'):
            summary.append(f"Label: {self.metadata['label']}")
        if self.metadata.get('protocol'):
            summary.append(f"Protocol: {self.metadata['protocol']}")
        if self.metadata.get('data_type'):
            summary.append(f"Data: {self.metadata['data_type']}")
        if self.metadata.get('encrypted'):
            summary.append("Encrypted: Yes")
        if self.metadata.get('authenticated'):
            summary.append("Authenticated: Yes")
        return summary

    def is_connected_to_shape(self, shape):
        return self.start_shape == shape or self.end_shape == shape
    
    def get_other_shape(self, shape):
        if self.start_shape == shape:
            return self.end_shape
        elif self.end_shape == shape:
            return self.start_shape
        return None
    
class ConnectorManager:
    def __init__(self, scene):
        self.scene = scene
        self.connectors = []
    
    def create_connector(self, start_shape, end_shape, connector_type = "line"):
        connector = ConnectorItem(start_shape, end_shape, connector_type)
        self.connectors.append(connector)
        self.scene.addItem(connector)
        return connector
    
    def update_connectors_for_shape(self, shape):
        for connector in self.connectors:
            if connector.is_connected_to_shape(shape):
                connector.update_position()
    
    def remove_connectors_for_shape(self, shape):
        connectors_to_remove = []
        for connector in self.connectors:
            if connector.is_connected_to_shape(shape):
                connectors_to_remove.append(connector)
        for connector in connectors_to_remove:
            self.scene.removeItem(connector)
            self.connectors.remove(connector)
    
    def get_connectors_for_shape(self, shape):
        return [conn for conn in self.connectors if conn.is_connected_to_shape(shape)]
    
    def clear_all_connectors(self):
        for connector in self.connectors:
            self.scene.removeItem(connector)
        self.connectors.clear()

             
    
        
