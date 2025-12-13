import unittest
from pathlib import Path
import tempfile
import os
from src.scanner.file_handler import FileHandler
from src.core.config_manager import ProjectConfig
from src.scanner.file_analyzer import FileAnalyzer
from src.scanner.gitignore_handler import GitIgnoreHandler
from src.scanner.progress_callback import ScanProgressCallback


class TestFileHandlerFiltering(unittest.TestCase):
    """Testfälle für die verbesserte Dateifilterung in FileHandler"""
    
    def setUp(self):
        """Setzt den Test-Setup mit einer Testkonfiguration"""
        self.config = ProjectConfig()
        # Erweitere die Konfiguration mit Test-Ausschlussmustern
        self.config.exclude_patterns.extend([
            "test_exclude_dir", "*.tmp", "*.temp", "node_modules", "venv", "__pycache__"
        ])
        self.config.include_patterns.extend(["*.py", "*.js", "*.txt"])
        
        self.file_handler = FileHandler(self.config)
    
    def test_exclude_directory_patterns(self):
        """Testet das Ausschließen von Verzeichnissen basierend auf Mustern"""
        # Teste die neue Methode _should_exclude_dir
        test_dir = Path("/tmp/test_project/test_exclude_dir")
        result = self.file_handler._should_exclude_dir(
            "test_exclude_dir", 
            Path("/tmp/test_project"), 
            self.config.exclude_patterns
        )
        self.assertTrue(result, "Verzeichnis sollte basierend auf Muster ausgeschlossen werden")
    
    def test_exclude_common_directories(self):
        """Testet das Ausschließen üblicher Verzeichnisse wie node_modules, venv etc."""
        exclude_indicators = ["node_modules", "venv", "__pycache__", "dist", "build"]
        
        for indicator in exclude_indicators:
            result = self.file_handler._should_exclude_dir(
                indicator, 
                Path("/tmp/test_project"), 
                self.config.exclude_patterns
            )
            self.assertTrue(
                result, 
                f"Verzeichnis '{indicator}' sollte als auszuschließen erkannt werden"
            )
    
    def test_should_include_file_positive(self):
        """Testet positives Einschließen von Dateien"""
        test_file = Path("/tmp/test_project/main.py")
        
        # Erstelle temporär die Datei
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()
        
        result = self.file_handler._should_include_file(test_file)
        self.assertTrue(result, "Python-Datei sollte eingeschlossen werden")
        
        # Bereinige
        test_file.unlink()
        test_file.parent.rmdir()
    
    def test_should_exclude_file_by_pattern(self):
        """Testet das Ausschließen von Dateien basierend auf Ausschlussmustern"""
        test_file = Path("/tmp/test_project/backup.tmp")
        
        # Erstelle temporär die Datei
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()
        
        result = self.file_handler._should_include_file(test_file)
        self.assertFalse(result, "tmp-Datei sollte ausgeschlossen werden")
        
        # Bereinige
        test_file.unlink()
        test_file.parent.rmdir()


class TestFileAnalyzer(unittest.TestCase):
    """Testfälle für die Dateianalyse-Funktionalität"""
    
    def setUp(self):
        self.analyzer = FileAnalyzer()
    
    def test_analyze_file_included(self):
        """Testet die Analyse einer eingeschlossenen Datei"""
        test_file = Path("/tmp/test.py")
        
        # Simuliere eine Datei
        self.analyzer.analyze_file(test_file, is_included=True)
        
        self.assertEqual(self.analyzer.scan_statistics['included_files'], 1)
        self.assertEqual(self.analyzer.scan_statistics['file_types']['code'], 1)
        self.assertIn(test_file, self.analyzer.filtered_files)
    
    def test_analyze_file_excluded(self):
        """Testet die Analyse einer ausgeschlossenen Datei"""
        test_file = Path("/tmp/test.log")
        
        # Simuliere eine Datei
        self.analyzer.analyze_file(test_file, is_included=False)
        
        self.assertEqual(self.analyzer.scan_statistics['excluded_files'], 1)
        self.assertIn(test_file, self.analyzer.excluded_files)
    
    def test_get_scan_report(self):
        """Testet die Generierung eines Scan-Berichts"""
        # Füge einige Dateien hinzu
        self.analyzer.analyze_file(Path("/tmp/test1.py"), is_included=True)
        self.analyzer.analyze_file(Path("/tmp/test2.js"), is_included=True)
        self.analyzer.analyze_file(Path("/tmp/test3.log"), is_included=False)
        
        report = self.analyzer.get_scan_report()
        
        self.assertEqual(report['summary']['included_files'], 2)
        self.assertEqual(report['summary']['excluded_files'], 1)
        self.assertIn('.py', report['file_extensions'])
        self.assertIn('.js', report['file_extensions'])


class TestGitIgnoreHandler(unittest.TestCase):
    """Testfälle für die GitIgnore-Handler-Funktionalität"""
    
    def setUp(self):
        # Erstelle ein temporäres Verzeichnis für Tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.gitignore_path = self.temp_dir / ".gitignore"
    
    def tearDown(self):
        # Lösche temporäres Verzeichnis und Inhalt
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_read_gitignore_patterns(self):
        """Testet das Lesen von Mustern aus einer .gitignore-Datei"""
        # Erstelle eine Test-.gitignore-Datei
        with open(self.gitignore_path, 'w', encoding='utf-8') as f:
            f.write("# Kommentar\n")
            f.write("*.tmp\n")
            f.write("test_dir/\n")
            f.write("secret.key\n")
        
        handler = GitIgnoreHandler(self.temp_dir)
        patterns = handler._read_gitignore_patterns(self.gitignore_path)
        
        expected_patterns = ["*.tmp", "test_dir/", "secret.key"]
        self.assertEqual(patterns, expected_patterns)
    
    def test_matches_pattern(self):
        """Testet das Muster-Matching für .gitignore-Regeln"""
        handler = GitIgnoreHandler(self.temp_dir)
        
        # Teste verschiedene Muster
        result = handler._matches_pattern(self.temp_dir / "test.tmp", "*.tmp")
        self.assertTrue(result, "Datei mit .tmp-Erweiterung sollte gematcht werden")
        
        result = handler._matches_pattern(self.temp_dir / "test.txt", "*.tmp")
        self.assertFalse(result, "Datei ohne .tmp-Erweiterung sollte nicht gematcht werden")


class TestProgressCallback(unittest.TestCase):
    """Testfälle für die Fortschritts-Callback-Funktionalität"""
    
    def setUp(self):
        self.callback = ScanProgressCallback()
    
    def test_update_total_directories(self):
        """Testet das Aktualisieren der Gesamtanzahl an Verzeichnissen"""
        self.callback.update_total_directories(10)
        self.assertEqual(self.callback.total_directories, 10)
    
    def test_update_total_files(self):
        """Testet das Aktualisieren der Gesamtanzahl an Dateien"""
        self.callback.update_total_files(100)
        self.assertEqual(self.callback.total_files, 100)
    
    def test_scanning_directory(self):
        """Testet das Verzeichnis-Scanning"""
        test_dir = Path("/tmp/test_dir")
        
        self.callback.update_total_directories(5)
        self.callback.scanning_directory(test_dir)
        
        self.assertEqual(self.callback.directories_scanned, 1)
        self.assertEqual(self.callback.current_directory, str(test_dir))
    
    def test_scanning_file(self):
        """Testet das Datei-Scanning"""
        test_file = Path("/tmp/test.py")
        
        self.callback.update_total_files(10)
        self.callback.scanning_file(test_file)
        
        self.assertEqual(self.callback.files_scanned, 1)


class TestConfigManagerExtended(unittest.TestCase):
    """Testfälle für die erweiterte Konfigurationsverwaltung"""
    
    def test_extended_exclude_patterns(self):
        """Testet die erweiterten Ausschlussmuster in der Konfiguration"""
        config = ProjectConfig()
        
        # Prüfe, ob die erweiterten Muster in der Standardkonfiguration enthalten sind
        extended_patterns = [
            "node_modules", "venv", ".venv", "__pycache__", ".git",
            "dist", "build", ".pytest_cache", ".vscode", ".idea",
            "target", "out", ".next", "coverage", ".tox", ".nox",
            "env", ".env", "env.bak", ".env.bak", "venv.bak", ".venv",
            "__bundle", "Pods", ".dart_tool", ".pub", "vendor", "bower_components",
            ".npm", ".yarn", "jspm_packages", ".angular", ".nuxt", ".vercel",
            ".netlify", ".cache", "tmp", "temp", ".tmp", ".temp", ".serverless",
            ".dynamodb", ".fusebox", ".nyc_output", ".sass-cache", "lib-cov"
        ]
        
        for pattern in extended_patterns:
            self.assertIn(pattern, config.exclude_patterns,
                         f"Ausschlussmuster '{pattern}' fehlt in der Konfiguration")


if __name__ == '__main__':
    # Führe alle Tests aus
    unittest.main(verbosity=2)