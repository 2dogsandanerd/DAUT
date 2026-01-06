"""
Tests für die DAUT-Verbesserungen
"""
import unittest
from pathlib import Path
import tempfile
import os
from src.core.service_config import ServiceConfig
from src.core.config_manager import ProjectConfig, ConfigManager
from src.quality.quality_evaluator import DocumentationQualityEvaluator, QualityScore
from src.quality.quality_manager import DocumentationQualityManager
from src.utils.structured_logging import StructuredLogger
from src.scanner.framework_parsers import FastAPIParser, FlaskParser, ExpressParser, DjangoParser
from src.matcher.advanced_matcher import AdvancedMatcherEngine, ConflictResolutionResult, ConflictResolutionStrategy
from src.scanner.parallel_scanner import ParallelScanner
from src.scanner.go_rust_parsers import GoParser, RustParser
from src.integration.git_hooks import GitHookManager
from src.utils.name_generator import UniqueNameGenerator, DocumentationFileOrganizer


class TestServiceConfig(unittest.TestCase):
    """Tests für die Service-Konfiguration"""
    
    def test_service_config_defaults(self):
        """Testet die Standardwerte der Service-Konfiguration"""
        config = ServiceConfig()
        self.assertEqual(config.ollama_host, "http://localhost:11434")
        self.assertEqual(config.chroma_host, "localhost")
        self.assertEqual(config.chroma_port, 8000)
        self.assertEqual(config.embedding_model, "nomic-embed-text")
        self.assertEqual(config.llm_model, "llama3")
    
    def test_service_config_custom_values(self):
        """Testet das Setzen benutzerdefinierter Werte"""
        config = ServiceConfig(
            ollama_host="http://custom-host:11434",
            embedding_model="custom-embedding-model",
            llm_model="custom-llm-model"
        )
        self.assertEqual(config.ollama_host, "http://custom-host:11434")
        self.assertEqual(config.embedding_model, "custom-embedding-model")
        self.assertEqual(config.llm_model, "custom-llm-model")


class TestConfigManager(unittest.TestCase):
    """Tests für den Konfigurationsmanager"""
    
    def test_config_manager_with_project_path(self):
        """Testet den Konfigurationsmanager mit Projektverzeichnis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Erstelle ein simuliertes Projektverzeichnis mit requirements.txt
            project_path = Path(temp_dir)
            req_file = project_path / "requirements.txt"
            req_file.write_text("fastapi==0.68.0\npydantic==1.8.2\n")
            
            # Initialisiere den ConfigManager mit Projektverzeichnis
            config_manager = ConfigManager(project_path=str(project_path))
            config = config_manager.get_effective_config()
            
            # Prüfe, ob die Konfiguration aktualisiert wurde
            self.assertIn("fastapi", config.project_type)
            self.assertIn("src", config.scan_paths)  # Sollte hinzugefügt werden, wenn src-Verzeichnis existiert


class TestDocumentationQualityEvaluator(unittest.TestCase):
    """Tests für den Dokumentations-Qualitätsbewerter"""
    
    def setUp(self):
        self.evaluator = DocumentationQualityEvaluator()
    
    def test_evaluate_empty_documentation(self):
        """Testet die Bewertung leerer Dokumentation"""
        score = self.evaluator.evaluate_documentation("")
        self.assertEqual(score.overall_score, 0.0)
        self.assertIn("Dokumentation ist leer", score.feedback)
    
    def test_evaluate_documentation_with_completeness(self):
        """Testet die Bewertung auf Vollständigkeit"""
        doc = """
        ## Funktion: calculate_sum
        
        ### Beschreibung
        Berechnet die Summe von zwei Zahlen.
        
        ### Parameter
        - a: Erste Zahl
        - b: Zweite Zahl
        
        ### Rückgabewert
        Die Summe der beiden Zahlen
        """
        score = self.evaluator.evaluate_documentation(doc)
        # Vollständigkeit sollte gut bewertet werden, da Beschreibung, Parameter und Rückgabewert vorhanden sind
        self.assertGreaterEqual(score.detailed_scores['completeness'], 0.7)
    
    def test_evaluate_documentation_with_examples(self):
        """Testet die Bewertung von Beispielen"""
        doc = """
        ## Funktion: calculate_sum
        
        ### Beschreibung
        Berechnet die Summe von zwei Zahlen.
        
        ### Beispiel
        ```python
        result = calculate_sum(2, 3)
        print(result)  # Ausgabe: 5
        ```
        """
        score = self.evaluator.evaluate_documentation(doc)
        # Beispiele sollten gut bewertet werden, wenn Beispiel vorhanden ist
        self.assertGreaterEqual(score.detailed_scores['examples'], 0.7)


class TestStructuredLogging(unittest.TestCase):
    """Tests für das strukturierte Logging"""
    
    def test_logger_initialization(self):
        """Testet die Initialisierung des Loggers"""
        logger = StructuredLogger("test_logger")
        self.assertIsNotNone(logger.logger)
    
    def test_logging_with_extra_data(self):
        """Testet das Logging mit zusätzlichen Daten"""
        logger = StructuredLogger("test_logger")
        # Dies sollte keinen Fehler verursachen
        logger.info("Testmeldung", extra_data={"test_key": "test_value"})


class TestFrameworkParsers(unittest.TestCase):
    """Tests für die Framework-Parser"""
    
    def test_fastapi_parser_basic(self):
        """Testet den FastAPI-Parser"""
        parser = FastAPIParser()
        # Teste mit einer einfachen FastAPI-Datei
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    \"\"\"
    Liest ein Item anhand der ID
    \"\"\"
    return {"item_id": item_id, "q": q}
""")
            temp_file = f.name
        
        try:
            elements = parser.parse_file(Path(temp_file))
            # Sollte mindestens ein Element finden
            self.assertGreaterEqual(len(elements), 1)
            if elements:
                element = elements[0]
                self.assertEqual(element['type'], 'api_endpoint')
                self.assertIn('read_item', element['name'])
        finally:
            os.unlink(temp_file)
    
    def test_flask_parser_basic(self):
        """Testet den Flask-Parser"""
        parser = FlaskParser()
        # Teste mit einer einfachen Flask-Datei
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from flask import Flask

app = Flask(__name__)

@app.route('/hello/<name>')
def hello(name):
    \"\"\"
    Sagt Hallo zu jemandem
    \"\"\"
    return f"Hello {name}!"
""")
            temp_file = f.name
        
        try:
            elements = parser.parse_file(Path(temp_file))
            # Sollte mindestens ein Element finden
            self.assertGreaterEqual(len(elements), 1)
            if elements:
                element = elements[0]
                self.assertEqual(element['type'], 'api_endpoint')
                self.assertIn('hello', element['name'])
        finally:
            os.unlink(temp_file)


class TestAdvancedMatcher(unittest.TestCase):
    """Tests für den erweiterten Matcher"""
    
    def setUp(self):
        self.matcher = AdvancedMatcherEngine()
    
    def test_resolution_result_creation(self):
        """Testet die Erstellung von Konfliktlösungsresultaten"""
        result = ConflictResolutionResult(
            resolution_strategy=ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE,
            confidence=0.9,
            suggested_changes={'test': 'change'},
            reason="Test reason"
        )
        self.assertEqual(result.resolution_strategy, ConflictResolutionStrategy.UPDATE_DOCUMENTATION_FROM_CODE)
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.suggested_changes['test'], 'change')
        self.assertEqual(result.reason, "Test reason")


class TestParallelScanner(unittest.TestCase):
    """Tests für den parallelen Scanner"""
    
    def test_parallel_scanner_initialization(self):
        """Testet die Initialisierung des parallelen Scanners"""
        config = ProjectConfig()
        scanner = ParallelScanner(config, max_workers=2)
        self.assertEqual(scanner.max_workers, 2)


class TestGoRustParsers(unittest.TestCase):
    """Tests für die Go- und Rust-Parser"""
    
    def test_goparser_basic(self):
        """Testet den Go-Parser"""
        parser = GoParser()
        # Teste mit einer einfachen Go-Datei
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write("""
package main

import "fmt"

type Person struct {
    Name string
    Age  int
}

func (p Person) Greet() string {
    return fmt.Sprintf("Hello, my name is %s and I am %d years old", p.Name, p.Age)
}

func main() {
    p := Person{Name: "Alice", Age: 30}
    fmt.Println(p.Greet())
}
""")
            temp_file = f.name
        
        try:
            elements = parser.parse_file(Path(temp_file))
            # Sollte Funktionen und Strukturen finden
            function_found = any(elem['type'] == 'function' and elem['name'] == 'main' for elem in elements)
            struct_found = any(elem['type'] == 'struct' and elem['name'] == 'Person' for elem in elements)
            self.assertTrue(function_found or struct_found)
        finally:
            os.unlink(temp_file)
    
    def test_rustparser_basic(self):
        """Testet den Rust-Parser"""
        parser = RustParser()
        # Teste mit einer einfachen Rust-Datei
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write("""
struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: String, age: u32) -> Person {
        Person { name, age }
    }

    fn greet(&self) -> String {
        format!("Hello, my name is {} and I am {} years old", self.name, self.age)
    }
}

fn main() {
    let person = Person::new("Alice".to_string(), 30);
    println!("{}", person.greet());
}
""")
            temp_file = f.name
        
        try:
            elements = parser.parse_file(Path(temp_file))
            # Sollte Funktionen und Strukturen finden
            function_found = any(elem['type'] == 'function' and elem['name'] == 'main' for elem in elements)
            struct_found = any(elem['type'] == 'struct' and elem['name'] == 'Person' for elem in elements)
            self.assertTrue(function_found or struct_found)
        finally:
            os.unlink(temp_file)


class TestNameGenerator(unittest.TestCase):
    """Tests für den Namensgenerator"""
    
    def setUp(self):
        self.generator = UniqueNameGenerator()
    
    def test_unique_name_generation(self):
        """Testet die Generierung eindeutiger Namen"""
        name1 = self.generator.generate_unique_filename("test", ".md", "/path/to/file.py")
        name2 = self.generator.generate_unique_filename("test", ".md", "/path/to/file.py")
        
        # Die Namen sollten unterschiedlich sein
        self.assertNotEqual(name1, name2)
        
        # Name2 sollte einen Zähler enthalten
        self.assertIn("_1", name2)
    
    def test_namespace_derivation(self):
        """Testet die Ableitung von Namensräumen aus Pfaden"""
        namespace = self.generator._derive_namespace_from_path("/project/src/module/file.py")
        # Sollte die letzten beiden Verzeichnisebenen verwenden
        self.assertIn("src.module", namespace)


class TestDocumentationFileOrganizer(unittest.TestCase):
    """Tests für die Dokumentationsdatei-Organisation"""
    
    def setUp(self):
        self.organizer = DocumentationFileOrganizer()
    
    def test_organize_documentation_files(self):
        """Testet die Organisation von Dokumentationsdateien"""
        elements = [
            {
                'name': 'calculate_sum',
                'type': 'function',
                'file_path': '/project/src/math.py'
            },
            {
                'name': 'UserClass',
                'type': 'class',
                'file_path': '/project/src/models.py'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping = self.organizer.organize_documentation_files(elements, temp_dir)
            
            # Sollte eine Zuordnung erstellen
            self.assertIn('function:calculate_sum', mapping)
            self.assertIn('class:UserClass', mapping)


if __name__ == '__main__':
    unittest.main()