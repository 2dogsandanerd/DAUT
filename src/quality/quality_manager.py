"""
Modul zur Integration der Qualitätsevaluation in den Dokumentationsprozess
"""
from typing import List, Dict, Any, Optional
from src.quality.quality_evaluator import DocumentationQualityEvaluator, QualityScore
from src.models.element import CodeElement


class DocumentationQualityManager:
    """Verwaltet die Qualitätsevaluation von Dokumentation"""
    
    def __init__(self):
        self.evaluator = DocumentationQualityEvaluator()
        self.quality_threshold = 0.7  # Mindestqualitätsschwelle
    
    def evaluate_single_documentation(self, documentation: str, code_element: Optional[CodeElement] = None) -> QualityScore:
        """Bewertet eine einzelne Dokumentation"""
        return self.evaluator.evaluate_documentation(documentation, code_element)
    
    def evaluate_batch_documentation(self, documentation_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bewertet eine Liste von Dokumentationen
        
        Args:
            documentation_list: Liste von Dictionaries mit 'documentation' und optional 'code_element'
            
        Returns:
            Liste von Dictionaries mit Bewertungen
        """
        results = []
        
        for item in documentation_list:
            doc_text = item.get('documentation', '')
            code_elem = item.get('code_element')
            
            quality_score = self.evaluate_single_documentation(doc_text, code_elem)
            
            result = {
                'documentation': doc_text,
                'quality_score': quality_score,
                'is_acceptable': quality_score.overall_score >= self.quality_threshold
            }
            
            if code_elem:
                result['element_name'] = code_elem.name
            
            results.append(result)
        
        return results
    
    def filter_by_quality(self, documentation_list: List[Dict[str, Any]], min_score: float = None) -> List[Dict[str, Any]]:
        """
        Filtert Dokumentationen basierend auf der Qualität
        
        Args:
            documentation_list: Liste von Dokumentationen zum Filtern
            min_score: Mindestqualitätsschwelle (optional, verwendet Standardwert falls None)
            
        Returns:
            Gefilterte Liste von Dokumentationen
        """
        threshold = min_score if min_score is not None else self.quality_threshold
        
        filtered_docs = []
        for item in documentation_list:
            doc_text = item.get('documentation', '')
            code_elem = item.get('code_element')
            
            quality_score = self.evaluate_single_documentation(doc_text, code_elem)
            
            if quality_score.overall_score >= threshold:
                item['quality_score'] = quality_score
                filtered_docs.append(item)
        
        return filtered_docs
    
    def get_quality_report(self, documentation_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Erstellt einen Qualitätsbericht für eine Liste von Dokumentationen
        
        Args:
            documentation_list: Liste von Dokumentationen zum Bewerten
            
        Returns:
            Bericht mit Qualitätsstatistiken
        """
        if not documentation_list:
            return {
                'total_documents': 0,
                'average_score': 0.0,
                'acceptable_count': 0,
                'poor_count': 0,
                'quality_distribution': {}
            }
        
        scores = []
        for item in documentation_list:
            doc_text = item.get('documentation', '')
            code_elem = item.get('code_element')
            
            quality_score = self.evaluate_single_documentation(doc_text, code_elem)
            scores.append(quality_score.overall_score)
        
        # Kategorisieren der Bewertungen
        excellent = sum(1 for score in scores if score >= 0.9)
        good = sum(1 for score in scores if 0.7 <= score < 0.9)
        acceptable = sum(1 for score in scores if 0.5 <= score < 0.7)
        poor = sum(1 for score in scores if score < 0.5)
        
        return {
            'total_documents': len(scores),
            'average_score': sum(scores) / len(scores) if scores else 0.0,
            'acceptable_count': sum(1 for score in scores if score >= self.quality_threshold),
            'poor_count': sum(1 for score in scores if score < 0.5),
            'quality_distribution': {
                'excellent': excellent,
                'good': good,
                'acceptable': acceptable,
                'poor': poor
            }
        }