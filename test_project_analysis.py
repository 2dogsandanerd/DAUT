import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.core.project_analyzer import ProjectAnalyzer

def test_project_analysis():
    """Testet die verbesserte Projektanalyse mit einem Beispielprojekt"""
    print("Teste verbesserte Projektanalyse...")
    
    # Wähle ein Testverzeichnis (hier das Hauptverzeichnis des Mail Modul Alpha)
    test_project_path = "/mnt/dev/eingang/mail_modul_alpha"
    
    if not os.path.exists(test_project_path):
        print(f"Testverzeichnis nicht gefunden: {test_project_path}")
        # Als Fallback, teste im aktuellen Verzeichnis
        test_project_path = "."
    
    config_manager = ConfigManager()
    config = config_manager.get_effective_config()
    analyzer = ProjectAnalyzer(config)
    
    # Erkenne Projekttyp
    project_type = analyzer.detect_project_type(test_project_path)
    print(f"Erkannter Projekttyp: {project_type}")
    
    # Erhalte Scan-Pfade
    scan_paths = analyzer.get_scan_paths(test_project_path)
    print(f"Erkannte Scan-Pfade:")
    for path in scan_paths:
        print(f"  - {path}")
    
    print(f"\nInsgesamt {len(scan_paths)} Pfade erkannt.")

if __name__ == "__main__":
    test_project_analysis()