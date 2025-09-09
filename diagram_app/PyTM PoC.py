import sys
#this file is for later conversion into pytm integration; foundation basically
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
                             QGraphicsLineItem, QGraphicsTextItem, QLabel, QComboBox, QLineEdit, QGroupBox, QFormLayout, QCheckBox, QTabWidget)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
#pip install pytm
try:
    from pytm import TM, Server, Actor, Dataflow, Boundary, Element, Process, Datastore
    pytm_available = True
except ImportError:
    #making some shit up
    pytm_available = False
    print("pytm not installed, using made up shit instead")

    class mockElement:
        def __init__(self, name):
            self.name = name
            self.threats = []

    class tm(mockElement):
        def __init__(self):
            self.threats = []
        
    def check(self):
        threats = {
            "element": "Web Server", "threat": "spoofing", "severity": "high", "element": "database", "threat": "information disclosure", "Severity": "medium", "element": "user input", "threat": "tampering", "severity": "high",
        }
        return threats
    class Actor(mockElement): pass
    class Server(mockElement): pass
    class process(mockElement): pass
    class dataStore(mockElement): pass
    class boundary(mockElement): pass
    class Dataflow(mockElement):
        def __init__(self, source, sink, name):
            self.source = source
            self.sink = sink

class diagramElement:
    def __init__(self, element_type, name, x, y):
        self.element_type = element_type #"actor", "server", "process", "datastore", "boundary"
        self.name = name
        self.x = x
        self.y = y
        self.properties = {}
    def to_pytm_element(self):
        if self.element_type == "actor":
            return Actor(self.name)
        elif self.element_type == "server":
            return Server(self.name)
        elif self.element_type == "process":
            return Process(self.name)
        elif self.element_type == "datastore":
            return dataStore(self.name)
        elif self.element_type == "boundary":
            return Boundary(self.name)
        return None
    
class threatModelCanvas(QGraphicsView):
    element_selected = pyqtSignal(object)

    def __init__(self):
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.elements = []
        self.visual_items = {}
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.scene.setSceneRect(0, 0, 800, 600)
    def add_element(self, element_type, name, x, y):
        diagram_element = diagramElement(element_type, name, x, y)
        self.elements.append(diagram_element)
        if element_type == "actor":
            visual_item = self.scene.addEllipse(x, y, 60, 60,
                                                QPen(QColor("blue"), 2),
                                                QBrush(QColor("lightblue")))
        elif element_type == "server":
            visual_item = self.scene.addRect(x, y, 80, 50,
                                             QPen(QColor("green"),2),
                                             QBrush(QColor("lightgreen")))
        elif element_type == "process":
            visual_item = self.scene.addEllipse(x, y, 70, 50,
                                                QPen(QColor("organge"), 2),
                                                QBrush(QColor("lightorange")))


        elif element_type == "datastore":
            visual_item = self.scene.addRect(x, y, 90, 30,
                                             QPen(QColor("purple"), 2),
                                             QBrush(QColor("lightpurple")))        


        elif element_type == "boundary":
            visual_item = self.scene.addRect(x, y, 120, 80,
                                             QPen(QColor("red"),2),
                                             QBrush(QColor("lightred")))
        label = self.scene.addText(name, QFont("Arial", 8))
        label.setPos(x+5, y+5)
        self.visual_items[visual_item] = diagram_element
        return visual_item
    def mousePressEvent(self, event):
        return super().mousePressEvent(event)
        item = self.itemAt(event.pos())
        if item and item in self.visual_items:
            self.element_selected.emit(self.visual_items[item])
    def get_pytm_model(self):
        tm = TM("Pygram Diagram")
        pytm_elements = {}
        for element in self.elements:
            pytm_element = element.to_pytm_element()
            if pytm_element:
                pytm_elements[element.name] = pytm_element

        tm.elements = list(pytm_elements.values())
        return tm

class PropertyPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.current_element = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        info_group = QGroupBox("Element Information")
        info_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.type_label = QLabel("No element selected")
        info_layout.addRow("Name", self.name_edit)
        info_layout.addRow("Type:", self.type_label)
        info_group.setLayout(info_layout)

        threat_group = QGroupBox("Threat Modeling Properties")
        threat_layout = QFormLayout()

        self.has_authentication = QCheckBox()
        self.has_authorization = QCheckBox()
        self.handles_pii = QCheckBox()
        self.internet_facing = QCheckBox()

        threat_layout.addRow("Has authentication:", self.has_authentication)
        threat_layout.addRow("Has authorization:", self.has_authorization)
        threat_layout.addRow("Handles PII:", self.handles_pii)
        threat_layout.addRow("Internet Facing:", self.internet_facing)
        threat_group.setLayout(threat_layout)

        layout.addWidget(info_group)
        layout.addWidget(threat_group)
        layout.addStretch()

        self.setLayout(layout)
    
    def set_element(self, element):
        self.current_element = element
        if element:
            self.name_edit.setText(element.name)
            self.type_label.setText(element.element_type.capitalize())
            props = element.properties
            self.has_authentication.setChecked(props.get("has_auth", False))
            self.has_authorization.setChecked(props.get("has_authz", False))
            self.handles_pii.setChecked(props.get("handles_pii", False))
            self.internet_facing.setChecked(props.get("internet_facing", False))
        else:
            self.name_edit.setText("")
            self.type_label.setText("No element selected")
class ThreatResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout

        controls_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Run Threat Analysis")
        self.export_button = QPushButton("Export Report")

        controls_layout.addWidget(self.analyze_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addStretch()

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Element", "Threat Type", "Severity", "Description"])

        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setPlaceholderText("Select a tgreat to see details and mitigation suggestions!")

        layout.addLayout(controls_layout)
        layout.addWidget(QLabel("Identified Threats:"))
        layout.addWidget(self.results_tree)
        layout.addWidget(QLabel("Threat Details:"))
        layout.addWidget(self.details_text)
        self.setLaoyut(layout)
        self.results_tree.itemClicked.connect(self.show_threat_details)
    
    def update_threats(self, threats):
        self.results_tree.clear()
        for threat in threats:
            item = QTreeWidget([
                threat.get("element", "Unknown"),
                threat.get("threat", "Unknown"),
                threat.get("severity", "Unknown"),
                threat.get("description", "No description available")
            ])
            if threat.get("severity") == "High":
                item.setbackgound(0, QBrush(QColor("lightcoral")))
            elif threat.get("severity") == "Medium":
                item.setBackground(0, QBrush(QColor("lightyellow")))
            else:
                item.setBackground(0, QBrush(QColor("lightgreen")))
            self.results_tree.addTopLevelItem(item)
    def show_threat_details(self, item):
        threat_type = item.text(1)
        element = item.text(0)
        details = {
            "Spoofing": f"The {element} component may be vulnerable to spoofing attacks where an attacker impersonates a legitimate user or system.",
            "Tampering": f"Data flowing through {element} could be modified by an attacker without detection.",
            "Information Disclosure": f"Sensitive information in {element} may be exposed to unauthorized parties.",
        }
        detail_text = details.get(threat_type, "No details available for this threat type.")
        self.details_text.setPlainText(detail_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    def setup_ui(self):
        self.setWindowTitle("Pygram - Threat Modelling PoC")
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout
        toolbox = QWidget()
        toolbox.setMaximumWidth(200)
        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Diagramming", "Threat Modeling"])
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        tools_group = QGroupBox("Add Elements")
        tools_layout = QVBoxLayout
        self.add_actor_btn = QPushButton("Add Actor")
        self.add_server_btn = QPushButton("Add Server")
        self.add_process_btn = QPushButton("Add Process")
        self.add_datastore_btn = QPushButton("Add Data Store")
        self.add_boundary_btn = QPushButton("Add Boundary")
        tools_layout.addWidget(self.add_actor_btn)
        tools_layout.addWidget(self.add_server_btn)
        tools_layout.addWidget(self.add_process_btn)
        tools_layout.addWidget(self.add_datastore_btn)
        tools_layout.addWidget(self.add_boundary_btn)
        tools_group.setLayout(tools_layout)
        toolbox_layout.addWidget(mode_group)
        toolbox_layout.addWidget(tools_group)
        toolbox_layout.addStretch()
        toolbox.setLayout(toolbox_layout)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = threatModelCanvas
        right_panel = QTabWidget()
        right_panel.setMaximumWidth(400)
        self.property_panel = PropertyPanel
        self.threats_panel = ThreatResultsPanel()
        right_panel.addTab(self.property_panel, "Properties")
        right_panel.addTab(self.threats_panel, "Threats")
        splitter.addWidgets(self.canvas)
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 400])
        main_layout.addWidget(toolbox)
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.canvas.element_selected.connect(self.property_panel.set_element)
        self.threats_panel.analyze_button.clicked.connect(self.run_threat_alaysis)
        self.threats_panel.export_button.clicked.connect(self.export_report)
        self.add_actor_btn.clicked.connect(lambda: self.add_element("actor"))
        self.add_server_btn.clicked.connect(lambda: self.add_element("server"))
        self.add_process_btn.clicked.connect(lambda: self.add_element("process"))
        self.add_datastore_btn.clicked.connect(lambda: self.add_element("datastore"))
        self.add_boundary_btn.clicked.connect(lambda: self.add_element("boundary"))
        self.setup_demo_diagram()

    def add_element(self, element_type):
        import random
        name = f"{element_type.capitalize()} {random.randomint(1, 100)}"
        x = random.randint(50, 600)
        y = random.randint(50, 400)
        self.canvas.add_element(element_type, name, x, y)
    
    def setup_demo_diagram(self):
        self.canvas.add_element("actor", "User", 50, 100)
        self.canvas.add_element("server", "Web Server", 250, 100)
        self.canvas.add_element("datastore", "Database", 450, 100)
        self.canvas.add_element("boundary", "DMZ", 200, 50)
    
    def run_threat_analysis(self):
        tm = self.canvas.get_pytm_model()
        try:
            threats = tm.check()
            self.threats_panel.update_threats(threats)
        except Exception as e:
            print(f"Threat analysis error 42: {e}")
            fake_threats = {
                {"element": "Web Server", "Threat": "Spoofing", "severity": "High", "Description": "Server identity verification needed"},
                {"Element": "Database", "Threat": "Information Disclusre", "Severity": "Medium", "Description": "Database access control required"},
                {"Element": "User", "Threat": "Tampering", "Severity": "High", "Description": "Input validation needed"},
            }
            self.threats_panel.update_threats(fake_threats)
    
#    def export_report(self):
        #for now, we're skipping in poc- but ideally, this saves to PDF, HTML, and JSON, and use pytm's report shit

def main():
    app = QApplication(sys.argv)
    if not pytm_available:
        print("This is a demo Poc. If you want a real one, install pytm.")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()