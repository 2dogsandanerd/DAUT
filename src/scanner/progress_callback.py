from typing import Callable, Optional
from pathlib import Path
from typing import List, Dict, Any


class ScanProgressCallback:
    """
    Callback-Klasse zur Verfolgung des Scan-Fortschritts
    """
    def __init__(self):
        self.total_directories = 0
        self.directories_scanned = 0
        self.total_files = 0
        self.files_scanned = 0
        self.current_directory = ""
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None

    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """
        Setzt die Callback-Funktion zur Fortschrittsanzeige
        
        Args:
            callback: Funktion mit Signatur callback(current, total, description)
        """
        self.progress_callback = callback

    def update_total_directories(self, count: int):
        """Aktualisiert die Gesamtanzahl der zu scannenden Verzeichnisse"""
        self.total_directories = count

    def update_total_files(self, count: int):
        """Aktualisiert die Gesamtanzahl der zu scannenden Dateien"""
        self.total_files = count

    def scanning_directory(self, directory: Path):
        """Wird aufgerufen, wenn ein Verzeichnis gescannt wird"""
        self.current_directory = str(directory)
        self.directories_scanned += 1
        if self.progress_callback:
            self.progress_callback(
                self.directories_scanned, 
                self.total_directories, 
                f"Scanne Verzeichnis: {directory.name}"
            )

    def scanning_file(self, file_path: Path):
        """Wird aufgerufen, wenn eine Datei gescannt wird"""
        self.files_scanned += 1

        # Standard-Ausgabe wenn kein Callback gesetzt
        if self.total_files > 0:
            percentage = (self.files_scanned / self.total_files) * 100
            print(f"\r🔍 Scanning: [{self.files_scanned}/{self.total_files}] {percentage:.1f}% - {file_path.name[:50]}", end='', flush=True)

        if self.progress_callback:
            self.progress_callback(
                self.files_scanned,
                self.total_files,
                f"Scanne Datei: {file_path.name}"
            )

    def get_progress_info(self) -> Dict[str, Any]:
        """Gibt Informationen über den aktuellen Fortschritt zurück"""
        return {
            'directories_scanned': self.directories_scanned,
            'total_directories': self.total_directories,
            'files_scanned': self.files_scanned,
            'total_files': self.total_files,
            'current_directory': self.current_directory,
            'directory_percentage': (self.directories_scanned / max(1, self.total_directories)) * 100,
            'file_percentage': (self.files_scanned / max(1, self.total_files)) * 100
        }