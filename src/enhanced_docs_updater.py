#!/usr/bin/env python3
"""
Erweiterte Version der Documentation Auto-Update Tool (DAUT) Hauptanwendung
mit manueller und automatischer KI-Steuerung
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.core.config_manager import ConfigManager
from src.core.project_analyzer import ProjectAnalyzer
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine
from src.llm.client import OllamaClient
from src.models.element import CodeElement, ElementType
from src.utils.structured_logging import get_logger

def main():
    # Initialisiere strukturiertes Logging
    logger = get_logger("daut.enhanced_docs_updater")

    parser = argparse.ArgumentParser(description="Documentation Auto-Update Tool")
    parser.add_argument("project_path", help="Pfad zum zu scannenden Projekt")
    parser.add_argument("--config", help="Pfad zur Konfigurationsdatei")
    parser.add_argument("--service-config", help="Pfad zur Service-Konfigurationsdatei (LLM, ChromaDB)")
    parser.add_argument("--mode", choices=["scan", "analyze", "update", "dry-run", "ai-generate"],
                       default="scan", help="Ausführungsmodus")
    parser.add_argument("--output", help="Ausgabeverzeichnis für Ergebnisse")
    parser.add_argument("--ai-auto", action="store_true",
                        help="Automatische KI-Generierung für alle Diskrepanzen (nur im ai-generate Modus)")
    parser.add_argument("--ai-selective", nargs="+", type=int,
                        help="Selektive KI-Generierung für bestimmte Diskrepanz-Indizes (nur im ai-generate Modus)")

    args = parser.parse_args()

    # Logge den Start des Programms
    logger.info("Enhanced DAUT gestartet", extra_data={
        "project_path": args.project_path,
        "mode": args.mode,
        "config_file": args.config,
        "ai_auto": args.ai_auto,
        "ai_selective": args.ai_selective
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

    if args.mode in ["analyze", "update", "dry-run", "ai-generate"]:
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

        # Speichere Diskrepanzen für späteren Zugriff
        if args.output:
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            discrepancies_file = output_path / "discrepancies.json"
            with open(discrepancies_file, "w", encoding="utf-8") as f:
                json.dump(discrepancies, f, indent=2, default=str)
            logger.info(f"Diskrepanzen gespeichert", extra_data={"output_path": str(discrepancies_file)})

        # KI-Generierungsmodus
        if args.mode == "ai-generate":
            logger.info("Starte KI-Generierungsmodus", extra_data={"project_path": args.project_path})
            handle_ai_generation_mode(discrepancies, args)

    # Ergebnisse speichern
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Speichere Ergebnisse in JSON-Datei
        with open(output_path / "scan_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Ergebnisse gespeichert", extra_data={"output_path": str(output_path / 'scan_results.json')})

    # ChromaDB Aktualisierung nach dem Scannen und ggf. Update
    if args.mode in ["scan", "analyze", "update", "dry-run", "ai-generate"]:
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

def handle_ai_generation_mode(discrepancies: Dict[str, Any], args: argparse.Namespace):
    """Behandelt den KI-Generierungsmodus"""
    logger = get_logger("daut.ai_generation")
    print("\n=== KI-Dokumentationsgenerierungsmodus ===")
    logger.info("Starte KI-Dokumentationsgenerierungsmodus", extra_data={
        "discrepancies_summary": {
            "undocumented_code_count": len(discrepancies.get('undocumented_code', [])),
            "outdated_documentation_count": len(discrepancies.get('outdated_documentation', [])),
            "mismatched_elements_count": len(discrepancies.get('mismatched_elements', []))
        }
    })

    # Prüfe Ollama-Verbindung
    ollama_client = OllamaClient()
    if not ollama_client.health_check():
        logger.error("Ollama nicht verfügbar - kann keine KI-Dokumentation generieren")
        print("✗ Ollama nicht verfügbar - kann keine KI-Dokumentation generieren")
        return

    logger.info("Ollama-Verbindung erfolgreich hergestellt")
    print("✓ Ollama-Verbindung erfolgreich")

    # Initialisiere UpdaterEngine
    updater = UpdaterEngine()

    # Verarbeite undokumentierten Code
    undocumented_code = discrepancies.get('undocumented_code', [])

    if not undocumented_code:
        logger.info("Kein undokumentierter Code gefunden")
        print("Kein undokumentierter Code gefunden")
        return

    logger.info(f"Verarbeite undokumentierten Code", extra_data={
        "undocumented_code_count": len(undocumented_code)
    })
    print(f"\nGefundener undokumentierter Code ({len(undocumented_code)} Elemente):")
    for i, code_elem in enumerate(undocumented_code):
        print(f"{i+1}. {code_elem.type.value}: {code_elem.name} ({code_elem.file_path})")

    # Entscheide, welche Elemente verarbeitet werden sollen
    elements_to_process = []

    if args.ai_auto:
        # Automatischer Modus: Verarbeite alle Elemente
        logger.info("Automatischer Modus aktiviert", extra_data={"total_elements": len(undocumented_code)})
        print("\nAutomatischer Modus: Verarbeite alle undokumentierten Elemente...")
        elements_to_process = [(i, elem) for i, elem in enumerate(undocumented_code)]
    elif args.ai_selective:
        # Selektiver Modus: Verarbeite nur ausgewählte Elemente
        logger.info("Selektiver Modus aktiviert", extra_data={"selected_indices": args.ai_selective})
        print(f"\nSelektiver Modus: Verarbeite Elemente {args.ai_selective}...")
        elements_to_process = [(i, undocumented_code[i]) for i in args.ai_selective if 0 <= i < len(undocumented_code)]
    else:
        # Interaktiver Modus: Frage Benutzer
        logger.info("Interaktiver Modus aktiviert")
        print("\nInteraktiver Modus - wählen Sie die zu verarbeitenden Elemente:")
        selected_indices = []

        for i, code_elem in enumerate(undocumented_code[:10]):  # Zeige nur die ersten 10
            choice = input(f"Generiere KI-Dokumentation für {code_elem.type.value}: {code_elem.name}? (j/N/q): ").strip().lower()
            if choice == 'q':
                break
            elif choice == 'j' or choice == 'y':
                selected_indices.append(i)

        elements_to_process = [(i, undocumented_code[i]) for i in selected_indices]

    # Generiere KI-Dokumentation für ausgewählte Elemente
    if elements_to_process:
        logger.info(f"Starte Dokumentationsgenerierung", extra_data={
            "elements_to_process": len(elements_to_process)
        })
        print(f"\nGeneriere KI-Dokumentation für {len(elements_to_process)} Elemente...")

        generated_docs = []
        for idx, (orig_idx, code_elem) in enumerate(elements_to_process):
            print(f"\n[{idx+1}/{len(elements_to_process)}] Generiere Dokumentation für: {code_elem.name}")

            generated_doc = updater.generate_documentation_for_code(code_elem, ollama_client)

            if generated_doc:
                generated_docs.append({
                    "original_index": orig_idx,
                    "name": code_elem.name,
                    "type": code_elem.type.value,
                    "file_path": code_elem.file_path,
                    "generated_documentation": generated_doc
                })
                logger.debug(f"Dokumentation generiert", extra_data={
                    "element_name": code_elem.name,
                    "element_type": code_elem.type.value
                })
                print(f"✓ Dokumentation generiert für {code_elem.name}")
            else:
                logger.warning(f"Fehler bei der Generierung", extra_data={
                    "element_name": code_elem.name,
                    "element_type": code_elem.type.value
                })
                print(f"✗ Fehler bei der Generierung für {code_elem.name}")

        # Speichere generierte Dokumentation
        if generated_docs and args.output:
            output_path = Path(args.output)
            ai_docs_file = output_path / "ai_generated_documentation.json"
            with open(ai_docs_file, "w", encoding="utf-8") as f:
                json.dump(generated_docs, f, indent=2, ensure_ascii=False)
            logger.info(f"KI-Dokumentation gespeichert", extra_data={
                "output_file": str(ai_docs_file),
                "generated_docs_count": len(generated_docs)
            })
            print(f"\nKI-generierte Dokumentation gespeichert unter: {ai_docs_file}")

            # Erstelle auch Markdown-Dateien
            for doc in generated_docs:
                md_file = output_path / f"{doc['name']}_ai_generated.md"
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(f"# KI-generierte Dokumentation für {doc['name']}\n\n")
                    f.write(doc["generated_documentation"])
                logger.debug(f"Markdown-Dokumentation gespeichert", extra_data={
                    "file_path": str(md_file)
                })
                print(f"Markdown-Dokumentation gespeichert: {md_file}")
    else:
        logger.info("Keine Elemente zur Verarbeitung ausgewählt")
        print("Keine Elemente zur Verarbeitung ausgewählt")

if __name__ == "__main__":
    main()