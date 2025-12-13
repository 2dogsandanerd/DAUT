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

def main():
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
    
    if args.mode in ["analyze", "update", "dry-run", "ai-generate"]:
        matcher = MatcherEngine()
        discrepancies = matcher.find_discrepancies(
            results['code_elements'],
            results['doc_elements']
        )
        
        print(f"Gefundene Diskrepanzen:")
        print(f"- Undokumentierter Code: {len(discrepancies['undocumented_code'])}")
        print(f"- Veraltete Dokumentation: {len(discrepancies['outdated_documentation'])}")
        print(f"- Nicht übereinstimmende Elemente: {len(discrepancies['mismatched_elements'])}")
        
        # Speichere Diskrepanzen für späteren Zugriff
        if args.output:
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            discrepancies_file = output_path / "discrepancies.json"
            with open(discrepancies_file, "w", encoding="utf-8") as f:
                json.dump(discrepancies, f, indent=2, default=str)
            print(f"Diskrepanzen gespeichert unter: {discrepancies_file}")
        
        # KI-Generierungsmodus
        if args.mode == "ai-generate":
            handle_ai_generation_mode(discrepancies, args)
    
    # Ergebnisse speichern
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Speichere Ergebnisse in JSON-Datei
        with open(output_path / "scan_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Ergebnisse gespeichert unter: {output_path / 'scan_results.json'}")
    
    # ChromaDB Aktualisierung nach dem Scannen und ggf. Update
    if args.mode in ["scan", "analyze", "update", "dry-run", "ai-generate"]:
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

def handle_ai_generation_mode(discrepancies: Dict[str, Any], args: argparse.Namespace):
    """Behandelt den KI-Generierungsmodus"""
    print("\n=== KI-Dokumentationsgenerierungsmodus ===")
    
    # Prüfe Ollama-Verbindung
    ollama_client = OllamaClient()
    if not ollama_client.health_check():
        print("✗ Ollama nicht verfügbar - kann keine KI-Dokumentation generieren")
        return
    
    print("✓ Ollama-Verbindung erfolgreich")
    
    # Initialisiere UpdaterEngine
    updater = UpdaterEngine()
    
    # Verarbeite undokumentierten Code
    undocumented_code = discrepancies.get('undocumented_code', [])
    
    if not undocumented_code:
        print("Kein undokumentierter Code gefunden")
        return
    
    print(f"\nGefundener undokumentierter Code ({len(undocumented_code)} Elemente):")
    for i, code_elem in enumerate(undocumented_code):
        print(f"{i+1}. {code_elem.type.value}: {code_elem.name} ({code_elem.file_path})")
    
    # Entscheide, welche Elemente verarbeitet werden sollen
    elements_to_process = []
    
    if args.ai_auto:
        # Automatischer Modus: Verarbeite alle Elemente
        print("\nAutomatischer Modus: Verarbeite alle undokumentierten Elemente...")
        elements_to_process = [(i, elem) for i, elem in enumerate(undocumented_code)]
    elif args.ai_selective:
        # Selektiver Modus: Verarbeite nur ausgewählte Elemente
        print(f"\nSelektiver Modus: Verarbeite Elemente {args.ai_selective}...")
        elements_to_process = [(i, undocumented_code[i]) for i in args.ai_selective if 0 <= i < len(undocumented_code)]
    else:
        # Interaktiver Modus: Frage Benutzer
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
                print(f"✓ Dokumentation generiert für {code_elem.name}")
            else:
                print(f"✗ Fehler bei der Generierung für {code_elem.name}")
        
        # Speichere generierte Dokumentation
        if generated_docs and args.output:
            output_path = Path(args.output)
            ai_docs_file = output_path / "ai_generated_documentation.json"
            with open(ai_docs_file, "w", encoding="utf-8") as f:
                json.dump(generated_docs, f, indent=2, ensure_ascii=False)
            print(f"\nKI-generierte Dokumentation gespeichert unter: {ai_docs_file}")
            
            # Erstelle auch Markdown-Dateien
            for doc in generated_docs:
                md_file = output_path / f"{doc['name']}_ai_generated.md"
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(f"# KI-generierte Dokumentation für {doc['name']}\n\n")
                    f.write(doc["generated_documentation"])
                print(f"Markdown-Dokumentation gespeichert: {md_file}")
    else:
        print("Keine Elemente zur Verarbeitung ausgewählt")

if __name__ == "__main__":
    main()