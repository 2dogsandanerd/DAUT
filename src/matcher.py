from typing import List, Dict, Any
from src.models.element import CodeElement, DocElement
from src.matcher.advanced_matcher import AdvancedMatcherEngine

class MatcherEngine:
    def __init__(self):
        # Verwende den erweiterten Matcher für differenzierte Konfliktanalyse
        self.advanced_matcher = AdvancedMatcherEngine()

    def find_discrepancies(self, code_elements: List[CodeElement], doc_elements: List[DocElement]) -> Dict[str, Any]:
        """Findet Diskrepanzen zwischen Code und Dokumentation mit differenzierter Analyse"""
        # Verwende den erweiterten Matcher
        return self.advanced_matcher.find_discrepancies(code_elements, doc_elements)

    def get_resolution_recommendations(self, discrepancies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gibt Empfehlungen für die Lösung von Konflikten"""
        return self.advanced_matcher.get_resolution_recommendations(discrepancies)