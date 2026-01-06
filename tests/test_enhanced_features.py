"""
Zusätzliche Tests für die DAUT-Verbesserungen
"""
import unittest
import tempfile
import os
from pathlib import Path
from src.updater.engine import UpdaterEngine
from src.scanner.universal_scanner import UniversalScanner
from src.core.config_manager import ConfigManager
from src.models.element import CodeElement, ElementType


class TestUpdaterEngineEnhancements(unittest.TestCase):
    """Tests für die UpdaterEngine-Erweiterungen"""
    
    def setUp(self):
        # Erstelle temporäres Verzeichnis für Tests
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Lösche temporäres Verzeichnis nach Tests
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_updater_engine_initialization(self):
        """Testet die Initialisierung der UpdaterEngine mit neuen Komponenten"""
        engine = UpdaterEngine()
        
        # Prüfe, ob die neuen Komponenten initialisiert wurden
        self.assertIsNotNone(engine.quality_manager)
        self.assertIsNotNone(engine.name_generator)
        
        # Prüfe, ob die Konfiguration korrekt geladen wurde
        self.assertIsNotNone(engine.service_config)
        self.assertEqual(engine.service_config.embedding_model, "nomic-embed-text")
        self.assertEqual(engine.service_config.llm_model, "llama3")


class TestUniversalScannerEnhancements(unittest.TestCase):
    """Tests für die UniversalScanner-Erweiterungen"""
    
    def test_universal_scanner_parallel_scan(self):
        """Testet die parallele Scan-Funktion des UniversalScanners"""
        config = ConfigManager().get_effective_config()
        scanner = UniversalScanner(config)
        
        # Erstelle ein temporäres Projektverzeichnis mit ein paar Dateien
        with tempfile.TemporaryDirectory() as temp_dir:
            # Erstelle eine Test-Python-Datei
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("""
def test_function():
    \"\"\"Eine Testfunktion\"\"\"
    return "Hello, World!"

class TestClass:
    \"\"\"Eine Testklasse\"\"\"
    def test_method(self):
        return "Test"
""")
            
            # Aktualisiere die Scan-Pfade
            config.scan_paths = [temp_dir]
            
            # Führe einen parallelen Scan durch
            result = scanner.scan_project_parallel(temp_dir, max_workers=2)
            
            # Prüfe, ob Elemente gefunden wurden
            self.assertGreaterEqual(len(result['code_elements']), 2)  # Funktion + Klasse
            self.assertEqual(result['scan_summary']['workers_used'], 2)


class TestCodeElementEnhancements(unittest.TestCase):
    """Tests für die CodeElement-Erweiterungen"""
    
    def test_code_element_creation(self):
        """Testet die Erstellung von CodeElementen mit verschiedenen Typen"""
        # Teste Funktion
        func_element = CodeElement(
            name="test_function",
            type=ElementType.FUNCTION,
            signature="def test_function() -> str:",
            parameters=[{"name": "param1", "type_annotation": "str"}],
            return_type="str",
            docstring="Eine Testfunktion",
            line_number=1,
            file_path="/path/to/file.py"
        )
        
        self.assertEqual(func_element.name, "test_function")
        self.assertEqual(func_element.type, ElementType.FUNCTION)
        
        # Teste Klasse
        class_element = CodeElement(
            name="TestClass",
            type=ElementType.CLASS,
            signature="class TestClass:",
            methods=[{"name": "test_method", "is_private": False}],
            docstring="Eine Testklasse",
            line_number=5,
            file_path="/path/to/file.py"
        )
        
        self.assertEqual(class_element.name, "TestClass")
        self.assertEqual(class_element.type, ElementType.CLASS)


class TestQualityManagerIntegration(unittest.TestCase):
    """Tests für die Integration des QualityManagers"""
    
    def test_quality_evaluation_integration(self):
        """Testet die Integration der Qualitätsbewertung in die UpdaterEngine"""
        engine = UpdaterEngine()
        
        # Erstelle eine Testdokumentation
        test_doc = """
        ## test_function
        
        ### Beschreibung
        Eine Testfunktion
        
        ### Parameter
        - param1: Ein Parameter
        
        ### Rückgabewert
        Ein String
        
        ### Beispiel
        ```python
        result = test_function("test")
        ```
        """
        
        # Bewertung sollte erfolgreich sein
        quality_score = engine.quality_manager.evaluate_single_documentation(test_doc)
        self.assertGreaterEqual(quality_score.overall_score, 0.5)  # Sollte eine akzeptable Bewertung haben


class TestConfigManagerEnhancements(unittest.TestCase):
    """Tests für die ConfigManager-Erweiterungen"""
    
    def test_config_update_for_project(self):
        """Testet die Projektanpassung der Konfiguration"""
        config = ConfigManager().get_effective_config()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Erstelle eine requirements.txt mit FastAPI
            req_file = Path(temp_dir) / "requirements.txt"
            req_file.write_text("fastapi==0.68.0\npydantic==1.8.2\n")
            
            # Erstelle ein src-Verzeichnis
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            # Aktualisiere die Konfiguration basierend auf dem Projekt
            config.update_for_project(temp_dir)
            
            # Prüfe, ob die Konfiguration aktualisiert wurde
            self.assertIn("fastapi", config.project_type)
            self.assertIn("src", config.scan_paths)


def run_all_tests():
    """Führt alle Tests aus"""
    # Erstelle einen Test-Loader und Test-Suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Füge alle Tests hinzu
    suite.addTests(loader.loadTestsFromTestCase(TestUpdaterEngineEnhancements))
    suite.addTests(loader.loadTestsFromTestCase(TestUniversalScannerEnhancements))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeElementEnhancements))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManagerEnhancements))
    
    # Führe die Tests aus
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    # Führe alle Tests aus
    result = run_all_tests()
    
    # Gib eine Zusammenfassung aus
    print(f"\nTests durchgeführt: {result.testsRun}")
    print(f"Fehlgeschlagen: {len(result.failures)}")
    print(f"Fehler: {len(result.errors)}")
    
    if result.failures:
        print("\nFehlgeschlagene Tests:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nFehlerhafte Tests:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # Beende mit Exit-Code basierend auf Testergebnis
    exit(0 if result.wasSuccessful() else 1)