from pathlib import Path
from typing import List, Dict, Any, Optional
from src.models.element import CodeElement, DocElement
from .chroma_updater import ChromaUpdater
from src.core.service_config import ServiceConfig
from src.quality.quality_manager import DocumentationQualityManager
from src.utils.name_generator import UniqueNameGenerator
import shutil
import tempfile
import os

class UpdaterEngine:
    def __init__(self, config_path: str = "./service_config.json"):
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True)
        # Lade oder erstelle die Service-Konfiguration
        self.service_config = ServiceConfig.load_from_file(config_path)
        self.chroma_updater = ChromaUpdater(self.service_config)
        self.quality_manager = DocumentationQualityManager()
        self.name_generator = UniqueNameGenerator()
    
    def backup_file(self, file_path: str) -> str:
        """Erstellt ein Backup der Datei und gibt den Pfad zum Backup zurück"""
        source_path = Path(file_path)
        backup_path = self.backup_dir / f"{source_path.name}.{os.getpid()}.backup"
        shutil.copy2(source_path, backup_path)
        return str(backup_path)
    
    def update_documentation(self, file_path: str, new_content: str) -> bool:
        """Aktualisiert eine Dokumentationsdatei mit neuem Inhalt"""
        try:
            # Erstelle Backup
            backup_path = self.backup_file(file_path)
            print(f"Backup erstellt: {backup_path}")
            
            # Aktualisiere die Datei
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Dokumentationsdatei aktualisiert: {file_path}")
            return True
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Datei {file_path}: {e}")
            return False
    
    def generate_documentation_for_code(self, code_element: CodeElement, llm_client: Any, project_root: str = None) -> Optional[str]:
        """Generiert Dokumentation für ein Code-Element mit Hilfe des LLM"""
        if not llm_client:
            print("Kein LLM-Client zur Verfügung - kann keine Dokumentation generieren")
            return None

        # Hole relevanten Kontext aus ChromaDB
        context_info = self._get_context_from_chroma(code_element, project_root)

        # Erstelle einen verbesserten Prompt für die Dokumentation
        prompt = f"""
        Du bist ein erfahrener Software-Dokumentationsspezialist. Erstelle eine hochwertige Dokumentation für das folgende Code-Element basierend auf dem bereitgestellten Kontext und den Projekt-Stil-Richtlinien.

        Projekt-Kontext (aus ähnlichen Elementen im Projekt):
        {context_info}

        Code-Element Details:
        - Name: {code_element.name}
        - Typ: {code_element.type.value if code_element.type else 'unbekannt'}
        - Signatur: {code_element.signature or 'nicht verfügbar'}
        - Parameter: {', '.join([str(p) for p in code_element.parameters]) if code_element.parameters else 'keine'}
        - Rückgabetyp: {code_element.return_type or 'nicht spezifiziert'}
        - Docstring: {code_element.docstring or 'nicht vorhanden'}
        - API-Info: {code_element.api_info or 'nicht zutreffend'}
        - Datei: {code_element.file_path}
        - Code-Snippet: {code_element.code_snippet or 'nicht verfügbar'}

        Bitte erstelle eine klare, professionelle Dokumentation im Markdown-Format mit folgender Struktur:

        ## {code_element.name}

        ### Beschreibung
        [Klare, verständliche Beschreibung der Funktion/Klasse/Methoden Zweck und Verwendung]

        ### Parameter
        [Tabelle oder Liste mit Parameternamen, Typen und Beschreibungen]

        ### Rückgabewert
        [Beschreibung des Rückgabewerts und dessen Typ]

        ### Beispiel
        [Ein oder zwei klare Beisele zur Verwendung, wenn möglich]

        ### Weitere Informationen
        [Zusätzliche relevante Informationen wie Ausnahmen, Seiteneffekte, etc.]

        Beachte den Stil und die Formatierung des bestehenden Projekts. Verwende korrektes Markdown und schreibe verständlich für andere Entwickler.
        """

        # Generiere die Dokumentation mit dem konfigurierten LLM-Modell
        try:
            generated_doc = llm_client.generate(self.service_config.llm_model, prompt)
            return generated_doc
        except Exception as e:
            print(f"Fehler bei der Generierung der Dokumentation: {e}")
            return None

    def _get_context_from_chroma(self, code_element: CodeElement, project_root: str = None) -> str:
        """Holt relevanten Kontext aus ChromaDB basierend auf dem Code-Element"""
        try:
            # Verwende den ChromaUpdater für die semantische Suche
            # Dies nutzt die gleiche ChromaDB-Instanz wie die update_chroma_db Funktion
            from src.chroma.client import ChromaDBClient

            # Erstelle temporären Client (in einer vollständigen Implementierung
            # würde man den bestehenden client von chroma_updater nutzen)
            chroma_client = ChromaDBClient(
                host=self.service_config.chroma_host,
                port=self.service_config.chroma_port,
                timeout=self.service_config.chroma_timeout
            )

            # Prüfe Verbindung
            if not chroma_client.health_check():
                return "ChromaDB ist nicht erreichbar"

            # Erstelle Suchabfrage basierend auf dem Code-Element
            search_query = f"{code_element.name} {code_element.signature or ''} {code_element.type.value if code_element.type else ''}"

            # Suche in der entsprechenden Collection (basierend auf Projekt-Pfad)
            # FIX: Verwende project_root falls verfügbar, sonst fallback auf code_element.project_path
            # Dies verhindert Fragmentierung in viele kleine Collections
            base_path = project_root if project_root else code_element.project_path
            project_name = Path(base_path).name if base_path else "default"
            collection_name = f"{project_name}_code"
            
            # Debug output
            print(f"🔍 Suche Kontext in Collection: {collection_name}")

            # Führe die Abfrage durch (auto_create=True erstellt die Collection, falls sie nicht existiert)
            results = chroma_client.query_collection(
                collection_name=collection_name,
                query=search_query,
                n_results=5,  # Hole die 5 ähnlichsten Ergebnisse
                auto_create=True  # Erstelle Collection automatisch, falls sie nicht existiert
            )

            if results and 'documents' in results and results['documents']:
                # Extrahiere die relevantesten Dokumente
                relevant_docs = results['documents'][0]  # Erste Ergebnismenge
                if relevant_docs:
                    return "\n".join([doc[:500] for doc in relevant_docs if doc])  # Begrenze Länge
                else:
                    return "Keine relevanten Kontext-Informationen gefunden"
            else:
                return "Keine relevanten Kontext-Informationen gefunden"

        except Exception as e:
            print(f"Fehler beim Abrufen des Kontexts aus ChromaDB: {e}")
            return f"Fehler beim Abrufen des Kontexts aus ChromaDB: {str(e)}"
    
    def update_chroma_db(self, code_elements: List[CodeElement], doc_elements: List[DocElement], project_path: str) -> bool:
        """
        Aktualisiert die ChromaDB mit den aktuellen Code- und Dokumentationselementen
        """
        return self.chroma_updater.update_chroma_with_elements(code_elements, doc_elements, project_path)

    def generate_documentation_updates(self, discrepancies: Dict[str, Any], llm_client: Any, output_dir: str = "./docs", project_path: str = None) -> Dict[str, Any]:
        """
        Generiert Dokumentations-Updates basierend auf Diskrepanzen und speichert sie in Dateien

        Args:
            discrepancies: Dictionary mit Diskrepanzen (von matcher.py)
            llm_client: Instanz des LLM-Clients
            output_dir: Verzeichnis für die generierten Dokumentationsdateien
            project_path: Pfad zum Root-Projekt (für Kontext-Lookup)

        Returns:
            Dictionary mit Ergebnissen der Generierung
        """
        results = {
            'generated_files': [],
            'errors': [],
            'skipped': []
        }

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Generiere Dokumentation für undokumentierten Code
        undocumented = discrepancies.get('undocumented_code', [])
        total_items = len(undocumented)

        print(f"\n{'='*60}")
        print(f"📝 Starte Dokumentations-Generierung für {total_items} Code-Elemente")
        print(f"{'='*60}\n")

        for idx, code_element in enumerate(undocumented, 1):
            try:
                # Fortschrittsanzeige
                print(f"[{idx}/{total_items}] Verarbeite: {code_element.name} ({code_element.type.value if code_element.type else 'unknown'})")

                # Verwende den UniqueNameGenerator für eindeutige Dateinamen
                filename = self.name_generator.generate_unique_filename_from_element(
                    element_name=code_element.name,
                    element_type=code_element.type.value if code_element.type else 'unknown',
                    source_file_path=code_element.file_path or str(output_path)
                )
                filepath = output_path / filename

                # SKIP: Wenn Datei bereits existiert
                if filepath.exists():
                    print(f"    ⏭️  Übersprungen (existiert): {filepath.name}")
                    results['skipped'].append(f"Bereits vorhanden: {code_element.name}")
                    continue

                # Generiere Dokumentation für das Code-Element
                generated_doc = self.generate_documentation_for_code(code_element, llm_client, project_path)

                if generated_doc:
                    # Bewertung der Dokumentationsqualität
                    quality_score = self.quality_manager.evaluate_single_documentation(generated_doc, code_element)

                    # Nur speichern, wenn die Qualität über der Schwelle liegt
                    if quality_score.overall_score >= self.quality_manager.quality_threshold:
                        # Speichere die generierte Dokumentation
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(generated_doc)

                        results['generated_files'].append({
                            'path': str(filepath),
                            'quality_score': quality_score.overall_score,
                            'element_name': code_element.name
                        })
                        print(f"    ✅ Gespeichert (Qualität: {quality_score.overall_score:.2f}): {filepath.name}")
                    else:
                        results['skipped'].append({
                            'element_name': code_element.name,
                            'reason': f"Qualität unter Schwelle: {quality_score.overall_score:.2f} < {self.quality_manager.quality_threshold}",
                            'quality_score': quality_score.overall_score
                        })
                        print(f"    ⚠️  Übersprungen (Qualität: {quality_score.overall_score:.2f} < {self.quality_manager.quality_threshold}): {code_element.name}")

                        # Gebe Feedback für Verbesserungen aus
                        if quality_score.feedback:
                            print(f"       Feedback: {quality_score.feedback[0] if quality_score.feedback else 'Kein Feedback'}")
                else:
                    results['skipped'].append({
                        'element_name': code_element.name,
                        'reason': "Keine Dokumentation generiert"
                    })
                    print(f"    ⚠️  Übersprungen: {code_element.name}")

            except Exception as e:
                error_msg = f"Fehler bei der Generierung für {code_element.name}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"    ❌ Fehler: {str(e)[:100]}")

        # Zusammenfassung
        print(f"\n{'='*60}")
        print(f"✅ Dokumentations-Generierung abgeschlossen!")
        print(f"{'='*60}")
        print(f"📊 Statistik:")
        print(f"   • Generiert:     {len(results['generated_files'])} Dateien")
        print(f"   • Übersprungen:  {len(results['skipped'])} Elemente")
        print(f"   • Fehler:        {len(results['errors'])} Fehler")

        # Detaillierte Qualitätssummary, falls Dokumentationen generiert wurden
        if results['generated_files']:
            total_quality = sum(file.get('quality_score', 0) for file in results['generated_files'])
            avg_quality = total_quality / len(results['generated_files']) if results['generated_files'] else 0
            print(f"   • Durchschn. Qualität: {avg_quality:.2f}")
        print(f"{'='*60}\n")

        return results

    def update_existing_documentation(self, discrepancies: Dict[str, Any], llm_client: Any, project_path: str = None) -> Dict[str, Any]:
        """
        Aktualisiert bestehende Dokumentationsdateien basierend auf Diskrepanzen

        Args:
            discrepancies: Dictionary mit Diskrepanzen (von matcher.py)
            llm_client: Instanz des LLM-Clients
            project_path: Pfad zum Root-Projekt (für Kontext-Lookup)

        Returns:
            Dictionary mit Ergebnissen der Aktualisierung
        """
        results = {
            'updated_files': [],
            'errors': [],
            'skipped': []
        }

        # Aktualisiere bestehende Dokumentation basierend auf mismatched Elementen
        for mismatch in discrepancies.get('mismatched_elements', []):
            try:
                code_element = mismatch.get('code') if isinstance(mismatch, dict) else None
                doc_element = mismatch.get('documentation') if isinstance(mismatch, dict) else None

                if code_element and doc_element:
                    # Generiere verbesserte Dokumentation basierend auf aktuellem Code
                    improved_doc = self.generate_documentation_for_code(code_element, llm_client, project_path)

                    if improved_doc:
                        # Erstelle Backup der originalen Datei
                        backup_path = self.backup_file(doc_element.file_path)

                        # Aktualisiere die Dokumentationsdatei
                        success = self.update_documentation(doc_element.file_path, improved_doc)

                        if success:
                            results['updated_files'].append({
                                'file': doc_element.file_path,
                                'backup': backup_path,
                                'element': code_element.name
                            })
                        else:
                            results['errors'].append(f"Fehler beim Aktualisieren von {doc_element.file_path}")
                    else:
                        results['skipped'].append(f"Keine verbesserte Dokumentation generiert für {code_element.name}")
                else:
                    # Falls mismatch nicht das erwartete Format hat
                    if hasattr(mismatch, '__dict__'):
                        print(f"Unbekanntes Mismatch-Format: {mismatch.__dict__}")
                    else:
                        print(f"Unbekanntes Mismatch-Format: {mismatch}")

            except Exception as e:
                error_msg = f"Fehler bei der Aktualisierung für Mismatch: {str(e)}"
                results['errors'].append(error_msg)
                print(error_msg)

        return results

    def integrate_documentation_in_files(self, discrepancies: Dict[str, Any], llm_client: Any, project_path: str) -> Dict[str, Any]:
        """
        Integriert KI-generierte Dokumentation direkt in bestehende Projektdateien (z.B. Markdown-Dateien)

        Args:
            discrepancies: Dictionary mit Diskrepanzen (von matcher.py)
            llm_client: Instanz des LLM-Clients
            project_path: Pfad zum Projekt, in dem Dateien aktualisiert werden sollen

        Returns:
            Dictionary mit Ergebnissen der Integration
        """
        results = {
            'integrated_elements': [],
            'errors': [],
            'skipped': []
        }

        project_path = Path(project_path)

        # Verarbeite undokumentierten Code, um ihn in die passenden Dokumentationsdateien zu integrieren
        for code_element in discrepancies.get('undocumented_code', []):
            try:
                # Generiere Dokumentation für das Code-Element
                generated_doc = self.generate_documentation_for_code(code_element, llm_client)

                if generated_doc:
                    # Bestimme die passende Dokumentationsdatei basierend auf dem Dateipfad des Code-Elements
                    # Wenn das Code-Element aus einer Python-Datei kommt, suchen wir eine entsprechende .md-Datei
                    code_file_path = Path(code_element.file_path)

                    # Bestimme die zugehörige Dokumentationsdatei
                    doc_file_path = self._determine_doc_file_path(code_file_path, project_path)

                    if doc_file_path and doc_file_path.exists():
                        # Lese die bestehende Dokumentationsdatei
                        with open(doc_file_path, 'r', encoding='utf-8') as f:
                            existing_content = f.read()

                        # Erstelle Backup
                        backup_path = self.backup_file(str(doc_file_path))

                        # Füge die neue Dokumentation zum bestehenden Inhalt hinzu
                        # In einer vollständigen Implementierung würde man klüger entscheiden, wo genau
                        # die neue Dokumentation eingefügt werden soll (z.B. nach bestimmten Headern)
                        updated_content = existing_content + "\n\n" + generated_doc

                        # Schreibe den aktualisierten Inhalt zurück
                        with open(doc_file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)

                        results['integrated_elements'].append({
                            'element': code_element.name,
                            'file': str(doc_file_path),
                            'backup': backup_path
                        })

                        print(f"Dokumentation für {code_element.name} in {doc_file_path} integriert")
                    else:
                        # Wenn keine passende Dokumentationsdatei gefunden wurde, erstelle eine neue
                        new_doc_path = self._create_new_doc_file(code_element, project_path, generated_doc)
                        if new_doc_path:
                            results['integrated_elements'].append({
                                'element': code_element.name,
                                'file': str(new_doc_path),
                                'backup': None,  # Kein Backup, da neue Datei
                                'new_file': True
                            })
                            print(f"Neue Dokumentationsdatei erstellt: {new_doc_path}")
                        else:
                            results['skipped'].append(f"Konnte keine Dokumentationsdatei für {code_element.name} erstellen")
                else:
                    results['skipped'].append(f"Keine Dokumentation generiert für {code_element.name}")

            except Exception as e:
                error_msg = f"Fehler bei der Integration für {code_element.name}: {str(e)}"
                results['errors'].append(error_msg)
                print(error_msg)

        return results

    def _determine_doc_file_path(self, code_file_path: Path, project_path: Path) -> Path:
        """
        Bestimmt die passende Dokumentationsdatei für eine gegebene Code-Datei
        """
        # Ersetze den Code-Datei-Ordner durch einen docs-Ordner wenn vorhanden
        # oder füge einen suffix hinzu wie z.B. _docs.md

        # Versuche verschiedene Muster:
        # 1. Suche nach einem docs-Ordner im gleichen Verzeichnis oder Projektwurzel
        possible_docs_dirs = [
            project_path / "docs",
            project_path / "documentation",
            code_file_path.parent / "docs",
            code_file_path.parent
        ]

        doc_filename = code_file_path.stem + ".md"

        for docs_dir in possible_docs_dirs:
            doc_file = docs_dir / doc_filename
            if doc_file.exists():
                return doc_file

        # Wenn keine bestehende Datei gefunden wurde, gib den Pfad für eine neue Datei zurück
        default_docs_dir = project_path / "docs"
        default_docs_dir.mkdir(exist_ok=True)
        return default_docs_dir / doc_filename

    def _create_new_doc_file(self, code_element: CodeElement, project_path: Path, content: str) -> Path:
        """
        Erstellt eine neue Dokumentationsdatei für ein Code-Element
        """
        try:
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)

            # Erstelle Dateinamen basierend auf dem Code-Element
            safe_name = "".join(c for c in code_element.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()

            filename = f"{safe_name}.md"
            filepath = docs_dir / filename

            # Stelle sicher, dass der Dateiname einzigartig ist
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                name_part = original_filepath.stem
                suffix_part = original_filepath.suffix
                filepath = docs_dir / f"{name_part}_{counter}{suffix_part}"
                counter += 1

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return filepath
        except Exception as e:
            print(f"Fehler beim Erstellen der Dokumentationsdatei: {e}")
            return None