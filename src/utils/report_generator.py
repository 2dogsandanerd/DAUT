from typing import Dict, Any, List
from ..models.element import CodeElement, DocElement

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_scan_report(self, scan_results: Dict[str, Any]) -> str:
        """Generiert einen menschenlesbaren Scan-Bericht"""
        report = []
        report.append("# Scan-Bericht\n")
        
        summary = scan_results['scan_summary']
        report.append(f"## Zusammenfassung")
        report.append(f"- Gesamte Dateien gescannt: {summary['total_files_scanned']}")
        report.append(f"- Code-Elemente gefunden: {summary['code_files']}")
        report.append(f"- Dokumentations-Elemente gefunden: {summary['doc_files']}")
        report.append(f"- Projekt-Pfad: {summary['project_path']}")
        report.append("")  # Leerzeile
        
        report.append(f"## Code-Elemente (Auszug)")
        for i, elem in enumerate(scan_results['code_elements'][:10]):  # Nur ersten 10 anzeigen
            report.append(f"- {elem.type.value}: {elem.name} in {elem.file_path}")
        if len(scan_results['code_elements']) > 10:
            report.append(f"... und {len(scan_results['code_elements']) - 10} weitere")
        report.append("")
        
        report.append(f"## Dokumentations-Elemente (Auszug)")
        for i, elem in enumerate(scan_results['doc_elements'][:10]):  # Nur ersten 10 anzeigen
            report.append(f"- {elem.type.value}: {elem.name}")
        if len(scan_results['doc_elements']) > 10:
            report.append(f"... und {len(scan_results['doc_elements']) - 10} weitere")
        report.append("")
        
        return "\n".join(report)
    
    def generate_discrepancy_report(self, discrepancies: Dict[str, Any]) -> str:
        """Generiert einen Bericht über gefundene Diskrepanzen"""
        report = []
        report.append("# Diskrepanz-Bericht\n")
        
        report.append(f"## Undokumentierter Code")
        for elem in discrepancies['undocumented_code']:
            report.append(f"- {elem.type.value}: {elem.name} in {elem.file_path}")
        report.append("")
        
        report.append(f"## Veraltete Dokumentation")
        for elem in discrepancies['outdated_documentation']:
            report.append(f"- {elem.type.value}: {elem.name}")
        report.append("")
        
        report.append(f"## Nicht übereinstimmende Elemente")
        for item in discrepancies['mismatched_elements']:
            code_elem = item['code']
            doc_elem = item['documentation']
            report.append(f"- Code: {code_elem.name} vs Doc: {doc_elem.name}")
        report.append("")
        
        return "\n".join(report)