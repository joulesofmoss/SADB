from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QComboBox, QTextEdit, QSpinBox, QCheckBox, QGroupBox, QScrollArea, QPushButton, QListWidget, QListWidgetItem, QInputDialog, QColorDialog, QTabWidget, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from errorLogging import getLogger, safe_execute, gui_safe_execute, erorrHandler

class MetadataPanel(QWidget):
    metadata_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = getLogger("metadata_panel")
        self.current_shape = None
        self.setup_ui()
    
    @gui_safe_execute
    def setup_ui(self):
        with erorrHandler("metadata panel UI setup", self.logger):
            layout = QVBoxLayout()
            layout.setSpacing(5)
            layout.setContentsMargins(10, 10, 10, 10)
            title = QLabel("Shape Properties")
            title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
            layout.addWidget(title)

            self.tab_widget = QTabWidget()
            
            basic_tab = QWidget()
            self.setup_basic_tab(basic_tab)
            self.tab_widget.addTab(basic_tab, "Basic")

            security_tab = QWidget()
            self.setup_security_tab(security_tab)
            self.tab_widget.addTab(security_tab, "Security")
            
            technical_tab = QWidget()
            self.setup_technical_tab(technical_tab)
            self.tab_widget.addTab(technical_tab, "Technical")
            
            trust_tab = QWidget()
            self.setup_trust_tab(trust_tab)
            self.tab_widget.addTab(trust_tab, "Trust & Compliance")

            layout.addWidget(self.tab_widget)
            self.setLayout(layout)
    
    @gui_safe_execute
    def setup_basic_tab(self, tab):
        with erorrHandler("basic tab setup", self.logger):
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            layout = QVBoxLayout(scroll_widget)

            basic_group = QGroupBox("Basic Information")
            basic_layout = QFormLayout()

            self.label_edit = QLineEdit()
            self.label_edit.textChanged.connect(self.on_basic_property_changed)
            basic_layout.addRow("Label:", self.label_edit)

            self.description_edit = QTextEdit()
            self.description_edit.setMaximumHeight(80)
            self.description_edit.textChanged.connect(self.on_basic_property_changed)
            basic_layout.addRow("Description:", self.description_edit)

            self.category_combo = QComboBox()
            self.category_combo.addItems([
                "Process", "Data Store", "External Entity", "Data Flow",
                "Trust Boundary", "Threat Actor", "Asset", "Control"
            ])
            self.category_combo.currentTextChanged.connect(self.on_basic_property_changed)
            basic_layout.addRow("Category:", self.category_combo)

            self.priority_combo = QComboBox()
            self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
            self.priority_combo.currentTextChanged.connect(self.on_basic_property_changed)
            basic_layout.addRow("Priority:", self.priority_combo)

            self.owner_edit = QLineEdit()
            self.owner_edit.textChanged.connect(self.on_basic_property_changed)
            basic_layout.addRow("Owner:", self.owner_edit)

            basic_group.setLayout(basic_layout)
            layout.addWidget(basic_group)

            identification_group = QGroupBox("Identification")
            identification_layout = QFormLayout()

            self.id_edit = QLineEdit()
            self.id_edit.textChanged.connect(self.on_basic_property_changed)
            identification_layout.addRow("ID:", self.id_edit)

            self.version_edit = QLineEdit()
            self.version_edit.textChanged.connect(self.on_basic_property_changed)
            identification_layout.addRow("Version:", self.version_edit)

            self.created_date_edit = QLineEdit()
            self.created_date_edit.textChanged.connect(self.on_basic_property_changed)
            identification_layout.addRow("Created:", self.created_date_edit)

            self.modified_date_edit = QLineEdit()
            self.modified_date_edit.textChanged.connect(self.on_basic_property_changed)
            identification_layout.addRow("Modified:", self.modified_date_edit)

            identification_group.setLayout(identification_layout)
            layout.addWidget(identification_group)

            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(scroll_area)

    @gui_safe_execute
    def setup_security_tab(self, tab):
        with erorrHandler("security tab setup", self.logger):
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            layout = QVBoxLayout(scroll_widget)

            access_group = QGroupBox("Access Control")
            access_layout = QFormLayout()

            self.authentication_combo = QComboBox()
            self.authentication_combo.addItems([
                "None", "Basic Authentication", "Windows Authentication", 
                "Certificate Authentication", "Multi-Factor Authentication",
                "OAuth", "SAML", "Kerberos"
            ])
            self.authentication_combo.currentTextChanged.connect(self.on_security_property_changed)
            access_layout.addRow("Authentication:", self.authentication_combo)

            self.authorization_combo = QComboBox()
            self.authorization_combo.addItems([
                "None", "Role-Based Access Control (RBAC)", 
                "Attribute-Based Access Control (ABAC)",
                "Discretionary Access Control (DAC)", "Mandatory Access Control (MAC)"
            ])
            self.authorization_combo.currentTextChanged.connect(self.on_security_property_changed)
            access_layout.addRow("Authorization:", self.authorization_combo)

            self.privileges_edit = QLineEdit()
            self.privileges_edit.setPlaceholderText("e.g., Read, Write, Execute, Admin")
            self.privileges_edit.textChanged.connect(self.on_security_property_changed)
            access_layout.addRow("Required Privileges:", self.privileges_edit)

            access_group.setLayout(access_layout)
            layout.addWidget(access_group)

            encryption_group = QGroupBox("Encryption & Data Protection")
            encryption_layout = QFormLayout()

            self.encryption_transit_combo = QComboBox()
            self.encryption_transit_combo.addItems([
                "None", "TLS 1.2", "TLS 1.3", "IPSec", "SSL", "Custom"
            ])
            self.encryption_transit_combo.currentTextChanged.connect(self.on_security_property_changed)
            encryption_layout.addRow("Encryption in Transit:", self.encryption_transit_combo)

            self.encryption_rest_combo = QComboBox()
            self.encryption_rest_combo.addItems([
                "None", "AES-256", "AES-128", "RSA", "BitLocker", "Custom"
            ])
            self.encryption_rest_combo.currentTextChanged.connect(self.on_security_property_changed)
            encryption_layout.addRow("Encryption at Rest:", self.encryption_rest_combo)

            self.data_classification_combo = QComboBox()
            self.data_classification_combo.addItems([
                "Public", "Internal", "Confidential", "Restricted", "Top Secret"
            ])
            self.data_classification_combo.currentTextChanged.connect(self.on_security_property_changed)
            encryption_layout.addRow("Data Classification:", self.data_classification_combo)

            encryption_group.setLayout(encryption_layout)
            layout.addWidget(encryption_group)

            threats_group = QGroupBox("Threat Information")
            threats_layout = QVBoxLayout()

            threat_form = QFormLayout()
            self.threat_level_combo = QComboBox()
            self.threat_level_combo.addItems(["Low", "Medium", "High", "Critical"])
            self.threat_level_combo.currentTextChanged.connect(self.on_security_property_changed)
            threat_form.addRow("Threat Level:", self.threat_level_combo)

            threats_layout.addLayout(threat_form)

            self.threats_list = QListWidget()
            self.threats_list.setMaximumHeight(120)
            threats_layout.addWidget(QLabel("Identified Threats:"))
            threats_layout.addWidget(self.threats_list)

            threat_buttons = QHBoxLayout()
            self.add_threat_btn = QPushButton("Add Threat")
            self.add_threat_btn.clicked.connect(self.add_threat)
            self.remove_threat_btn = QPushButton("Remove Threat")
            self.remove_threat_btn.clicked.connect(self.remove_threat)
            threat_buttons.addWidget(self.add_threat_btn)
            threat_buttons.addWidget(self.remove_threat_btn)
            threats_layout.addLayout(threat_buttons)

            threats_group.setLayout(threats_layout)
            layout.addWidget(threats_group)

            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(scroll_area)

    @gui_safe_execute
    def setup_technical_tab(self, tab):
        with erorrHandler("technical tab setup", self.logger):
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            layout = QVBoxLayout(scroll_widget)

            network_group = QGroupBox("Network Configuration")
            network_layout = QFormLayout()

            self.ip_address_edit = QLineEdit()
            self.ip_address_edit.setPlaceholderText("e.g., 192.168.1.100")
            self.ip_address_edit.textChanged.connect(self.on_technical_property_changed)
            network_layout.addRow("IP Address:", self.ip_address_edit)

            self.port_edit = QLineEdit()
            self.port_edit.setPlaceholderText("e.g., 443, 80, 8080")
            self.port_edit.textChanged.connect(self.on_technical_property_changed)
            network_layout.addRow("Ports:", self.port_edit)

            self.protocol_combo = QComboBox()
            self.protocol_combo.addItems([
                "HTTP", "HTTPS", "TCP", "UDP", "FTP", "SFTP", "SSH", 
                "SMTP", "POP3", "IMAP", "DNS", "DHCP", "SNMP", "Custom"
            ])
            self.protocol_combo.currentTextChanged.connect(self.on_technical_property_changed)
            network_layout.addRow("Protocol:", self.protocol_combo)

            self.domain_edit = QLineEdit()
            self.domain_edit.setPlaceholderText("e.g., example.com")
            self.domain_edit.textChanged.connect(self.on_technical_property_changed)
            network_layout.addRow("Domain/FQDN:", self.domain_edit)

            network_group.setLayout(network_layout)
            layout.addWidget(network_group)

            system_group = QGroupBox("System Information")
            system_layout = QFormLayout()

            self.os_combo = QComboBox()
            self.os_combo.addItems([
                "Windows Server 2019", "Windows Server 2022", "Windows 10", "Windows 11",
                "Ubuntu 20.04", "Ubuntu 22.04", "CentOS 7", "CentOS 8", "RHEL 8", "RHEL 9",
                "macOS", "iOS", "Android", "Custom"
            ])
            self.os_combo.currentTextChanged.connect(self.on_technical_property_changed)
            system_layout.addRow("Operating System:", self.os_combo)
            self.service_account_edit = QLineEdit()
            self.service_account_edit.textChanged.connect(self.on_technical_property_changed)
            system_layout.addRow("Service Account:", self.service_account_edit)
            self.dependencies_edit = QTextEdit()
            self.dependencies_edit.setMaximumHeight(80)
            self.dependencies_edit.setPlaceholderText("List system dependencies...")
            self.dependencies_edit.textChanged.connect(self.on_technical_property_changed)
            system_layout.addRow("Dependencies:", self.dependencies_edit)
            system_group.setLayout(system_layout)
            layout.addWidget(system_group)
            database_group = QGroupBox("Database Information")
            database_layout = QFormLayout()
            self.db_type_combo = QComboBox()
            
            self.db_type_combo.addItems([
                "None", "SQL Server", "MySQL", "PostgreSQL", "Oracle", 
                "SQLite", "MongoDB", "Redis", "Cassandra", "Custom"
            ])
            
            self.db_type_combo.currentTextChanged.connect(self.on_technical_property_changed)
            database_layout.addRow("Database Type:", self.db_type_combo)
            self.db_version_edit = QLineEdit()
            self.db_version_edit.textChanged.connect(self.on_technical_property_changed)
            database_layout.addRow("Database Version:", self.db_version_edit)
            self.connection_string_edit = QLineEdit()
            self.connection_string_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.connection_string_edit.textChanged.connect(self.on_technical_property_changed)
            database_layout.addRow("Connection String:", self.connection_string_edit)
            database_group.setLayout(database_layout)
            layout.addWidget(database_group)
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(scroll_area)

    @gui_safe_execute
    def setup_trust_tab(self, tab):
        with erorrHandler("trust tab setup", self.logger):
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            layout = QVBoxLayout(scroll_widget)

            trust_group = QGroupBox("Trust Boundaries")
            trust_layout = QFormLayout()

            self.trust_level_combo = QComboBox()
            self.trust_level_combo.addItems([
                "Untrusted", "Low Trust", "Medium Trust", "High Trust", "Fully Trusted"
            ])
            self.trust_level_combo.currentTextChanged.connect(self.on_trust_property_changed)
            trust_layout.addRow("Trust Level:", self.trust_level_combo)

            self.network_zone_combo = QComboBox()
            self.network_zone_combo.addItems([
                "Internet", "DMZ", "Internal Network", "Secure Network", 
                "Management Network", "Isolated Network"
            ])
            self.network_zone_combo.currentTextChanged.connect(self.on_trust_property_changed)
            trust_layout.addRow("Network Zone:", self.network_zone_combo)

            self.boundary_type_combo = QComboBox()
            self.boundary_type_combo.addItems([
                "None", "Firewall", "Application Boundary", "Process Boundary",
                "Machine Boundary", "Subnet Boundary", "Domain Boundary"
            ])
            self.boundary_type_combo.currentTextChanged.connect(self.on_trust_property_changed)
            trust_layout.addRow("Boundary Type:", self.boundary_type_combo)

            trust_group.setLayout(trust_layout)
            layout.addWidget(trust_group)

            compliance_group = QGroupBox("Compliance & Standards")
            compliance_layout = QVBoxLayout()

            compliance_form = QFormLayout()
            
            self.compliance_frameworks_edit = QLineEdit()
            self.compliance_frameworks_edit.setPlaceholderText("e.g., SOX, HIPAA, PCI-DSS, GDPR")
            self.compliance_frameworks_edit.textChanged.connect(self.on_trust_property_changed)
            compliance_form.addRow("Compliance Frameworks:", self.compliance_frameworks_edit)

            self.security_standards_edit = QLineEdit()
            self.security_standards_edit.setPlaceholderText("e.g., ISO 27001, NIST, CIS Controls")
            self.security_standards_edit.textChanged.connect(self.on_trust_property_changed)
            compliance_form.addRow("Security Standards:", self.security_standards_edit)

            compliance_layout.addLayout(compliance_form)

            self.audit_checkbox = QCheckBox("Subject to Regular Audits")
            self.audit_checkbox.stateChanged.connect(self.on_trust_property_changed)
            compliance_layout.addWidget(self.audit_checkbox)

            self.logging_checkbox = QCheckBox("Security Logging Enabled")
            self.logging_checkbox.stateChanged.connect(self.on_trust_property_changed)
            compliance_layout.addWidget(self.logging_checkbox)

            self.monitoring_checkbox = QCheckBox("Continuous Monitoring")
            self.monitoring_checkbox.stateChanged.connect(self.on_trust_property_changed)
            compliance_layout.addWidget(self.monitoring_checkbox)

            compliance_group.setLayout(compliance_layout)
            layout.addWidget(compliance_group)

            business_group = QGroupBox("Business Context")
            business_layout = QFormLayout()

            self.business_impact_combo = QComboBox()
            self.business_impact_combo.addItems([
                "Minimal", "Low", "Medium", "High", "Critical"
            ])
            self.business_impact_combo.currentTextChanged.connect(self.on_trust_property_changed)
            business_layout.addRow("Business Impact:", self.business_impact_combo)

            self.data_retention_edit = QLineEdit()
            self.data_retention_edit.setPlaceholderText("e.g., 7 years, 30 days")
            self.data_retention_edit.textChanged.connect(self.on_trust_property_changed)
            business_layout.addRow("Data Retention:", self.data_retention_edit)

            self.backup_frequency_combo = QComboBox()
            self.backup_frequency_combo.addItems([
                "None", "Real-time", "Hourly", "Daily", "Weekly", "Monthly"
            ])
            self.backup_frequency_combo.currentTextChanged.connect(self.on_trust_property_changed)
            business_layout.addRow("Backup Frequency:", self.backup_frequency_combo)

            business_group.setLayout(business_layout)
            layout.addWidget(business_group)

            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(scroll_area)

    @gui_safe_execute
    def add_threat(self, *args):
        with erorrHandler("add threat", self.logger):
            threat_types = [
                "Spoofing", "Tampering", "Repudiation", "Information Disclosure",
                "Denial of Service", "Elevation of Privilege", "SQL Injection",
                "Cross-Site Scripting (XSS)", "Cross-Site Request Forgery (CSRF)",
                "Buffer Overflow", "Man-in-the-Middle", "Phishing", "Malware",
                "Social Engineering", "Physical Access", "Custom"
            ]
            
            threat, ok = QInputDialog.getItem(
                self, "Add Threat", "Select threat type:", threat_types, 0, False
            )
            
            if ok and threat:
                if threat == "Custom":
                    custom_threat, ok = QInputDialog.getText(
                        self, "Custom Threat", "Enter custom threat:"
                    )
                    if ok and custom_threat:
                        threat = custom_threat
                
                if threat and threat != "Custom":
                    item = QListWidgetItem(threat)
                    self.threats_list.addItem(item)
                    self.on_security_property_changed()

    @gui_safe_execute
    def remove_threat(self, *args):
        with erorrHandler("remove threat", self.logger):
            current_item = self.threats_list.currentItem()
            if current_item:
                row = self.threats_list.row(current_item)
                self.threats_list.takeItem(row)
                self.on_security_property_changed()

    @gui_safe_execute
    def on_basic_property_changed(self, *args):
        with erorrHandler("basic property changed", self.logger):
            metadata = self.get_all_metadata()
            self.metadata_changed.emit(metadata)

    @gui_safe_execute
    def on_security_property_changed(self, *args):
        with erorrHandler("security property changed", self.logger):
            metadata = self.get_all_metadata()
            self.metadata_changed.emit(metadata)

    @gui_safe_execute
    def on_technical_property_changed(self, *args):
        with erorrHandler("technical property changed", self.logger):
            metadata = self.get_all_metadata()
            self.metadata_changed.emit(metadata)

    @gui_safe_execute
    def on_trust_property_changed(self, *args):
        with erorrHandler("trust property changed", self.logger):
            metadata = self.get_all_metadata()
            self.metadata_changed.emit(metadata)

    @gui_safe_execute
    def get_all_metadata(self):
        with erorrHandler("get all metadata", self.logger):
            threats = []
            for i in range(self.threats_list.count()):
                threats.append(self.threats_list.item(i).text())

            metadata = {
                'basic': {
                    'label': self.label_edit.text(),
                    'description': self.description_edit.toPlainText(),
                    'category': self.category_combo.currentText(),
                    'priority': self.priority_combo.currentText(),
                    'owner': self.owner_edit.text(),
                    'id': self.id_edit.text(),
                    'version': self.version_edit.text(),
                    'created': self.created_date_edit.text(),
                    'modified': self.modified_date_edit.text()
                },
                'security': {
                    'authentication': self.authentication_combo.currentText(),
                    'authorization': self.authorization_combo.currentText(),
                    'privileges': self.privileges_edit.text(),
                    'encryption_transit': self.encryption_transit_combo.currentText(),
                    'encryption_rest': self.encryption_rest_combo.currentText(),
                    'data_classification': self.data_classification_combo.currentText(),
                    'threat_level': self.threat_level_combo.currentText(),
                    'threats': threats
                },
                'technical': {
                    'ip_address': self.ip_address_edit.text(),
                    'ports': self.port_edit.text(),
                    'protocol': self.protocol_combo.currentText(),
                    'domain': self.domain_edit.text(),
                    'operating_system': self.os_combo.currentText(),
                    'service_account': self.service_account_edit.text(),
                    'dependencies': self.dependencies_edit.toPlainText(),
                    'db_type': self.db_type_combo.currentText(),
                    'db_version': self.db_version_edit.text(),
                    'connection_string': self.connection_string_edit.text()
                },
                'trust': {
                    'trust_level': self.trust_level_combo.currentText(),
                    'network_zone': self.network_zone_combo.currentText(),
                    'boundary_type': self.boundary_type_combo.currentText(),
                    'compliance_frameworks': self.compliance_frameworks_edit.text(),
                    'security_standards': self.security_standards_edit.text(),
                    'audit_required': self.audit_checkbox.isChecked(),
                    'logging_enabled': self.logging_checkbox.isChecked(),
                    'monitoring_enabled': self.monitoring_checkbox.isChecked(),
                    'business_impact': self.business_impact_combo.currentText(),
                    'data_retention': self.data_retention_edit.text(),
                    'backup_frequency': self.backup_frequency_combo.currentText()
                }
            }
            return metadata

    @gui_safe_execute
    def set_metadata(self, metadata):
        with erorrHandler("set metadata", self.logger):
            if not metadata:
                return

            basic = metadata.get('basic', {})
            self.label_edit.setText(basic.get('label', ''))
            self.description_edit.setText(basic.get('description', ''))
            self.category_combo.setCurrentText(basic.get('category', 'Process'))
            self.priority_combo.setCurrentText(basic.get('priority', 'Medium'))
            self.owner_edit.setText(basic.get('owner', ''))
            self.id_edit.setText(basic.get('id', ''))
            self.version_edit.setText(basic.get('version', ''))
            self.created_date_edit.setText(basic.get('created', ''))
            self.modified_date_edit.setText(basic.get('modified', ''))

            security = metadata.get('security', {})
            self.authentication_combo.setCurrentText(security.get('authentication', 'None'))
            self.authorization_combo.setCurrentText(security.get('authorization', 'None'))
            self.privileges_edit.setText(security.get('privileges', ''))
            self.encryption_transit_combo.setCurrentText(security.get('encryption_transit', 'None'))
            self.encryption_rest_combo.setCurrentText(security.get('encryption_rest', 'None'))
            self.data_classification_combo.setCurrentText(security.get('data_classification', 'Public'))
            self.threat_level_combo.setCurrentText(security.get('threat_level', 'Low'))
            
            self.threats_list.clear()
            for threat in security.get('threats', []):
                item = QListWidgetItem(threat)
                self.threats_list.addItem(item)

            technical = metadata.get('technical', {})
            self.ip_address_edit.setText(technical.get('ip_address', ''))
            self.port_edit.setText(technical.get('ports', ''))
            self.protocol_combo.setCurrentText(technical.get('protocol', 'HTTP'))
            self.domain_edit.setText(technical.get('domain', ''))
            self.os_combo.setCurrentText(technical.get('operating_system', 'Windows Server 2019'))
            self.service_account_edit.setText(technical.get('service_account', ''))
            self.dependencies_edit.setText(technical.get('dependencies', ''))
            self.db_type_combo.setCurrentText(technical.get('db_type', 'None'))
            self.db_version_edit.setText(technical.get('db_version', ''))
            self.connection_string_edit.setText(technical.get('connection_string', ''))

            trust = metadata.get('trust', {})
            self.trust_level_combo.setCurrentText(trust.get('trust_level', 'Medium Trust'))
            self.network_zone_combo.setCurrentText(trust.get('network_zone', 'Internal Network'))
            self.boundary_type_combo.setCurrentText(trust.get('boundary_type', 'None'))
            self.compliance_frameworks_edit.setText(trust.get('compliance_frameworks', ''))
            self.security_standards_edit.setText(trust.get('security_standards', ''))
            self.audit_checkbox.setChecked(trust.get('audit_required', False))
            self.logging_checkbox.setChecked(trust.get('logging_enabled', False))
            self.monitoring_checkbox.setChecked(trust.get('monitoring_enabled', False))
            self.business_impact_combo.setCurrentText(trust.get('business_impact', 'Medium'))
            self.data_retention_edit.setText(trust.get('data_retention', ''))
            self.backup_frequency_combo.setCurrentText(trust.get('backup_frequency', 'Daily'))

    @gui_safe_execute
    def clear_all(self):
        with erorrHandler("clear all metadata", self.logger):
            self.set_metadata({})