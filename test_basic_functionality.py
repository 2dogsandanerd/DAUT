import sys
import os
# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.core.project_analyzer import ProjectAnalyzer
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine

def test_basic_functionality():
    """Testet die grundlegenden Funktionen des Dokumentations-Updaters"""
    print("Starte grundlegende Funktionalitätstests...")
    
    # Test 1: Konfigurations-Management
    print("\n1. Teste Konfigurations-Management...")
    config_manager = ConfigManager()
    config = config_manager.get_effective_config()
    print(f"   Standard-Scan-Pfade: {config.scan_paths}")
    print("   ✓ Konfigurations-Management funktioniert")
    
    # Test 2: Projekt-Analyse (wenn ein Projekt-Pfad angegeben ist)
    print("\n2. Teste Projekt-Analyse...")
    # Für diesen Test verwenden wir das aktuelle Verzeichnis
    current_dir = os.path.dirname(__file__)
    analyzer = ProjectAnalyzer(config)
    project_type = analyzer.detect_project_type(current_dir)
    print(f"   Erkannter Projekttyp für {os.path.basename(current_dir)}: {project_type}")
    scan_paths = analyzer.get_scan_paths(current_dir)
    print(f"   Empfohlene Scan-Pfade: {scan_paths[:3]}...")  # Nur die ersten 3 anzeigen
    print("   ✓ Projekt-Analyse funktioniert")
    
    # Test 3: Scanner-Initialisierung
    print("\n3. Teste Scanner-Initialisierung...")
    scanner = UniversalScanner(config)
    print("   ✓ Scanner erfolgreich initialisiert")
    
    # Test 4: Matcher-Engine
    print("\n4. Teste Matcher-Engine...")
    matcher = MatcherEngine()
    print("   ✓ Matcher-Engine erfolgreich initialisiert")
    
    print("\n✓ Alle grundlegenden Funktionen wurden erfolgreich getestet!")

if __name__ == "__main__":
    test_basic_functionality()