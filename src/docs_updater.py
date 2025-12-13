import argparse
from pathlib import Path
from src.core.config_manager import ConfigManager
from src.core.project_analyzer import ProjectAnalyzer
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine

def main():
    parser = argparse.ArgumentParser(description="Documentation Auto-Update Tool")
    parser.add_argument("project_path", help="Pfad zum zu scannenden Projekt")
    parser.add_argument("--config", help="Pfad zur Konfigurationsdatei")
    parser.add_argument("--service-config", help="Pfad zur Service-Konfigurationsdatei (LLM, ChromaDB)")
    parser.add_argument("--mode", choices=["scan", "analyze", "update", "dry-run"], 
                       default="scan", help="Ausführungsmodus")
    parser.add_argument("--output", help="Ausgabeverzeichnis für Ergebnisse")
    
    args = parser.parse_args()
    
    # Konfiguration laden
    config_manager = ConfigManager(args.config)
    config = config_manager.get_effective_config()
    
    # Projekt analysieren und ggf. Konfiguration anpassen
    analyzer = ProjectAnalyzer(config)
    project_type = analyzer.detect_project_type(args.project_path)
    print(f"Erkannter Projekttyp: {project_type}")
    
    # Scanner initialisieren und Projekt scannen
    scanner = UniversalScanner(config)
    print("Starte Projekt-Scan...")
    results = scanner.scan_project(args.project_path)
    
    print(f"Scan abgeschlossen. Gefunden: {results['scan_summary']['total_files_scanned']} Dateien")
    
    if args.mode in ["analyze", "update", "dry-run"]:
        matcher = MatcherEngine()
        discrepancies = matcher.find_discrepancies(
            results['code_elements'],
            results['doc_elements']
        )
        
        print(f"Gefundene Diskrepanzen:")
        print(f"- Undokumentierter Code: {len(discrepancies['undocumented_code'])}")
        print(f"- Veraltete Dokumentation: {len(discrepancies['outdated_documentation'])}")
        print(f"- Nicht übereinstimmende Elemente: {len(discrepancies['mismatched_elements'])}")
        
        if args.mode in ["update", "dry-run"]:
            print("Update-Funktionalität würde hier implementiert werden...")
            if args.mode == "dry-run":
                print("(Trockenlauf - keine tatsächlichen Änderungen werden vorgenommen)")
    
    # Ergebnisse speichern
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Speichere Ergebnisse in JSON-Datei
        import json
        with open(output_path / "scan_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Ergebnisse gespeichert unter: {output_path / 'scan_results.json'}")
    
    # ChromaDB Aktualisierung nach dem Scannen und ggf. Update
    if args.mode in ["scan", "analyze", "update", "dry-run"]:
        print("Starte ChromaDB-Aktualisierung...")
        updater = UpdaterEngine(config_path=args.service_config or "./service_config.json")
        success = updater.update_chroma_db(
            results['code_elements'],
            results['doc_elements'],
            args.project_path
        )
        if success:
            print("ChromaDB erfolgreich aktualisiert")
        else:
            print("Fehler bei der ChromaDB-Aktualisierung")

if __name__ == "__main__":
    main()