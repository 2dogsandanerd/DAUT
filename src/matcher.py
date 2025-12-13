from typing import List, Dict, Any
from src.models.element import CodeElement, DocElement

class MatcherEngine:
    def __init__(self):
        pass
    
    def find_discrepancies(self, code_elements: List[CodeElement], doc_elements: List[DocElement]) -> Dict[str, Any]:
        """Findet Diskrepanzen zwischen Code und Dokumentation"""
        discrepancies = {
            'undocumented_code': [],
            'outdated_documentation': [],
            'mismatched_elements': []
        }
        
        # Erstelle Lookup-Tabellen für einfachen Zugriff
        code_lookup = {elem.name: elem for elem in code_elements}
        doc_lookup = {elem.name: elem for elem in doc_elements}
        
        # Finde undokumentierten Code
        for code_elem in code_elements:
            if code_elem.name not in doc_lookup:
                # Ausschließlich nach Funktion, Klasse oder API-Endpunkt suchen
                if code_elem.type in ['function', 'class', 'api_endpoint']:
                    discrepancies['undocumented_code'].append(code_elem)
        
        # Finde veraltete Dokumentation
        for doc_elem in doc_elements:
            if doc_elem.name not in code_lookup:
                discrepancies['outdated_documentation'].append(doc_elem)
        
        # Finde Diskrepanzen zwischen vorhandenen Elementen
        for name in set(code_lookup.keys()) & set(doc_lookup.keys()):
            code_elem = code_lookup[name]
            doc_elem = doc_lookup[name]
            
            # Hier könnte die Logik für den Abgleich erweitert werden
            # z.B. Inhalt, Parameter, etc. vergleichen
            if self._is_mismatched(code_elem, doc_elem):
                discrepancies['mismatched_elements'].append({
                    'code': code_elem,
                    'documentation': doc_elem
                })
        
        return discrepancies
    
    def _is_mismatched(self, code_elem: CodeElement, doc_elem: DocElement) -> bool:
        """Prüft, ob Code-Element und Dokumentation nicht übereinstimmen"""
        # Prüfe auf verschiedene Arten von Diskrepanzen:

        # 1. Unterschiedliche Parameter
        if self._parameters_differ(code_elem, doc_elem):
            return True

        # 2. Unterschiedlicher Rückgabetyp
        if self._return_types_differ(code_elem, doc_elem):
            return True

        # 3. Docstring stark abweichend von Dokumentation
        if self._docstring_vs_doc_differ(code_elem, doc_elem):
            return True

        # 4. Unterschiedliche API-Informationen
        if code_elem.api_info and doc_elem.content and code_elem.api_info != doc_elem.content:
            return True

        # Wenn keine Diskrepanz gefunden wurde
        return False

    def _parameters_differ(self, code_elem: CodeElement, doc_elem: DocElement) -> bool:
        """Prüft, ob Parameter des Code-Elements von der Dokumentation abweichen"""
        # In einer kompletten Implementierung würde dies die Parameter
        # des Code-Elements mit denen in der Dokumentation vergleichen
        # Für den Moment eine einfache Heuristik basierend auf Anzahl
        if hasattr(code_elem, 'parameters') and code_elem.parameters:
            # Wenn Code Parameter hat aber Dokumentation erwähnt keine Parameter
            # könnte dies eine Diskrepanz sein (vereinfachte Heuristik)
            doc_content = getattr(doc_elem, 'content', '').lower()
            expected_param_count = len(code_elem.parameters) if code_elem.parameters else 0

            # Zähle Parametererwähnungen in der Dokumentation
            param_mentions = doc_content.count('parameter') + doc_content.count('param') + doc_content.count('arg')

            # Wenn Code Parameter hat aber Dokumentation keine erwähnt (vereinfachte Prüfung)
            return expected_param_count > 0 and param_mentions == 0
        return False

    def _return_types_differ(self, code_elem: CodeElement, doc_elem: DocElement) -> bool:
        """Prüft, ob der Rückgabetyp vom dokumentierten Wert abweicht"""
        code_return = getattr(code_elem, 'return_type', '')
        doc_content = getattr(doc_elem, 'content', '').lower()

        # Wenn Code einen Rückgabetyp hat, aber die Dokumentation nichts erwähnt
        if code_return and code_return.lower() != 'none':
            return 'return' not in doc_content and 'returns' not in doc_content and 'rueckgabe' not in doc_content
        return False

    def _docstring_vs_doc_differ(self, code_elem: CodeElement, doc_elem: DocElement) -> bool:
        """Prüft, ob der Docstring vom dokumentierten Inhalt abweicht"""
        code_docstring = getattr(code_elem, 'docstring', '')
        doc_content = getattr(doc_elem, 'content', '')

        # Einfache Ähnlichkeitsprüfung (kann verbessert werden mit semantischer Analyse)
        if code_docstring and doc_content:
            # Wenn Docstring und Dokumentation stark unterschiedlich sind
            # (vereinfachte Prüfung basierend auf Länge und Übereinstimmung)
            common_words = set(code_docstring.lower().split()) & set(doc_content.lower().split())
            if len(common_words) == 0 and len(code_docstring) > 20 and len(doc_content) > 20:
                return True
        return False