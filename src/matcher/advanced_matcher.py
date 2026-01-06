"""
Erweiterter Konfliktlösungsmechanismus für Diskrepanzen zwischen Code und Dokumentation
"""
from typing import Dict, List, Any, Optional, Tuple
from src.models.element import CodeElement, DocElement
from enum import Enum
import difflib


class ConflictType(Enum):
    """Aufzählung verschiedener Arten von Konflikten"""
    UNDOCUMENTED_CODE = "undocumented_code"
    OUTDATED_DOCUMENTATION = "outdated_documentation"
    MISMATCHED_PARAMETERS = "mismatched_parameters"
    MISMATCHED_RETURN_TYPE = "mismatched_return_type"
    MISMATCHED_SIGNATURE = "mismatched_signature"
    MISMATCHED_DESCRIPTION = "mismatched_description"


class ConflictResolutionStrategy(Enum):
    """Aufzählung verschiedener Konfliktlösungsstrategien"""
    UPDATE_DOCUMENTATION_FROM_CODE = "update_doc_from_code"
    UPDATE_CODE_FROM_DOCUMENTATION = "update_code_from_doc"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    MARK_AS_OBSOLETE = "mark_as_obsolete"
    GENERATE_NEW_DOCUMENTATION = "generate_new_documentation"


class ConflictResolutionResult:
    """Ergebnis einer Konfliktlösung"""
    def __init__(self, 
                 resolution_strategy: ConflictResolutionStrategy,
                 confidence: float,
                 suggested_changes: Optional[Dict[str, Any]] = None,
                 reason: str = ""):
        self.resolution_strategy = resolution_strategy
        self.confidence = confidence  # 0.0 - 1.0
        self.suggested_changes = suggested_changes or {}
        self.reason = reason


class AdvancedMatcherEngine:
    """Erweiterter Matcher mit differenzierter Konfliktlösung"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
    
    def find_discrepancies(self, code_elements: List[CodeElement], doc_elements: List[DocElement]) -> Dict[str, Any]:
        """Findet Diskrepanzen zwischen Code und Dokumentation mit differenzierter Analyse"""
        discrepancies = {
            'undocumented_code': [],
            'outdated_documentation': [],
            'mismatched_elements': [],
            'conflict_analysis': []
        }

        # Erstelle Lookup-Tabellen für einfachen Zugriff
        code_lookup = {elem.name: elem for elem in code_elements}
        doc_lookup = {elem.name: elem for elem in doc_elements}

        # Finde undokumentierten Code
        for code_elem in code_elements:
            if code_elem.name not in doc_lookup:
                # Ausschließlich nach Funktion, Klasse oder API-Endpunkt suchen
                if code_elem.type and code_elem.type.value in ['function', 'class', 'api_endpoint']:
                    discrepancies['undocumented_code'].append(code_elem)

        # Finde veraltete Dokumentation
        for doc_elem in doc_elements:
            if doc_elem.name not in code_lookup:
                discrepancies['outdated_documentation'].append(doc_elem)

        # Finde Diskrepanzen zwischen vorhandenen Elementen mit differenzierter Analyse
        for name in set(code_lookup.keys()) & set(doc_lookup.keys()):
            code_elem = code_lookup[name]
            doc_elem = doc_lookup[name]

            # Führe eine detaillierte Konfliktanalyse durch
            conflict_analysis = self._analyze_conflict(code_elem, doc_elem)
            
            if conflict_analysis:
                discrepancies['mismatched_elements'].append({
                    'code': code_elem,
                    'documentation': doc_elem,
                    'conflict_analysis': conflict_analysis
                })
                
                discrepancies['conflict_analysis'].append({
                    'element_name': name,
                    'conflict_analysis': conflict_analysis
                })

        return discrepancies

    def _analyze_conflict(self, code_elem: CodeElement, doc_elem: DocElement) -> List[Dict[str, Any]]:
        """Führt eine detaillierte Konfliktanalyse durch"""
        conflicts = []
        
        # 1. Parameter-Konflikte
        param_conflict = self._analyze_parameter_conflicts(code_elem, doc_elem)
        if param_conflict:
            conflicts.append(param_conflict)
        
        # 2. Rückgabetyp-Konflikte
        return_conflict = self._analyze_return_type_conflicts(code_elem, doc_elem)
        if return_conflict:
            conflicts.append(return_conflict)
        
        # 3. Signatur-Konflikte
        signature_conflict = self._analyze_signature_conflicts(code_elem, doc_elem)
        if signature_conflict:
            conflicts.append(signature_conflict)
        
        # 4. Beschreibungs-Konflikte
        description_conflict = self._analyze_description_conflicts(code_elem, doc_elem)
        if description_conflict:
            conflicts.append(description_conflict)
        
        return conflicts

    def _analyze_parameter_conflicts(self, code_elem: CodeElement, doc_elem: DocElement) -> Optional[Dict[str, Any]]:
        """Analysiert Parameter-Konflikte"""
        if not code_elem.parameters or not doc_elem.content:
            return None
        
        # Extrahiere Parameter aus der Dokumentation
        doc_params = self._extract_parameters_from_doc(doc_elem.content)
        
        # Vergleiche Parameterlisten
        code_param_names = [p.get('name', '') for p in code_elem.parameters if isinstance(p, dict)]
        doc_param_names = [p.get('name', '') for p in doc_params if isinstance(p, dict)]
        
        missing_in_doc = set(code_param_names) - set(doc_param_names)
        extra_in_doc = set(doc_param_names) - set(code_param_names)
        
        if missing_in_doc or extra_in_doc:
            resolution = self._resolve_parameter_conflict(
                code_elem.parameters, doc_params, missing_in_doc, extra_in_doc
            )
            
            return {
                'conflict_type': ConflictType.MISMATCHED_PARAMETERS.value,
                'resolution': resolution,
                'details': {
                    'code_parameters': code_elem.parameters,
                    'doc_parameters': doc_params,
                    'missing_in_doc': list(missing_in_doc),
                    'extra_in_doc': list(extra_in_doc)
                }
            }
        
        return None

    def _analyze_return_type_conflicts(self, code_elem: CodeElement, doc_elem: DocElement) -> Optional[Dict[str, Any]]:
        """Analysiert Rückgabetyp-Konflikte"""
        if not code_elem.return_type or not doc_elem.content:
            return None
        
        # Extrahiere Rückgabetyp aus der Dokumentation
        doc_return_type = self._extract_return_type_from_doc(doc_elem.content)
        
        # Vergleiche Rückgabetypen
        if code_elem.return_type.lower() != doc_return_type.lower():
            resolution = self._resolve_return_type_conflict(code_elem.return_type, doc_return_type)
            
            return {
                'conflict_type': ConflictType.MISMATCHED_RETURN_TYPE.value,
                'resolution': resolution,
                'details': {
                    'code_return_type': code_elem.return_type,
                    'doc_return_type': doc_return_type
                }
            }
        
        return None

    def _analyze_signature_conflicts(self, code_elem: CodeElement, doc_elem: DocElement) -> Optional[Dict[str, Any]]:
        """Analysiert Signatur-Konflikte"""
        if not code_elem.signature or not doc_elem.content:
            return None
        
        # Berechne die Ähnlichkeit zwischen Code-Signatur und Dokumentation
        similarity = difflib.SequenceMatcher(
            None, 
            code_elem.signature.lower(), 
            doc_elem.content.lower()
        ).ratio()
        
        if similarity < self.confidence_thresholds['medium']:
            resolution = self._resolve_signature_conflict(similarity)
            
            return {
                'conflict_type': ConflictType.MISMATCHED_SIGNATURE.value,
                'resolution': resolution,
                'details': {
                    'code_signature': code_elem.signature,
                    'doc_content': doc_elem.content[:200] + "..." if len(doc_elem.content) > 200 else doc_elem.content,
                    'similarity': similarity
                }
            }
        
        return None

    def _analyze_description_conflicts(self, code_elem: CodeElement, doc_elem: DocElement) -> Optional[Dict[str, Any]]:
        """Analysiert Beschreibungs-Konflikte"""
        if not code_elem.docstring or not doc_elem.content:
            return None
        
        # Berechne die Ähnlichkeit zwischen Docstring und Dokumentation
        similarity = difflib.SequenceMatcher(
            None, 
            code_elem.docstring.lower(), 
            doc_elem.content.lower()
        ).ratio()
        
        if similarity < self.confidence_thresholds['medium']:
            resolution = self._resolve_description_conflict(similarity)
            
            return {
                'conflict_type': ConflictType.MISMATCHED_DESCRIPTION.value,
                'resolution': resolution,
                'details': {
                    'code_docstring': code_elem.docstring,
                    'doc_content': doc_elem.content,
                    'similarity': similarity
                }
            }
        
        return None

    def _extract_parameters_from_doc(self, doc_content: str) -> List[Dict[str, str]]:
        """Extrahiert Parameter aus der Dokumentation"""
        params = []
        
        # Einfache Extraktion von Parametern aus der Dokumentation
        # In einer vollständigen Implementierung würde dies komplexere Parsing-Logik verwenden
        lines = doc_content.split('\n')
        for line in lines:
            # Suche nach gängigen Parametern-Mustern
            if any(keyword in line.lower() for keyword in ['param', 'parameter', 'args', 'arguments']):
                # Extrahiere Parameternamen (vereinfacht)
                import re
                param_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', line)
                for match in param_matches:
                    if len(match) > 1 and not any(keyword in match.lower() for keyword in ['param', 'parameter', 'args', 'arguments']):
                        params.append({'name': match})
        
        return params

    def _extract_return_type_from_doc(self, doc_content: str) -> str:
        """Extrahiert den Rückgabetyp aus der Dokumentation"""
        # Einfache Extraktion des Rückgabetyps aus der Dokumentation
        lines = doc_content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['return', 'returns', 'rueckgabe']):
                # Extrahiere möglichen Typ (vereinfacht)
                import re
                type_matches = re.findall(r':\s*([a-zA-Z][a-zA-Z0-9_]*)', line)
                if type_matches:
                    return type_matches[0]
        
        return "unknown"

    def _resolve_parameter_conflict(self, code_params: List[Dict], doc_params: List[Dict], 
                                   missing_in_doc: set, extra_in_doc: set) -> ConflictResolutionResult:
        """Löst Parameter-Konflikte"""
        if missing_in_doc and not extra_in_doc:
            # Parameter fehlen in der Dokumentation - aktualisiere Dokumentation
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.9,
                suggested_changes={'missing_parameters': list(missing_in_doc)},
                reason="Parameter existieren im Code, fehlen aber in der Dokumentation"
            )
        elif extra_in_doc and not missing_in_doc:
            # Parameter existieren in der Dokumentation, fehlen aber im Code - veraltete Dokumentation
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.8,
                suggested_changes={'extra_parameters': list(extra_in_doc)},
                reason="Parameter existieren in der Dokumentation, fehlen aber im Code"
            )
        else:
            # Komplexerer Konflikt - manuelle Überprüfung erforderlich
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.MANUAL_REVIEW_REQUIRED,
                confidence=0.4,
                suggested_changes={'missing_parameters': list(missing_in_doc), 'extra_parameters': list(extra_in_doc)},
                reason="Komplexer Parameter-Konflikt - manuelle Überprüfung erforderlich"
            )

    def _resolve_return_type_conflict(self, code_return_type: str, doc_return_type: str) -> ConflictResolutionResult:
        """Löst Rückgabetyp-Konflikte"""
        if code_return_type.lower() == "none" and doc_return_type.lower() != "none":
            # Code gibt nichts zurück, Dokumentation sagt etwas anderes
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.85,
                suggested_changes={'correct_return_type': code_return_type},
                reason="Code gibt None zurück, Dokumentation zeigt anderen Typ"
            )
        elif doc_return_type.lower() == "unknown":
            # Dokumentation hat keinen Rückgabetyp - aktualisiere aus Code
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.9,
                suggested_changes={'return_type': code_return_type},
                reason="Dokumentation hat keinen Rückgabetyp, Code zeigt Typ"
            )
        else:
            # Beide haben Typen, aber unterschiedliche - manuelle Überprüfung
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.MANUAL_REVIEW_REQUIRED,
                confidence=0.3,
                suggested_changes={'code_return_type': code_return_type, 'doc_return_type': doc_return_type},
                reason="Unterschiedliche Rückgabetypen in Code und Dokumentation - manuelle Überprüfung erforderlich"
            )

    def _resolve_signature_conflict(self, similarity: float) -> ConflictResolutionResult:
        """Löst Signatur-Konflikte"""
        if similarity < self.confidence_thresholds['low']:
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.GENERATE_NEW_DOCUMENTATION,
                confidence=0.7,
                reason="Sehr geringe Ähnlichkeit zwischen Code-Signatur und Dokumentation - neue Dokumentation erforderlich"
            )
        elif similarity < self.confidence_thresholds['medium']:
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.6,
                reason="Geringe Ähnlichkeit zwischen Code-Signatur und Dokumentation - Dokumentation sollte aktualisiert werden"
            )
        else:
            # Hohe Ähnlichkeit - wahrscheinlich keine Konflikte
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.9,
                reason="Hohe Ähnlichkeit zwischen Code und Dokumentation - geringfügige Aktualisierungen erforderlich"
            )

    def _resolve_description_conflict(self, similarity: float) -> ConflictResolutionResult:
        """Löst Beschreibungs-Konflikte"""
        if similarity < self.confidence_thresholds['low']:
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.8,
                reason="Sehr geringe Ähnlichkeit zwischen Docstring und Dokumentation - Dokumentation sollte aktualisiert werden"
            )
        elif similarity < self.confidence_thresholds['medium']:
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.7,
                reason="Geringe Ähnlichkeit zwischen Docstring und Dokumentation - Dokumentation sollte aktualisiert werden"
            )
        else:
            # Hohe Ähnlichkeit - wahrscheinlich keine Konflikte
            return ConflictResolutionResult(
                resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
                confidence=0.95,
                reason="Hohe Ähnlichkeit zwischen Docstring und Dokumentation - keine wesentlichen Konflikte"
            )

    def get_resolution_recommendations(self, discrepancies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gibt Empfehlungen für die Lösung von Konflikten"""
        recommendations = []
        
        # Empfehlungen für dokumentierten Code
        for code_elem in discrepancies.get('undocumented_code', []):
            recommendations.append({
                'element_name': code_elem.name,
                'element_type': code_elem.type.value if code_elem.type else 'unknown',
                'resolution': ConflictResolutionStrategy.GENERATE_NEW_DOCUMENTATION.value,
                'confidence': 0.9,
                'reason': 'Element ist nicht dokumentiert',
                'suggested_action': 'Neue Dokumentation generieren'
            })
        
        # Empfehlungen für veraltete Dokumentation
        for doc_elem in discrepancies.get('outdated_documentation', []):
            recommendations.append({
                'element_name': doc_elem.name,
                'element_type': doc_elem.type.value if doc_elem.type else 'unknown',
                'resolution': ConflictResolutionStrategy.MARK_AS_OBSOLETE.value,
                'confidence': 0.8,
                'reason': 'Dokumentation existiert, aber kein entsprechender Code',
                'suggested_action': 'Als veraltet markieren'
            })
        
        # Empfehlungen für Diskrepanzen
        for mismatch in discrepancies.get('mismatched_elements', []):
            if 'conflict_analysis' in mismatch:
                for conflict in mismatch['conflict_analysis']:
                    recommendations.append({
                        'element_name': mismatch['code'].name,
                        'element_type': mismatch['code'].type.value if mismatch['code'].type else 'unknown',
                        'conflict_type': conflict['conflict_type'],
                        'resolution': conflict['resolution'].resolution_strategy.value,
                        'confidence': conflict['resolution'].confidence,
                        'reason': conflict['resolution'].reason,
                        'suggested_action': self._get_action_description(conflict['resolution'].resolution_strategy)
                    })
        
        return recommendations

    def _get_action_description(self, strategy: ConflictResolutionStrategy) -> str:
        """Gibt eine Beschreibung für eine Konfliktlösungsstrategie zurück"""
        descriptions = {
            ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE: "Dokumentation basierend auf Code aktualisieren",
            ConflictResolutionStrategy.UPDATE_CODE_FROM_DOCUMENTATION: "Code basierend auf Dokumentation aktualisieren",
            ConflictResolutionStrategy.MANUAL_REVIEW_REQUIRED: "Manuelle Überprüfung erforderlich",
            ConflictResolutionStrategy.MARK_AS_OBSOLETE: "Als veraltet markieren",
            ConflictResolutionStrategy.GENERATE_NEW_DOCUMENTATION: "Neue Dokumentation generieren"
        }
        return descriptions.get(strategy, "Unbekannte Strategie")