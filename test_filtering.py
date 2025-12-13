import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config_manager import ConfigManager
from src.scanner.file_handler import FileHandler
from pathlib import Path

def test_file_filtering():
    """Testet die verbesserte Dateifilterung, die .gitignore und venv/node_modules berücksichtigt"""
    print("Teste verbesserte Dateifilterung...")
    
    # Erstelle Config und FileHandler
    config_manager = ConfigManager()
    config = config_manager.get_effective_config()
    file_handler = FileHandler(config)
    
    # Teste mit dem Testprojekt
    test_project_path = Path("test_project")
    
    # Hole die gefilterten Dateien
    filtered_files = file_handler.get_filtered_files(test_project_path)
    
    print(f"Gefundene Dateien (nach Filterung):")
    for file_path in filtered_files:
        print(f"  - {file_path}")
    
    print(f"\nGesamt gefundene Dateien: {len(filtered_files)}")
    
    # Überprüfe, dass bestimmte unerwünschte Dateien/Verzeichnisse nicht enthalten sind
    unwanted_paths = []
    for file_path in filtered_files:
        file_str = str(file_path).lower()
        if any(unwanted in file_str for unwanted in ['venv/', 'node_modules/', '__pycache__']):
            unwanted_paths.append(file_path)
    
    if unwanted_paths:
        print(f"\nACHTUNG: Folgende unerwünschte Dateien wurden trotz Filterung gefunden:")
        for path in unwanted_paths:
            print(f"  - {path}")
    else:
        print(f"\n✓ Alle unerwünschten Dateien (venv, node_modules, __pycache__) wurden korrekt gefiltert!")

if __name__ == "__main__":
    test_file_filtering()