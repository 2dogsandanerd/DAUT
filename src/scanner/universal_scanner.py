from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import os
import mimetypes
from .code_scanner import CodeScanner
from .doc_scanner import DocScanner
from .file_handler import FileHandler
from .file_analyzer import FileAnalyzer
from .performance_analyzer import PerformanceAnalyzer
from .progress_callback import ScanProgressCallback
from .framework_parsers import get_framework_parser
from .parallel_scanner import ParallelScanner
from src.core.config_manager import ProjectConfig

class UniversalScanner:
    def __init__(self, config: ProjectConfig, progress_callback: Optional[ScanProgressCallback] = None):
        self.config = config
        self.code_scanner = CodeScanner(config)
        self.doc_scanner = DocScanner(config)
        self.file_handler = FileHandler(config)
        self.file_analyzer = FileAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.progress_callback = progress_callback or ScanProgressCallback()
    
    def scan_project(self, project_path: str) -> Dict[str, Any]:
        """Scannt das gesamte Projekt und gibt alle gefundenen Elemente zurück"""
        project_path = Path(project_path)

        # Starte Performance-Analyse
        start_time = self.performance_analyzer.start_timing()
        file_sizes = []
        directories_scanned = 0

        # Zähle alle Dateien und Verzeichnisse vor dem Scannen
        all_files = []
        scan_paths_list = []

        for scan_path_str in self.config.scan_paths:
            scan_path = project_path / scan_path_str
            if not scan_path.exists():
                continue
            scan_paths_list.append(scan_path)

            # Hole alle relevanten Dateien
            files = self.file_handler.get_filtered_files(scan_path)
            all_files.extend(files)

        # Informiere den Callback über die Gesamtanzahlen
        self.progress_callback.update_total_directories(len(scan_paths_list))
        self.progress_callback.update_total_files(len(all_files))

        # Dateien filtern und scannen
        code_elements = []
        doc_elements = []

        # Bestimme das Framework basierend auf dem Projekttyp
        framework_parser = None
        if hasattr(self.config, 'project_type'):
            # Versuche, einen spezifischen Parser basierend auf dem Projekttyp zu erhalten
            if 'fastapi' in self.config.project_type:
                framework_parser = get_framework_parser('fastapi')
            elif 'flask' in self.config.project_type:
                framework_parser = get_framework_parser('flask')
            elif 'django' in self.config.project_type:
                framework_parser = get_framework_parser('django')
            elif 'express' in self.config.project_type:
                framework_parser = get_framework_parser('express')

        for scan_path in scan_paths_list:
            # Benachrichtige den Callback, dass ein Verzeichnis gescannt wird
            self.progress_callback.scanning_directory(scan_path)

            directories_scanned += 1
            files = self.file_handler.get_filtered_files(scan_path)

            for file_path in files:
                file_ext = file_path.suffix.lower()
                file_sizes.append(file_path.stat().st_size)

                # Benachrichtige den Callback, dass eine Datei gescannt wird
                self.progress_callback.scanning_file(file_path)

                if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                    # Code-Datei scannen
                    elements = self.code_scanner.scan_file(file_path)

                    # Wenn ein Framework-Parser verfügbar ist, verwende diesen zusätzlich
                    if framework_parser and self._is_relevant_for_framework(file_path, framework_parser.get_framework_name()):
                        framework_elements = framework_parser.parse_file(file_path)
                        elements.extend(framework_elements)

                    code_elements.extend(elements)
                    # Analysiere die eingeschlossene Datei
                    self.file_analyzer.analyze_file(file_path, is_included=True)
                elif file_ext in ['.md', '.rst', '.txt']:
                    # Dokumentations-Datei scannen
                    elements = self.doc_scanner.scan_file(file_path)
                    doc_elements.extend(elements)
                    # Analysiere die eingeschlossene Datei
                    self.file_analyzer.analyze_file(file_path, is_included=True)
                else:
                    # Analysiere die ignorierte Datei
                    self.file_analyzer.analyze_file(file_path, is_included=False)

        # Stoppe Performance-Analyse
        total_files = len(code_elements) + len(doc_elements)
        metrics = self.performance_analyzer.stop_timing(
            start_time,
            files_processed=total_files,
            file_sizes=file_sizes,
            directories_scanned=directories_scanned
        )

        # Abschlussmeldung
        print(f"\n\n{'='*60}")
        print(f"✅ Scan abgeschlossen!")
        print(f"{'='*60}")
        print(f"📊 Gefunden:")
        print(f"   • Code-Elemente:   {len(code_elements)}")
        print(f"   • Doku-Elemente:   {len(doc_elements)}")
        print(f"   • Dateien gescannt: {self.progress_callback.files_scanned}")
        print(f"{'='*60}\n")

        return {
            'code_elements': code_elements,
            'doc_elements': doc_elements,
            'scan_summary': {
                'total_files_scanned': total_files,
                'code_files': len(code_elements),
                'doc_files': len(doc_elements),
                'project_path': str(project_path),
                'framework_used': framework_parser.get_framework_name() if framework_parser else None
            },
            'scan_report': self.file_analyzer.get_scan_report(),
            'performance_report': self.performance_analyzer.get_performance_report(),
            'progress_info': self.progress_callback.get_progress_info()
        }

    def _is_relevant_for_framework(self, file_path: Path, framework_name: str) -> bool:
        """Prüft, ob eine Datei für ein bestimmtes Framework relevant ist"""
        # Für Python-Frameworks
        if framework_name in ['fastapi', 'flask', 'django']:
            return file_path.suffix.lower() == '.py'
        # Für JavaScript-Frameworks
        elif framework_name == 'express':
            return file_path.suffix.lower() in ['.js', '.ts']
        return True

    def scan_project_parallel(self, project_path: str, max_workers: Optional[int] = None) -> Dict[str, Any]:
        """Scannt das Projekt mit paralleler Verarbeitung für verbesserte Performance"""
        # Erstelle einen ParallelScanner mit der gleichen Konfiguration
        parallel_scanner = ParallelScanner(self.config, max_workers=max_workers)

        # Führe den parallelen Scan durch
        result = parallel_scanner.scan_project_parallel(project_path)

        # Ergänze die Ergebnisse mit Analysedaten, die normalerweise im Standard-Scan erfasst werden
        result['scan_report'] = self.file_analyzer.get_scan_report()
        result['performance_report'] = self.performance_analyzer.get_performance_report()
        result['progress_info'] = self.progress_callback.get_progress_info() if self.progress_callback else {}

        return result
    
    def scan_single_file(self, file_path: str) -> Dict[str, Any]:
        """Scannt eine einzelne Datei"""
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
            elements = self.code_scanner.scan_file(file_path)
            return {'type': 'code', 'elements': elements}
        elif file_ext in ['.md', '.rst', '.txt']:
            elements = self.doc_scanner.scan_file(file_path)
            return {'type': 'doc', 'elements': elements}
        else:
            return {'type': 'unknown', 'elements': []}