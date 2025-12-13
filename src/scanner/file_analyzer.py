from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import mimetypes
import json


class FileAnalyzer:
    def __init__(self):
        self.scan_statistics = {
            'total_files': 0,
            'included_files': 0,
            'excluded_files': 0,  # Zähler für Anzahl ausgeschlossener Dateien
            'file_types': defaultdict(int),
            'excluded_dirs': defaultdict(int),
            'excluded_file_extensions': defaultdict(int),  # defaultdict für Erweiterungen ausgeschlossener Dateien
            'file_sizes': [],
            'by_extension': defaultdict(int)
        }
        self.filtered_files = []
        self.excluded_files = []

    def analyze_file(self, file_path: Path, is_included: bool = True) -> None:
        """
        Analysiert eine Datei und aktualisiert die Statistiken
        
        Args:
            file_path: Der Pfad zur Datei
            is_included: Ob die Datei eingeschlossen wurde oder ausgeschlossen wurde
        """
        file_size = file_path.stat().st_size
        file_ext = file_path.suffix.lower()
        
        # Aktualisiere allgemeine Statistiken
        self.scan_statistics['total_files'] += 1
        
        if is_included:
            self.scan_statistics['included_files'] += 1
            self.scan_statistics['file_types'][self._get_file_type(file_ext)] += 1
            self.scan_statistics['by_extension'][file_ext] += 1
            self.scan_statistics['file_sizes'].append(file_size)
            self.filtered_files.append(file_path)
        else:
            self.scan_statistics['excluded_files'] += 1
            self.excluded_files.append(file_path)
            self.scan_statistics['excluded_file_extensions'][file_ext] += 1

    def analyze_directory_exclusion(self, dir_path: Path) -> None:
        """
        Protokolliert ein ausgeschlossenes Verzeichnis
        
        Args:
            dir_path: Der Pfad zum ausgeschlossenen Verzeichnis
        """
        dir_name = dir_path.name
        self.scan_statistics['excluded_dirs'][dir_name] += 1

    def get_scan_report(self) -> Dict:
        """
        Gibt einen umfassenden Bericht über den Scanvorgang zurück
        
        Returns:
            Ein Dictionary mit detaillierten Scan-Statistiken
        """
        # Berechne zusätzliche Statistiken
        if self.scan_statistics['file_sizes']:
            avg_size = sum(self.scan_statistics['file_sizes']) / len(self.scan_statistics['file_sizes'])
            max_size = max(self.scan_statistics['file_sizes'])
            min_size = min(self.scan_statistics['file_sizes'])
        else:
            avg_size = max_size = min_size = 0

        report = {
            'summary': {
                'total_files_scanned': self.scan_statistics['total_files'],
                'included_files': self.scan_statistics['included_files'],
                'excluded_files': self.scan_statistics['excluded_files'],
                'inclusion_rate': self.scan_statistics['included_files'] / max(1, self.scan_statistics['total_files']) * 100
            },
            'file_types': dict(self.scan_statistics['file_types']),
            'file_extensions': dict(self.scan_statistics['by_extension']),
            'excluded_directories': dict(self.scan_statistics['excluded_dirs']),
            'excluded_file_extensions': dict(self.scan_statistics['excluded_file_extensions']),
            'file_size_stats': {
                'average_size_bytes': avg_size,
                'max_size_bytes': max_size,
                'min_size_bytes': min_size
            },
            'filtered_files': [str(f) for f in self.filtered_files],
            'excluded_files': [str(f) for f in self.excluded_files]
        }
        
        return report

    def save_scan_report(self, output_path: str) -> None:
        """
        Speichert den Scan-Bericht in einer Datei
        
        Args:
            output_path: Pfad zur Ausgabedatei
        """
        report = self.get_scan_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    def print_scan_summary(self) -> None:
        """
        Gibt eine Zusammenfassung des Scans auf der Konsole aus
        """
        report = self.get_scan_report()
        summary = report['summary']
        
        print(f"\n=== Scan-Zusammenfassung ===")
        print(f"Gescannte Dateien insgesamt: {summary['total_files_scanned']}")
        print(f"Eingeschlossene Dateien: {summary['included_files']}")
        print(f"Ausgeschlossene Dateien: {summary['excluded_files']}")
        print(f"Einschlussrate: {summary['inclusion_rate']:.2f}%")
        
        print(f"\nDateitypen-Verteilung:")
        for file_type, count in report['file_types'].items():
            print(f"  {file_type}: {count}")
            
        print(f"\nAusgeschlossene Verzeichnisse:")
        for dir_name, count in list(report['excluded_directories'].items())[:10]:  # Begrenze Ausgabe
            print(f"  {dir_name}: {count}")

    def _get_file_type(self, extension: str) -> str:
        """
        Bestimmt den Dateityp basierend auf der Erweiterung
        
        Args:
            extension: Die Dateierweiterung (z.B. '.py', '.js')
        
        Returns:
            Der Dateityp (z.B. 'python', 'javascript', 'documentation', etc.)
        """
        # Kategorisierung basierend auf Dateierweiterung
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', 
            '.cs', '.go', '.rb', '.php', '.html', '.css', '.sql', '.sh', '.pl', 
            '.r', '.m', '.swift', '.kt', '.scala', '.dart', '.rs', '.vue', '.svelte'
        }
        doc_extensions = {
            '.md', '.rst', '.txt', '.pdf', '.doc', '.docx', '.odt', '.tex', '.org'
        }
        config_extensions = {
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.xml', 
            '.env', '.properties', '.lock'
        }
        data_extensions = {
            '.csv', '.jsonl', '.xlsx', '.xls', '.db', '.sqlite', '.sqlitedb', 
            '.hdf5', '.pkl', '.pickle', '.npy', '.npz'
        }
        
        if extension in code_extensions:
            return 'code'
        elif extension in doc_extensions:
            return 'documentation'
        elif extension in config_extensions:
            return 'configuration'
        elif extension in data_extensions:
            return 'data'
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']:
            return 'image'
        elif extension in ['.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv']:
            return 'media'
        else:
            return 'other'