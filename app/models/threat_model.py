import sys
import json
from typing import List, Dict, Any, Optional, Tuple, Set

from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from errorLogging import getLogger, safe_execute, gui_safe_execute, erorrHandler

try:
    from pytm import TM, Server, Actor, Dataflow, Boundary, Element, Process, Datastore, Lambda
    pytm_available = True
except ImportError:
    pytm_available = False
    print("PyTM not installed. Using build-in threat analysis engine!")

class ThreatType(Enum):
    spoofing = "Spoofing"
    tampering = "Tampering"
    repudiation = "Repudiation"
    information_disclosure = "Information Disclosure"
    denial_of_service = "Denial of Service"
    elevation_of_privilege = "Elevation of Privilege"

class SeverityLevel(Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    crit = "Critical" # this is not in danger

class ElementType(Enum):
    actor = "actor"
    process = "process"
    datastore = "datastore"
    server = "server"
    boundary = "boundary"
    external = "external"
    database = "database"
    user = "user"

@dataclass
class ThreatInfo: # this is the danger.
    id: str
    element_name: str
    element_type: str
    threat_type: str
    severity: str
    desccription: str
    condition: str
    likelihood: str = "Medium"
    impact: str = "Medium"
    mitigations: List[str] = None
    references: List[str] = None

    def __post_init__(self):
        if self.mitigations is None:
            self.mitigations = []
        if self.references is None:
            self.references = []
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ElementSecurityProperties:
    has_authentication: bool = False
    has_authorization: bool = False
    has_encrypted_transit: bool = False
    has_encryption_rest: bool = False
    has_input_validation: bool=False
    has_output_encoding: bool = False
    has_logging: bool = False
    has_monitoring: bool = False
    is_hardened: bool = False
    is_internet_facing: bool = False
    handels_pii: bool = False
    data_classification: str = "Public"
    trust_level: str = "Low"

    def get_risk_score(self)->int:
        score = 0
        if not self.has_authentication: score += 2
        if not self.has_authorization: score += 2
        if not self.has_encrypted_transit: score +=1
        if not self.has_input_validation: score += 3
        if self.is_internet_facing: score += 2
        if self.handels_pii: score += 2
        if self.data_classification in ["Confidential", "Restricted"]: score +=1
        return min(score, 10)

class BuiltInThreatEngine:
    def __init__(self):
        self.logger = getLogger("builtin_threat_engine")
        self.stride_mapping = {
            ElementType.actor: [ThreatType.spoofing, ThreatType.repudiation],
            ElementType.process: [ThreatType.tampering, ThreatType.information_disclosure,
                                  ThreatType.denial_of_service, ThreatType.elevation_of_privilege],
            ElementType.server: [ThreatType.tampering, ThreatType.information_disclosure,
                                 ThreatType.denial_of_service, ThreatType.elevation_of_privilege],
            ElementType.datastore: [ThreatType.tampering, ThreatType.information_disclosure, ThreatType.denial_of_service],
            ElementType.database: [ThreatType.tampering, ThreatType.information_disclosure, ThreatType.denial_of_service],
            ElementType.boundary: [ThreatType.spoofing, ThreatType.tampering],
            ElementType.external: [ThreatType.spoofing, ThreatType.repudiation],
            ElementType.user: [ThreatType.spoofing, ThreatType.repudiation]
        }
    @safe_execute
    def analyze_element(self, element_name: str, element_type: str, security_props: ElementSecurityProperties) -> List[ThreatInfo]:
        threats = []

        try:
            elem_type = ElementType(element_type.lower())
        except ValueError:
            elem_type = ElementType.process
        applicable_threats = self.stride_mapping.get(elem_type, [ThreatType.information_disclosure])
        for threat_type in applicable_threats:
            threat = self._create_threat(element_name, elem_type, threat_type, security_props)
            if threat:
                threats.append(threat)
        return threats
    
    def create_threat(self, element_name: str, element_type: ElementType, threat_type: ThreatType, security_props: ElementSecurityProperties) -> Optional[ThreatInfo]:
        threat_id = f"T{hash(f'{element_name}{threat_type.value}')%1000:03d}"
        severity = self._calculate_severity(threat_type, security_props)
        description, condition = self._get_threat_details(element_type, threat_type, security_props)
        mitigations = self._get_mitigations(threat_type, element_type)
        likelihood = self._calculate_likelihood(threat_type, security_props)
        
        return ThreatInfo(
            id=threat_id,
            element_name=element_name,
            element_type=element_type.value,
            threat_type=threat_type.value,
            severity=severity,
            description=description,
            condition=condition,
            likelihood=likelihood,
            impact=self._calculate_impact(threat_type, security_props),
            mitigations=mitigations,
        )
    
    def calculate_severity(self, threat_type:ThreatType, security_props: ElementSecurityProperties) -> str:
        base_severity = {
            ThreatType.spoofing: 2,
            ThreatType.tampering: 3,
            ThreatType.repudiation: 1,
            ThreatType.information_disclosure: 3,
            ThreatType.denial_of_service: 2,
            ThreatType.elevation_of_privilege: 4
        }
        severity_score = base_severity.get(threat_type, 2)
        
        risk_score = security_props.get_risk_score()
        if risk_score >= 7:
            severity_score += 1
        if risk_score <= 3:
            severity_score -= 1
        
        if security_props.handles_pii or security_props.data_classification in ["Confidential", "Restricted"]:
            severity_score += 1
        if security_props.is_internet_facing:
            severity_score += 1
        if severity_score >= 4:
            return SeverityLevel.crit.value
        elif severity_score >= 3:
            return SeverityLevel.high.value
        elif severity_score >= 2:
            return SeverityLevel.medium.value
        else:
            return SeverityLevel.low.value
    
    def calculate_likelihood(self, threat_type: ThreatType, security_props: ElementSecurityProperties) -> str:
        if security_props.is_internet_facing:
            return "High"
        elif security_props.get_risk_score() >= 6:
            return "Medium"
        else:
            return "Low"
    
    def calculate_impact(self, threat_type: ThreatType, security_props: ElementSecurityProperties) -> str:
        if security_props.handles_pii or security_props.data_classification in ["Confidential", "Restricted"]:
            return "High"
        elif threat_type in [ThreatType.information_disclosure, ThreatType.elevation_of_privilege]:
            return "Medium"
        else:
            return "Low"
    
    def get_threat_details(self, element_type: ElementType, threat_type: ThreatType, security_props: ElementSecurityProperties) -> Tuple[str, str]:
        descriptions = {
            (ElementType.actor, ThreatType.spoofing): (
                "An attacker could impersonate this user or system!",
                "No strong authentication mechanism is in place."
            ),
            (ElementType.process, ThreatType.tampering): (
                "Process data or code could be modified by an attacker!"
                "Insufficient integrity protection mechanisms."
            ),
            (ElementType.datastore, ThreatType.information_disclosure): (
                "Sensitive data could be accessed by unauthorized parties!"
                "Inadequate acess controls or encryption."
            ),
            (ElementType.server, ThreatType.denial_of_service): (
                "Server availability could be comprised by resource exhaustion!"
                "No rate limiting or DDoS protection is in place."
            )
        }
        key = (element_type, threat_type)
        if key in descriptions:
            return descriptions[key]
        
        generic_descriptions = {
            ThreatType.spoofing: (
                f"Identity spoofing attack against {element_type.value}.",
                "eak or missing authentication controls."
            ),
            ThreatType.tampering: (
                f"Data or system tampering attack against {element_type.value}.",
                "Insufficient integrity protection."
            ),
            ThreatType.repudiation: (
                f"Actions could be denied or disputed by {element_type.value}",
                "Inadequate logging and audit trails."
            ),
            ThreatType.information_disclosure: (
                f"Sensitive information could be exposed from {element_type.value}."
                "Weak access controls or encryption."
            ),
            ThreatType.denial_of_service: (
                f"Service availability could be compromised for {element_type.value}",
                "No protection against resource exhaustion"
            ),
            ThreatType.elevation_of_privilege: (
                f"Attacker could gain elevated privileges on {element_type.value}",
                "Insufficient privilege management"
            )
        }
        return generic_descriptions.get(threat_type, ("Unknown Threat", "Unknown condition"))
    def get_mitigations(self, threat_type: ThreatType, element_type: ElementType) -> List[str]:
        mitigations = {
            ThreatType.spoofing: [
                "Implement strong authentication (multi-factor preferred)",
                "Use digital certificates for system authentication",
                "Enabel mutual authentication for system-to-system communication",
                "Implement account lockout policies"
            ],
            ThreatType.tampering: [
                "Implement digital signatures for data integrity",
                "Use secure communication protocols (TLS 1.3)",
                "Enable file integrity monitoring",
                "Implement access controls and privilege separation"
            ],
            ThreatType.repudiation: [
                "Implement comprehensive audit logging",
                "Use digital signatures for non-repudiation",
                "Enable secure time stamping",
                "Implement log integrity protection"
            ],
            ThreatType.information_disclosure: [
                "Encrypt sensitive data at rest and in transit",
                "Implement proper access controls (principle of least privilege)",
                "Use data loss prevention (DLP) tools",
                "Regular security assessments and penetration testing"
            ],
            ThreatType.denial_of_service: [
                "Implement rate limiting and throttling",
                "Use load balancing and redundancy",
                "Deply DDoS protection services",
                "Implement resource monitoring and alerting"
            ],
            ThreatType.elevation_of_privilege: [
                "Implement principle of least privilege",
                "Use role-based access control (RBAC)",
                "Regular privilege reviews and access certification",
                "Implement privilege escalation and monitoring"
            ]
        }
        base_mitigations = mitigations.get(threat_type, ["Review and implement appropriate security controls"])
        if element_type == ElementType.datastore:
            base_mitigations.extend(["Database access controls", "Data encryption", "Database activity monitoring"])
        elif element_type == ElementType.server:
            base_mitigations.extend(["Server hardening", "Security patches", "Host-based intrusion detection"])
        return base_mitigations[:4]
class ThreatModel:
    def __init__(self, name: str = "SADB Threat Model"):
        self.name = name
        self.logger = getLogger("threat_model")
        self.shapes = []
        self.connectors = []
        self.threats = []
        self.created_at = datetime.now()
        self.builtin_engine = BuiltInThreatEngine()
        self.pytm_integration = None
        if pytm_available:
            try:
                self.pytm_integration = PyTMAdapter()
                self.logger.info("PyTM integration enabled")
            except Exception as e:
                self.logger.warning(f"PyTM integration failed! Message: {e}")
    @gui_safe_execute
    def add_shape(self, shape):
        with erorrHandler("add shape to threat model", self.logger):
            if shape not in self.shapes:
                self.shapes.append(shape)
                self.logger.debug(f"Added shape: {getattr(shape, 'label', 'unlabeled')}")
    @gui_safe_execute
    def add_connector(self, connector):
        with erorrHandler("add connector to threat model", self.logger):
            if connector not in self.connectors:
                self.connectors.append(connector)
                self.logger.debug("Added connector")
    @gui_safe_execute
    def extract_security_propertiess(self, shape) -> ElementSecurityProperties:
        metadata = getattr(shape, 'metadata', {})
        security = metadata.get('security', {})
        technical = metadata.get('technical', {})
        trust = metadata.get('trust', {})

        return ElementSecurityProperties(
            has_authentication=security.get('authentication', 'None') != 'None',
            has_authorization=security.get('authorization', 'None') != 'None',
            has_encrypted_transit=security.get('encryption_transit', 'None') != 'None',
            has_encryption_rest=security.get('encryption_rest', 'None') != 'None',
            has_input_validation=trust.get('logging_enabled', False),
            has_monitoring=trust.get('monitoring_enabled', False),
            is_internet_facing=trust.get('network_zone', '')== 'Internet',
            handels_pii=security.get('data_classification', 'Public') in ['Confidential', 'Restricted'],
            data_classification=security.get('data_classification', 'Public'),
            trust_level=trust.get('trust_level', 'Low'),
        )
    def run_threat_analysis(self) -> List[ThreatInfo]:
        with erorrHandler("run threat analysis", self.logger):
            self.threats.clear()

            if self.pytm_integration and PYTM_AVAILABLE:
                try:
                    pytm_threats = self.pytm_integration.analyze_threats(self.shapes, self.connectors)
                    self.threats.extend(pytm_threats)
                    self.logger.info(f"PyTM analysis completed: {len(pytm_threats)} threats found")
                except Exception as e:
                    self.logger.warning(f"PyTM analysis failed, falling back to builtin: {e}")
            
           # built in type shit
            if not self.threats:  ##
                for shape in self.shapes:
                    element_name = getattr(shape, 'label', f'Element_{id(shape)}')
                    element_type = getattr(shape, 'shape_subtype', getattr(shape, 'item_type', 'process'))
                    security_props = self.extract_security_properties(shape)
                    shape_threats = self.builtin_engine.analyze_element(element_name, element_type, security_props)
                    self.threats.extend(shape_threats)
                self.logger.info(f"Builtin analysis completed: {len(self.threats)} threats found")
            self._analyze_dataflow_threats()
            return self.threats
    def _analyze_dataflow_threats(self):
        """Analyze threats specific to data flows"""
        for connector in self.connectors:
            try:
                start_shape = getattr(connector, 'start_shape', None)
                end_shape = getattr(connector, 'end_shape', None)
                
                if start_shape and end_shape:
                    start_name = getattr(start_shape, 'label', 'Unknown')
                    end_name = getattr(end_shape, 'label', 'Unknown')
                
                    connector_metadata = getattr(connector, 'metadata', {})
                    if not connector_metadata.get('encrypted', False):
                        threat = ThreatInfo(
                            id=f"DF{hash(f'{start_name}{end_name}') % 1000:03d}",
                            element_name=f"{start_name} -> {end_name}",
                            element_type="dataflow",
                            threat_type="Information Disclosure",
                            severity="Medium",
                            description="Unencrypted data flow could expose sensitive information",
                            condition="Data transmitted without encryption",
                            mitigations=["Implement TLS encryption", "Use VPN for internal communications"]
                        )
                        self.threats.append(threat)
            
            except Exception as e:
                self.logger.error(f"Failed to analyze dataflow threat: {e}")
    
    @safe_execute
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of threat analysis results"""
        if not self.threats:
            return {"total": 0, "by_severity": {}, "by_type": {}}
        
        by_severity = {}
        by_type = {}
        
        for threat in self.threats:
            severity = threat.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1
            threat_type = threat.threat_type
            by_type[threat_type] = by_type.get(threat_type, 0) + 1
        return {
            "total": len(self.threats),
            "by_severity": by_severity,
            "by_type": by_type,
            "elements_analyzed": len(self.shapes),
            "dataflows_analyzed": len(self.connectors)
        }
    
    @safe_execute
    def export_report(self, file_path: str, format: str = "json"):
        """Export threat analysis report"""
        with erorrHandler("export threat report", self.logger):
            summary = self.get_threat_summary()
            
            report_data = {
                "metadata": {
                    "model_name": self.name,
                    "generated_at": datetime.now().isoformat(),
                    "tool": "Pygram Threat Modeler",
                    "pytm_enabled": PYTM_AVAILABLE,
                    "analysis_engine": "PyTM" if (self.pytm_integration and PYTM_AVAILABLE) else "Built-in STRIDE"
                },
                "summary": summary,
                "threats": [threat.to_dict() for threat in self.threats],
                "recommendations": self._generate_recommendations()
            }
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            self.logger.info(f"Report exported to {file_path}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate high-level security recommendations"""
        if not self.threats:
            return ["Run threat analysis to get recommendations"]
        
        recommendations = []
        summary = self.get_threat_summary()
        
        high_severity = summary["by_severity"].get("High", 0) + summary["by_severity"].get("Critical", 0)
        if high_severity > 0:
            recommendations.append(f"Address {high_severity} high/critical severity threats immediately")
        
        threat_types = summary["by_type"]
        if threat_types.get("Spoofing", 0) > 0:
            recommendations.append("Implement strong authentication mechanisms across all components")
        
        if threat_types.get("Information Disclosure", 0) > 0:
            recommendations.append("Review and strengthen data protection and access controls")
        
        if threat_types.get("Tampering", 0) > 0:
            recommendations.append("Implement data integrity protection and secure communications")
        
        if not recommendations:
            recommendations.append("Continue monitoring and regular security assessments")
        
        return recommendations


class PyTMAdapter:
    """Adapter for PyTM integration when available"""
    
    def __init__(self):
        if not PYTM_AVAILABLE:
            raise ImportError("PyTM not available")
        self.logger = getLogger("pytm_adapter")
    
    def analyze_threats(self, shapes, connectors) -> List[ThreatInfo]:
        """Convert shapes to PyTM model and run analysis"""
        self.logger.info("PyTM adapter called (implementation pending)")
        return []
def create_threat_model_from_shapes(shapes, connectors=None, name="Diagram Threat Model") -> ThreatModel:
    """Create threat model from Pygram shapes"""
    tm = ThreatModel(name)
    for shape in shapes:
        tm.add_shape(shape)
    if connectors:
        for connector in connectors:
            tm.add_connector(connector)
    return tm
def quick_threat_analysis(shapes, connectors=None) -> Tuple[List[ThreatInfo], Dict[str, Any]]:
    """Quick threat analysis returning threats and summary"""
    tm = create_threat_model_from_shapes(shapes, connectors)
    threats = tm.run_threat_analysis()
    summary = tm.get_threat_summary()
    return threats, summary