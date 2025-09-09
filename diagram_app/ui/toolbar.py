from PyQt6.QtWidgets import (QToolBar, QLabel, QVBoxLayout, QWidget, QComboBox, QFrame, QScrollArea, QPushButton, QHBoxLayout, QGroupBox, QCheckBox, QSlider, QSpinBox, QTabWidget)
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal

class CollapsibleGroupBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.on_toggle)
        
    def on_toggle(self, checked):
        for child in self.findChildren(QWidget):
            if child != self:
                child.setVisible(checked)

class ToolbarManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.toolbar = None
        self.tool_group = None
        self.current_tool = "select"
        self.favorite_tools = ["select", "rect", "circle", "user", "process", "connector"]
        self.recent_tools = ["select"]
        self.max_recent_tools = 5
        
        self.shape_categories = {
            "Basic Shapes": {
                "description": "Fundamental geometric shapes",
                "tools": [
                    ("select", "Select/Move", "🖱️", "Select and move objects"),
                    ("rect", "Rectangle", "▮", "Draw rectangles"),
                    ("circle", "Circle", "⚪", "Draw circles and ellipses"),
                    ("diamond", "Diamond", "💎", "Draw diamond shapes"),
                    ("triangle", "Triangle", "🔺", "Draw triangular shapes"),
                    ("hexagon", "Hexagon", "⬡", "Draw hexagonal shapes"),
                    ("star", "Star", "⭐", "Draw star shapes"),
                    ("arrow", "Arrow", "⬆", "Draw directional arrows"),
                ]
            },
            "Cloud Infrastructure": {
                "description": "Cloud and server components",
                "tools": [
                    ("cloud", "Cloud", "☁️", "Cloud services representation"),
                    ("server", "Server", "🖧", "Physical or virtual servers"),
                    ("database", "Database", "🗄️", "Database systems"),
                    ("cylinder", "Database Cylinder", "🛢", "Traditional database symbol"),
                    ("network", "Network", "🌐", "Network infrastructure"),
                ]
            },
            "Threat Modeling": {
                "description": "Security analysis components",
                "tools": [
                    ("user", "User/Actor", "👤", "System users or actors"),
                    ("process", "Process", "⚙️", "System processes"),
                    ("datastore", "Data Store", "💾", "Data storage locations"),
                    ("external", "External Entity", "🏢", "External system entities"),
                    ("threat", "Threat", "⚠", "Security threats"),
                    ("boundary", "Trust Boundary", "🔒", "Security boundaries"),
                    ("decision", "Decision Point", "❓", "Decision nodes"),
                ]
            },
            "Flow & UML": {
                "description": "Flowchart and UML elements",
                "tools": [
                    ("start_end", "Start/End", "🏁", "Process start/end points"),
                    ("document", "Document", "📄", "Document representation"),
                    ("data", "Data", "📊", "Data flow elements"),
                    ("manual_input", "Manual Input", "⌨️", "Manual input processes"),
                    ("predefined", "Predefined Process", "📋", "Predefined operations"),
                ]
            },
            "Connectors": {
                "description": "Connection and relationship tools",
                "tools": [
                    ("connector", "Connect Shapes", "🔗", "Connect shapes with lines"),
                    ("data_flow", "Data Flow", "➡️", "Show data movement"),
                    ("control_flow", "Control Flow", "🔄", "Show control flow"),
                ]
            }
        }

    def create_toolbar(self): # FATHER TOOLBAR BESTOW ONTO ME, SO THAT YOU MAY VANQUISH MY SINS
        toolbar_widget = QWidget()
        main_layout = QVBoxLayout(toolbar_widget)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(3, 3, 3, 3)
        
        self.tool_group = QActionGroup(self.main_window)
        
        self.add_search_filter(main_layout)
        self.add_quick_access(main_layout)
        
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        shapes_tab = QWidget()
        shapes_layout = QVBoxLayout(shapes_tab)
        self.add_category_selector(shapes_layout)
        self.add_all_shape_categories(shapes_layout)
        tab_widget.addTab(shapes_tab, "🔧 Tools")
        
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        self.add_grouped_actions(actions_layout)
        tab_widget.addTab(actions_tab, "⚡ Actions")
        
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        self.add_settings_panel(settings_layout)
        tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        main_layout.addWidget(tab_widget)
        main_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidget(toolbar_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumWidth(200)
        scroll_area.setMaximumWidth(240)

        self.toolbar = QToolBar("Enhanced Tools")
        self.toolbar.setOrientation(Qt.Orientation.Vertical)
        self.toolbar.addWidget(scroll_area)

        self.main_window.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        return self.toolbar
    
    def add_search_filter(self, layout):
        search_group = CollapsibleGroupBox("🔍 Quick Search")
        search_layout = QVBoxLayout(search_group)
        
        self.search_combo = QComboBox()
        self.search_combo.setEditable(True)
        self.search_combo.setPlaceholderText("Search tools...")
        self.search_combo.currentTextChanged.connect(self.filter_by_search)
        
        all_tools = []
        for category_data in self.shape_categories.values():
            for tool_id, tool_name, emoji, description in category_data["tools"]:
                all_tools.append(f"{emoji} {tool_name}")
        
        self.search_combo.addItems(all_tools)
        search_layout.addWidget(self.search_combo)
        layout.addWidget(search_group)
    
    def add_quick_access(self, layout):
        quick_group = CollapsibleGroupBox("⭐ Quick Access")
        quick_layout = QVBoxLayout(quick_group)
        
        favorites_label = QLabel("Favorites:")
        favorites_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        quick_layout.addWidget(favorites_label)
        
        favorites_layout = QHBoxLayout()
        for tool_id in self.favorite_tools[:4]:
            tool_info = self.find_tool_info(tool_id)
            if tool_info:
                button = self.create_mini_tool_button(tool_id, tool_info[2], tool_info[1])
                favorites_layout.addWidget(button)
        quick_layout.addLayout(favorites_layout)
        
        recent_label = QLabel("Recent:")
        recent_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        quick_layout.addWidget(recent_label)
        
        self.recent_layout = QHBoxLayout()
        self.update_recent_tools_display()
        quick_layout.addLayout(self.recent_layout)
        
        layout.addWidget(quick_group)
    
    def add_category_selector(self, layout):
        selector_group = CollapsibleGroupBox("📂 Category Filter")
        selector_layout = QVBoxLayout(selector_group)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems(list(self.shape_categories.keys()))
        self.category_combo.currentTextChanged.connect(self.filter_categories)
        selector_layout.addWidget(self.category_combo)
        
        view_options_layout = QHBoxLayout()
        self.compact_view = QCheckBox("Compact")
        self.compact_view.toggled.connect(self.toggle_compact_view)
        self.show_descriptions = QCheckBox("Tips")
        self.show_descriptions.setChecked(True)
        self.show_descriptions.toggled.connect(self.toggle_descriptions)
        
        view_options_layout.addWidget(self.compact_view)
        view_options_layout.addWidget(self.show_descriptions)
        selector_layout.addLayout(view_options_layout)
        
        layout.addWidget(selector_group)

    def add_all_shape_categories(self, layout):
        for category_name, category_data in self.shape_categories.items():
            self.add_shape_category(layout, category_name, category_data)

    def add_shape_category(self, layout, category_name, category_data):
        category_group = CollapsibleGroupBox(category_name)
        category_layout = QVBoxLayout(category_group)
        
        if self.show_descriptions.isChecked() if hasattr(self, 'show_descriptions') else True:
            desc_label = QLabel(category_data["description"])
            desc_label.setStyleSheet("font-size: 10px; color: #666; font-style: italic;")
            desc_label.setWordWrap(True)
            category_layout.addWidget(desc_label)

        for tool_id, tool_name, emoji, description in category_data["tools"]:
            button = self.add_tool_button(category_layout, tool_id, tool_name, emoji, 
                                        category_name, description)
        
        category_group.setObjectName(f"category_{category_name.replace(' ', '_').lower()}")
        layout.addWidget(category_group)
    
    def add_tool_button(self, layout, tool_id, tool_name, emoji, category, description):
        button = QPushButton(f"{emoji} {tool_name}")
        button.setCheckable(True)
        button.setChecked(tool_id == "select")
        button.setToolTip(f"{tool_name}\n{description}\nCategory: {category}")
        button.setObjectName(f"tool_{tool_id}")

        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 10px;
                margin: 1px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: black;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e6f3ff;
                border-color: #0078d4;
                color: black;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
                border-color: #005a9e;
                font-weight: bold;
            } 
        """)

        button.clicked.connect(lambda checked, t=tool_id: self.select_tool(t, button))
        layout.addWidget(button)
        button.category = category
        button.description = description
        return button
    
    def create_mini_tool_button(self, tool_id, emoji, tool_name):
        button = QPushButton(emoji)
        button.setFixedSize(30, 30)
        button.setToolTip(tool_name)
        button.clicked.connect(lambda: self.select_tool(tool_id, None))
        button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e6f3ff;
                border-color: #0078d4;
            }
        """)
        return button
    
    def add_grouped_actions(self, layout):
        action_groups = {
            "File Operations": [
                ("💾", "Save Diagram", self.main_window.file_manager.save_diagram),
                ("📁", "Load Diagram", self.main_window.file_manager.load_diagram),
                ("📤", "Export Diagram", self.main_window.export_diagram),
            ],
            "View Controls": [
                ("🔍", "Zoom Fit", self.zoom_to_fit),
                ("🌐", "Toggle Grid", self.main_window.toggle_grid),
                ("🫰", "Toggle Snapping", self.main_window.toggle_grid_snapping),
                ("🤔", "Shape Properties", self.toggle_properties_panel),
            ],
            "Analysis": [
                ("💥", "Clear All", self.clear_diagram),
            ]
        }
        
        for group_name, actions in action_groups.items():
            group = CollapsibleGroupBox(group_name)
            group_layout = QVBoxLayout(group)
            
            for emoji, name, callback in actions:
                button = QPushButton(f"{emoji} {name}")
                button.clicked.connect(callback)
                button.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 5px 10px;
                        margin: 1px; 
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        background-color: #f8f8f8;
                        color: black;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #e8f4f8;
                        color: black;
                    }
                    QPushButton:pressed {
                        background-color: #d0e8f0;
                        color: black;
                    }
                """)
                group_layout.addWidget(button)
            
            layout.addWidget(group)
    
    def add_settings_panel(self, layout):
        grid_group = CollapsibleGroupBox("Grid Settings")
        grid_layout = QVBoxLayout(grid_group)
        
        grid_size_layout = QHBoxLayout()
        grid_size_layout.addWidget(QLabel("Grid Size:"))
        grid_size_spin = QSpinBox()
        grid_size_spin.setRange(10, 100)
        grid_size_spin.setValue(20)
        grid_size_layout.addWidget(grid_size_spin)
        grid_layout.addLayout(grid_size_layout)
        
        layout.addWidget(grid_group)
        
        ui_group = CollapsibleGroupBox("UI Preferences")
        ui_layout = QVBoxLayout(ui_group)
        
        auto_save = QCheckBox("Auto-save every 5 minutes")
        show_tooltips = QCheckBox("Show detailed tooltips")
        show_tooltips.setChecked(True)
        
        ui_layout.addWidget(auto_save)
        ui_layout.addWidget(show_tooltips)
        
        layout.addWidget(ui_group)
    
    def select_tool(self, tool_id, button):
        for child in self.toolbar.findChildren(QPushButton):
            if child.objectName().startswith("tool_"):
                child.setChecked(False)

        if button:
            button.setChecked(True)
        else:
            for child in self.toolbar.findChildren(QPushButton):
                if child.objectName() == f"tool_{tool_id}":
                    child.setChecked(True)
                    break

        self.current_tool = tool_id
        self.add_to_recent_tools(tool_id)
        self.main_window.set_tool(tool_id)
        print(f"Selected tool: {tool_id}")
    
    def add_to_recent_tools(self, tool_id):
        if tool_id in self.recent_tools:
            self.recent_tools.remove(tool_id)
        self.recent_tools.insert(0, tool_id)
        self.recent_tools = self.recent_tools[:self.max_recent_tools]
        self.update_recent_tools_display()
    
    def update_recent_tools_display(self):
        if not hasattr(self, 'recent_layout'):
            return
            
        while self.recent_layout.count():
            child = self.recent_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for tool_id in self.recent_tools[:4]:
            if tool_id != self.current_tool:
                tool_info = self.find_tool_info(tool_id)
                if tool_info:
                    button = self.create_mini_tool_button(tool_id, tool_info[2], tool_info[1])
                    self.recent_layout.addWidget(button)
    
    def find_tool_info(self, tool_id):
        for category_data in self.shape_categories.values():
            for tool_info in category_data["tools"]:
                if tool_info[0] == tool_id:
                    return tool_info
        return None
    
    def filter_categories(self, selected_category):
        show_all = selected_category == "All Categories"

        for child in self.toolbar.findChildren(CollapsibleGroupBox):
            if child.objectName().startswith("category_"):
                category_name = child.title()
                should_show = show_all or category_name == selected_category
                child.setVisible(should_show)
    
    def filter_by_search(self, search_text):
        if not search_text.strip():
            self.show_all_tools()
            return
        
        search_lower = search_text.lower()
        
        for child in self.toolbar.findChildren(QPushButton):
            if child.objectName().startswith("tool_"):
                tool_text = child.text().lower()
                description = getattr(child, 'description', '').lower()
                should_show = (search_lower in tool_text or 
                              search_lower in description)
                child.setVisible(should_show)
    
    def show_all_tools(self):
        for child in self.toolbar.findChildren(QPushButton):
            if child.objectName().startswith("tool_"):
                child.setVisible(True)
    
    def toggle_compact_view(self, enabled):
        font_size = "9px" if enabled else "11px"
        padding = "3px 6px" if enabled else "6px 10px"
        
        for child in self.toolbar.findChildren(QPushButton):
            if child.objectName().startswith("tool_"):
                current_style = child.styleSheet()
                new_style = current_style.replace("font-size: 11px", f"font-size: {font_size}")
                new_style = new_style.replace("padding: 6px 10px", f"padding: {padding}")
                child.setStyleSheet(new_style)
    
    def toggle_descriptions(self, enabled):
        for child in self.toolbar.findChildren(QLabel):
            if "font-style: italic" in child.styleSheet():
                child.setVisible(enabled)
    
    def toggle_properties_panel(self):
        if hasattr(self.main_window, 'properties_dock'):
            dock = self.main_window.properties_dock
            dock.setVisible(not dock.isVisible())
    
    def zoom_to_fit(self):
        if hasattr(self.main_window, 'view'):
            self.main_window.view.fitInView(
                self.main_window.scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )
    
    def clear_diagram(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            'Clear Diagram',
            'Are you sure you want to clear all shapes and connections?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.main_window.scene.clear()
            self.main_window.shapes.clear()
            self.main_window.connectors.clear()
    
    def get_current_tool(self):
        return self.current_tool
    
    def set_tool(self, tool_name):
        for button in self.toolbar.findChildren(QPushButton):
            if button.objectName() == f"tool_{tool_name}":
                for other_button in self.toolbar.findChildren(QPushButton):
                    if other_button.objectName().startswith("tool_"):
                        other_button.setChecked(False)
                
                button.setChecked(True)
                self.current_tool = tool_name
                self.main_window.set_tool(tool_name)
                break