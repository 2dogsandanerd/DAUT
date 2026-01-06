"""
Modul zur Bewertung der Qualität von generierter Dokumentation
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class QualityScore:
    """Datenklasse für die Qualitätseinschätzung"""
    overall_score: float  # 0.0 - 1.0
    detailed_scores: Dict[str, float]  # Detaillierte Bewertungen für verschiedene Aspekte
    feedback: List[str]  # Konkrete Feedbackpunkte
    suggestions: List[str]  # Verbesserungsvorschläge


class DocumentationQualityEvaluator:
    """Bewertungssystem für die Qualität von generierter Dokumentation"""
    
    def __init__(self):
        self.criteria_weights = {
            'completeness': 0.3,      # Vollständigkeit der Informationen
            'clarity': 0.25,          # Klarheit und Verständlichkeit
            'structure': 0.2,         # Struktur und Formatierung
            'accuracy': 0.15,         # Genauigkeit der Informationen
            'examples': 0.1           # Beispiele und Anwendungsfälle
        }
    
    def evaluate_documentation(self, documentation: str, code_element: Optional[object] = None) -> QualityScore:
        """
        Bewertet die Qualität einer Dokumentation
        
        Args:
            documentation: Die zu bewertende Dokumentation
            code_element: Optional das zugehörige Code-Element für Kontext
            
        Returns:
            QualityScore: Bewertungsergebnis
        """
        if not documentation or documentation.strip() == "":
            return QualityScore(
                overall_score=0.0,
                detailed_scores={key: 0.0 for key in self.criteria_weights.keys()},
                feedback=["Dokumentation ist leer"],
                suggestions=["Fügen Sie eine Beschreibung hinzu", "Fügen Sie Parameter und Rückgabewerte hinzu"]
            )
        
        detailed_scores = {}
        feedback = []
        suggestions = []
        
        # Vollständigkeit prüfen
        completeness_score, completeness_feedback, completeness_suggestions = self._evaluate_completeness(
            documentation, code_element
        )
        detailed_scores['completeness'] = completeness_score
        feedback.extend(completeness_feedback)
        suggestions.extend(completeness_suggestions)
        
        # Klarheit prüfen
        clarity_score, clarity_feedback, clarity_suggestions = self._evaluate_clarity(documentation)
        detailed_scores['clarity'] = clarity_score
        feedback.extend(clarity_feedback)
        suggestions.extend(clarity_suggestions)
        
        # Struktur prüfen
        structure_score, structure_feedback, structure_suggestions = self._evaluate_structure(documentation)
        detailed_scores['structure'] = structure_score
        feedback.extend(structure_feedback)
        suggestions.extend(structure_suggestions)
        
        # Genauigkeit prüfen (vereinfacht)
        accuracy_score, accuracy_feedback, accuracy_suggestions = self._evaluate_accuracy(
            documentation, code_element
        )
        detailed_scores['accuracy'] = accuracy_score
        feedback.extend(accuracy_feedback)
        suggestions.extend(accuracy_suggestions)
        
        # Beispiele prüfen
        examples_score, examples_feedback, examples_suggestions = self._evaluate_examples(documentation)
        detailed_scores['examples'] = examples_score
        feedback.extend(examples_feedback)
        suggestions.extend(examples_suggestions)
        
        # Gesamtbewertung berechnen
        overall_score = sum(
            detailed_scores[criterion] * self.criteria_weights[criterion]
            for criterion in self.criteria_weights
        )
        
        return QualityScore(
            overall_score=overall_score,
            detailed_scores=detailed_scores,
            feedback=feedback,
            suggestions=suggestions
        )
    
    def _evaluate_completeness(self, documentation: str, code_element: Optional[object]) -> Tuple[float, List[str], List[str]]:
        """Bewertet die Vollständigkeit der Dokumentation"""
        feedback = []
        suggestions = []
        
        # Prüfen auf grundlegende Abschnitte
        has_description = any(keyword in documentation.lower() for keyword in ['beschreibung', 'description', 'zweck', 'purpose'])
        has_parameters = any(keyword in documentation.lower() for keyword in ['parameter', 'parameters', 'args', 'arguments'])
        has_return = any(keyword in documentation.lower() for keyword in ['return', 'returns', 'rückgabe', 'rueckgabe'])
        
        score = 0.0
        checks = [has_description, has_parameters, has_return]
        completed_checks = sum(checks)
        
        if completed_checks == 3:
            score = 1.0
        elif completed_checks == 2:
            score = 0.7
        elif completed_checks == 1:
            score = 0.4
        else:
            score = 0.1
        
        # Feedback und Vorschläge basierend auf fehlenden Teilen
        if not has_description:
            feedback.append("Keine Beschreibung gefunden")
            suggestions.append("Fügen Sie eine klare Beschreibung des Elements hinzu")
        
        if not has_parameters and code_element and hasattr(code_element, 'parameters') and code_element.parameters:
            feedback.append("Keine Parameter-Dokumentation gefunden")
            suggestions.append("Dokumentieren Sie die Parameter des Elements")
        
        if not has_return and code_element and hasattr(code_element, 'return_type') and code_element.return_type:
            feedback.append("Keine Rückgabewert-Dokumentation gefunden")
            suggestions.append("Dokumentieren Sie den Rückgabewert des Elements")
        
        return score, feedback, suggestions
    
    def _evaluate_clarity(self, documentation: str) -> Tuple[float, List[str], List[str]]:
        """Bewertet die Klarheit der Dokumentation"""
        feedback = []
        suggestions = []
        
        # Einfache Klarheitsprüfungen
        word_count = len(documentation.split())
        sentence_count = len(re.split(r'[.!?]+', documentation))
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # Prüfen auf zu lange Sätze (weniger klar)
        if avg_sentence_length > 25:
            clarity_score = 0.5
            feedback.append("Sätze sind zu lang und komplex")
            suggestions.append("Verwenden Sie kürzere, einfachere Sätze")
        elif avg_sentence_length < 5:
            clarity_score = 0.6
            feedback.append("Sätze sind zu kurz")
            suggestions.append("Verwenden Sie etwas längere Sätze für bessere Ausdruckskraft")
        else:
            clarity_score = 1.0
        
        # Prüfen auf Fachjargon oder unklare Begriffe
        # (vereinfachte Prüfung - in der Realität komplexer)
        complex_indicators = ['kann', 'wird', 'sollte', 'muss', 'eventuell', 'vielleicht']
        complex_count = sum(1 for indicator in complex_indicators if indicator in documentation.lower())
        
        if complex_count > 3:
            clarity_score *= 0.8
            feedback.append("Verwendung von unklaren Formulierungen")
            suggestions.append("Verwenden Sie präzisere und direktere Sprache")
        
        return clarity_score, feedback, suggestions
    
    def _evaluate_structure(self, documentation: str) -> Tuple[float, List[str], List[str]]:
        """Bewertet die Struktur der Dokumentation"""
        feedback = []
        suggestions = []
        
        # Prüfen auf Markdown-Struktur
        has_headers = '#' in documentation
        has_lists = any(char in documentation for char in ['-', '*', '1.', '2.'])
        has_code_blocks = '```' in documentation or '`' in documentation
        
        score = 0.0
        structure_elements = [has_headers, has_lists, has_code_blocks]
        structure_count = sum(structure_elements)
        
        if structure_count >= 2:
            score = 1.0
        elif structure_count == 1:
            score = 0.6
        else:
            score = 0.2
            feedback.append("Keine klare Struktur erkannt")
            suggestions.extend([
                "Verwenden Sie Überschriften für verschiedene Abschnitte",
                "Verwenden Sie Listen für Parameter oder Optionen",
                "Verwenden Sie Code-Blöcke für Beispiele"
            ])
        
        if not has_headers:
            feedback.append("Keine Überschriften gefunden")
            suggestions.append("Strukturieren Sie die Dokumentation mit Überschriften")
        
        if not has_lists:
            feedback.append("Keine Listen für Parameter oder Rückgabewerte")
            suggestions.append("Verwenden Sie Listen für strukturierte Informationen")
        
        return score, feedback, suggestions
    
    def _evaluate_accuracy(self, documentation: str, code_element: Optional[object]) -> Tuple[float, float, List[str], List[str]]:
        """Bewertet die Genauigkeit der Dokumentation (vereinfacht)"""
        feedback = []
        suggestions = []
        
        # In einer vollständigen Implementierung würde man die Dokumentation mit dem 
        # tatsächlichen Code vergleichen, um Übereinstimmungen zu prüfen
        # Für diese Implementierung machen wir eine vereinfachte Prüfung
        
        # Prüfen ob die Dokumentation ausreichend detailliert ist
        if len(documentation) < 50:
            accuracy_score = 0.5
            feedback.append("Dokumentation ist sehr kurz")
            suggestions.append("Fügen Sie mehr Detailinformationen hinzu")
        else:
            accuracy_score = 0.8  # Annahme: längere Dokumentation ist tendenziell genauer
        
        # Prüfen auf allgemeine Formulierungen
        generic_terms = ['funktion', 'methode', 'klasse', 'element', 'etwas']
        generic_count = sum(1 for term in generic_terms if term in documentation.lower())
        
        if generic_count > 3:
            accuracy_score *= 0.8
            feedback.append("Verwendung allgemeiner Begriffe")
            suggestions.append("Verwenden Sie spezifischere Begriffe")
        
        return accuracy_score, feedback, suggestions
    
    def _evaluate_examples(self, documentation: str) -> Tuple[float, List[str], List[str]]:
        """Bewertet die Beispiele in der Dokumentation"""
        feedback = []
        suggestions = []
        
        # Prüfen auf Beispiele
        has_examples = any(keyword in documentation.lower() for keyword in ['beispiel', 'example', 'zeigt', 'zeigt wie'])
        has_code_examples = '```' in documentation or any(lang in documentation.lower() for lang in ['python', 'js', 'javascript', 'code'])
        
        score = 0.0
        if has_examples or has_code_examples:
            score = 1.0
        else:
            score = 0.2
            feedback.append("Keine Beispiele gefunden")
            suggestions.append("Fügen Sie praktische Beispiele hinzu")
        
        if has_examples and not has_code_examples:
            feedback.append("Keine Code-Beispiele gefunden")
            suggestions.append("Fügen Sie konkrete Code-Beispiele hinzu")
        
        return score, feedback, suggestions

    def get_quality_thresholds(self) -> Dict[str, float]:
        """Gibt die Schwellenwerte für verschiedene Qualitätsstufen zurück"""
        return {
            'excellent': 0.9,
            'good': 0.7,
            'acceptable': 0.5,
            'poor': 0.3
        }