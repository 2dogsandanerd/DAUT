import sys
import os
# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Testet, ob alle Module erfolgreich importiert werden können"""
    print("Teste Modul-Importe...")
    
    try:
        from src.core.config_manager import ConfigManager
        print("✓ config_manager erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von config_manager: {e}")
    
    try:
        from src.core.project_analyzer import ProjectAnalyzer
        print("✓ project_analyzer erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von project_analyzer: {e}")
    
    try:
        from src.scanner.universal_scanner import UniversalScanner
        print("✓ universal_scanner erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von universal_scanner: {e}")
    
    try:
        from src.matcher import MatcherEngine
        print("✓ matcher erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von matcher: {e}")
    
    try:
        from src.models.element import CodeElement, ElementType
        print("✓ models.element erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von models.element: {e}")
    
    try:
        from src.ui.main import main
        print("✓ ui.main erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von ui.main: {e}")
    
    try:
        from src.updater.engine import UpdaterEngine
        print("✓ updater.engine erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von updater.engine: {e}")
    
    try:
        from src.llm.client import OllamaClient
        print("✓ llm.client erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von llm.client: {e}")
    
    try:
        from src.chroma.client import ChromaDBClient
        print("✓ chroma.client erfolgreich importiert")
    except Exception as e:
        print(f"✗ Fehler beim Import von chroma.client: {e}")
    
    print("\nAlle Import-Tests abgeschlossen!")

if __name__ == "__main__":
    test_imports()