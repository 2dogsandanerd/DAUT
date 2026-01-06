"""
Modul für parallele Dateiverarbeitung zur Verbesserung der Performance
"""
import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import os
import threading
from src.core.config_manager import ProjectConfig
from src.scanner.code_scanner import CodeScanner
from src.scanner.doc_scanner import DocScanner
from src.scanner.file_handler import FileHandler
from src.models.element import CodeElement, DocElement


class ParallelScanner:
    """Scanner mit paralleler Verarbeitung für verbesserte Performance"""
    
    def __init__(self, config: ProjectConfig, max_workers: Optional[int] = None):
        self.config = config
        self.code_scanner = CodeScanner(config)
        self.doc_scanner = DocScanner(config)
        self.file_handler = FileHandler(config)
        
        # Setze maximale Anzahl Worker (Standard: Anzahl der CPU-Kerne)
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
    
    def scan_project_parallel(self, project_path: str, use_threading: bool = True) -> Dict[str, Any]:
        """
        Scannt das Projekt mit paralleler Verarbeitung
        
        Args:
            project_path: Pfad zum zu scannenden Projekt
            use_threading: Ob Threading (statt Multiprocessing) verwendet werden soll
        """
        project_path = Path(project_path)
        
        # Sammle alle zu scannenden Dateien
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
        
        print(f"Starte parallelen Scan von {len(all_files)} Dateien mit {self.max_workers} Workern...")
        
        # Initialisiere Ergebnisse
        code_elements = []
        doc_elements = []
        
        # Wähle die geeignete Methode für parallele Verarbeitung
        if use_threading:
            code_elements, doc_elements = self._process_files_with_threading(all_files)
        else:
            code_elements, doc_elements = self._process_files_with_multiprocessing(all_files)
        
        return {
            'code_elements': code_elements,
            'doc_elements': doc_elements,
            'scan_summary': {
                'total_files_scanned': len(all_files),
                'code_files': len(code_elements),
                'doc_files': len(doc_elements),
                'project_path': str(project_path),
                'workers_used': self.max_workers
            }
        }
    
    def _process_files_with_threading(self, files: List[Path]) -> tuple[List[CodeElement], List[DocElement]]:
        """Verarbeitet Dateien mit Threading"""
        code_elements = []
        doc_elements = []
        
        # Gruppiere Dateien nach Typ für effizientere Verarbeitung
        code_files = []
        doc_files = []
        
        for file_path in files:
            file_ext = file_path.suffix.lower()
            if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                code_files.append(file_path)
            elif file_ext in ['.md', '.rst', '.txt']:
                doc_files.append(file_path)
        
        # Verarbeite Code-Dateien parallel
        if code_files:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                code_results = list(executor.map(self._scan_code_file, code_files))
                # Entferne None-Werte und flache Liste
                for result in code_results:
                    if result:
                        code_elements.extend(result)
        
        # Verarbeite Dokumentations-Dateien parallel
        if doc_files:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                doc_results = list(executor.map(self._scan_doc_file, doc_files))
                # Entferne None-Werte und flache Liste
                for result in doc_results:
                    if result:
                        doc_elements.extend(result)
        
        return code_elements, doc_elements
    
    def _process_files_with_multiprocessing(self, files: List[Path]) -> tuple[List[CodeElement], List[DocElement]]:
        """Verarbeitet Dateien mit Multiprocessing"""
        # Für Multiprocessing müssen wir eine andere Herangehensweise wählen,
        # da die Scanner-Klassen nicht direkt serialisierbar sind
        code_elements = []
        doc_elements = []
        
        # Gruppiere Dateien nach Typ
        code_files = []
        doc_files = []
        
        for file_path in files:
            file_ext = file_path.suffix.lower()
            if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                code_files.append(file_path)
            elif file_ext in ['.md', '.rst', '.txt']:
                doc_files.append(file_path)
        
        # Verarbeite Code-Dateien parallel
        if code_files:
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Wir übergeben nur Dateipfade und erstellen Scanner innerhalb der Prozesse
                file_paths = [str(f) for f in code_files]
                code_results = list(executor.map(self._scan_code_file_multiprocess, file_paths))
                # Entferne None-Werte und flache Liste
                for result in code_results:
                    if result:
                        code_elements.extend(result)
        
        # Verarbeite Dokumentations-Dateien parallel
        if doc_files:
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                file_paths = [str(f) for f in doc_files]
                doc_results = list(executor.map(self._scan_doc_file_multiprocess, file_paths))
                # Entferne None-Werte und flache Liste
                for result in doc_results:
                    if result:
                        doc_elements.extend(result)
        
        return code_elements, doc_elements
    
    def _scan_code_file(self, file_path: Path) -> Optional[List[CodeElement]]:
        """Scannt eine einzelne Code-Datei (für Threading)"""
        try:
            return self.code_scanner.scan_file(file_path)
        except Exception as e:
            print(f"Fehler beim Scannen der Datei {file_path}: {e}")
            return None
    
    def _scan_doc_file(self, file_path: Path) -> Optional[List[DocElement]]:
        """Scannt eine einzelne Dokumentations-Datei (für Threading)"""
        try:
            return self.doc_scanner.scan_file(file_path)
        except Exception as e:
            print(f"Fehler beim Scannen der Datei {file_path}: {e}")
            return None
    
    @staticmethod
    def _scan_code_file_multiprocess(file_path_str: str) -> Optional[List[CodeElement]]:
        """Scannt eine einzelne Code-Datei (für Multiprocessing)"""
        from src.core.config_manager import ProjectConfig
        from src.scanner.code_scanner import CodeScanner
        
        # Erstelle temporäre Konfiguration (in der Praxis müsste dies anders gelöst werden)
        config = ProjectConfig()
        scanner = CodeScanner(config)
        
        try:
            file_path = Path(file_path_str)
            return scanner.scan_file(file_path)
        except Exception as e:
            print(f"Fehler beim Scannen der Datei {file_path_str}: {e}")
            return None
    
    @staticmethod
    def _scan_doc_file_multiprocess(file_path_str: str) -> Optional[List[DocElement]]:
        """Scannt eine einzelne Dokumentations-Datei (für Multiprocessing)"""
        from src.core.config_manager import ProjectConfig
        from src.scanner.doc_scanner import DocScanner
        
        # Erstelle temporäre Konfiguration (in der Praxis müsste dies anders gelöst werden)
        config = ProjectConfig()
        scanner = DocScanner(config)
        
        try:
            file_path = Path(file_path_str)
            return scanner.scan_file(file_path)
        except Exception as e:
            print(f"Fehler beim Scannen der Datei {file_path_str}: {e}")
            return None


class AsyncScanner:
    """Scanner mit asynchroner Verarbeitung"""
    
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.code_scanner = CodeScanner(config)
        self.doc_scanner = DocScanner(config)
        self.file_handler = FileHandler(config)
    
    async def scan_project_async(self, project_path: str) -> Dict[str, Any]:
        """Scannt das Projekt asynchron"""
        project_path = Path(project_path)
        
        # Sammle alle zu scannenden Dateien
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
        
        print(f"Starte asynchronen Scan von {len(all_files)} Dateien...")
        
        # Gruppiere Dateien nach Typ
        code_files = [f for f in all_files if f.suffix.lower() in ['.py', '.js', '.jsx', '.ts', '.tsx']]
        doc_files = [f for f in all_files if f.suffix.lower() in ['.md', '.rst', '.txt']]
        
        # Verarbeite Dateien asynchron
        code_elements = []
        doc_elements = []
        
        # Verarbeite Code-Dateien asynchron
        if code_files:
            code_tasks = [self._scan_code_file_async(f) for f in code_files]
            code_results = await asyncio.gather(*code_tasks, return_exceptions=True)
            for result in code_results:
                if isinstance(result, list):
                    code_elements.extend(result)
                elif isinstance(result, Exception):
                    print(f"Fehler bei asynchronem Scannen: {result}")
        
        # Verarbeite Dokumentations-Dateien asynchron
        if doc_files:
            doc_tasks = [self._scan_doc_file_async(f) for f in doc_files]
            doc_results = await asyncio.gather(*doc_tasks, return_exceptions=True)
            for result in doc_results:
                if isinstance(result, list):
                    doc_elements.extend(result)
                elif isinstance(result, Exception):
                    print(f"Fehler bei asynchronem Scannen: {result}")
        
        return {
            'code_elements': code_elements,
            'doc_elements': doc_elements,
            'scan_summary': {
                'total_files_scanned': len(all_files),
                'code_files': len(code_elements),
                'doc_files': len(doc_elements),
                'project_path': str(project_path)
            }
        }
    
    async def _scan_code_file_async(self, file_path: Path) -> Optional[List[CodeElement]]:
        """Scannt eine einzelne Code-Datei asynchron"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.code_scanner.scan_file, file_path)
    
    async def _scan_doc_file_async(self, file_path: Path) -> Optional[List[DocElement]]:
        """Scannt eine einzelne Dokumentations-Datei asynchron"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.doc_scanner.scan_file, file_path)