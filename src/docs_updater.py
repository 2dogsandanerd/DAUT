import argparse
from pathlib import Path
from src.core.config_manager import ConfigManager
from src.core.project_analyzer import ProjectAnalyzer
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine
from src.utils.structured_logging import get_logger

def main():
    # Initialisiere strukturiertes Logging
    logger = get_logger("daut.docs_updater")

    parser = argparse.ArgumentParser(description="Documentation Auto-Update Tool")
    parser.add_argument("project_path", help="Pfad zum zu scannenden Projekt")
    parser.add_argument("--config", help="Pfad zur Konfigurationsdatei")
    parser.add_argument("--service-config", help="Pfad zur Service-Konfigurationsdatei (LLM, ChromaDB)")
    parser.add_argument("--mode", choices=["scan", "analyze", "update", "dry-run"],
                       default="scan", help="Ausführungsmodus")
    parser.add_argument("--output", help="Ausgabeverzeichnis für Ergebnisse")

    args = parser.parse_args()

    # Logge den Start des Programms
    logger.info("DAUT gestartet", extra_data={
        "project_path": args.project_path,
        "mode": args.mode,
        "config_file": args.config
    })

    # Konfiguration laden und an Projekt anpassen
    config_manager = ConfigManager(args.config, project_path=args.project_path)
    config = config_manager.get_effective_config()

    # Projekt analysieren und ggf. Konfiguration anpassen
    analyzer = ProjectAnalyzer(config)
    project_type = analyzer.detect_project_type(args.project_path)
    logger.info(f"Erkannter Projekttyp: {project_type}", extra_data={"project_type": project_type})
    
    # Scanner initialisieren und Projekt scannen
    scanner = UniversalScanner(config)
    logger.info("Starte Projekt-Scan", extra_data={"project_path": args.project_path})
    results = scanner.scan_project(args.project_path)

    logger.info(f"Scan abgeschlossen", extra_data={
        "total_files_scanned": results['scan_summary']['total_files_scanned'],
        "code_elements_found": len(results['code_elements']),
        "doc_elements_found": len(results['doc_elements'])
    })

    if args.mode in ["analyze", "update", "dry-run"]:
        matcher = MatcherEngine()
        logger.debug("Starte Diskrepanz-Analyse")
        discrepancies = matcher.find_discrepancies(
            results['code_elements'],
            results['doc_elements']
        )

        logger.info(f"Gefundene Diskrepanzen:", extra_data={
            "undocumented_code": len(discrepancies['undocumented_code']),
            "outdated_documentation": len(discrepancies['outdated_documentation']),
            "mismatched_elements": len(discrepancies['mismatched_elements'])
        })

        if args.mode in ["update", "dry-run"]:
            logger.info("Update-Funktionalität würde hier implementiert werden...")
            if args.mode == "dry-run":
                logger.info("(Trockenlauf - keine tatsächlichen Änderungen werden vorgenommen)")

    # Ergebnisse speichern
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Speichere Ergebnisse in JSON-Datei
        import json
        with open(output_path / "scan_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Ergebnisse gespeichert", extra_data={"output_path": str(output_path / 'scan_results.json')})

    # ChromaDB Aktualisierung nach dem Scannen und ggf. Update
    if args.mode in ["scan", "analyze", "update", "dry-run"]:
        logger.info("Starte ChromaDB-Aktualisierung...")
        updater = UpdaterEngine(config_path=args.service_config or "./service_config.json")
        success = updater.update_chroma_db(
            results['code_elements'],
            results['doc_elements'],
            args.project_path
        )
        if success:
            logger.info("ChromaDB erfolgreich aktualisiert")
        else:
            logger.error("Fehler bei der ChromaDB-Aktualisierung")

if __name__ == "__main__":
    main()