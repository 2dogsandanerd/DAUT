import streamlit as st
import tempfile
from pathlib import Path
import json
from src.core.config_manager import ConfigManager, ProjectConfig
from src.scanner.universal_scanner import UniversalScanner
from src.core.project_analyzer import ProjectAnalyzer
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine
from src.models.element import CodeElement, DocElement
from src.ui.components import display_filter_statistics, display_performance_statistics, create_export_options, display_file_browser, display_filter_management, display_directory_visualization
from src.ui.chroma_components import display_chroma_collection_management, display_chroma_status
from src.llm.client import OllamaClient
from src.core.coverage_checker import CoverageChecker

def main():
    st.set_page_config(page_title="Documentation Auto-Update Tool", layout="wide")
    st.title("Documentation Auto-Update Tool (DAUT)")
    
    # Zustand initialisieren
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = None
    if 'project_path' not in st.session_state:
        st.session_state.project_path = ""
    if 'config' not in st.session_state:
        st.session_state.config = ConfigManager()
    if 'chroma_client' not in st.session_state:
        from src.chroma.client import ChromaDBClient
        from src.core.service_config import ServiceConfig
        # Lade Service-Konfiguration
        service_config = ServiceConfig()
        st.session_state.chroma_client = ChromaDBClient(
            host=service_config.chroma_host,
            port=service_config.chroma_port,
            timeout=service_config.chroma_timeout,
            persist_directory=service_config.chroma_persist_directory
        )
    if 'service_config' not in st.session_state:
        from src.core.service_config import ServiceConfig
        st.session_state.service_config = ServiceConfig()
    
    # Sidebar für Konfiguration
    with st.sidebar:
        # Logo & Titel zuerst
        st.image("doc_file.png", width=100)
        st.title("DocUpdater")
        
        # Aktuelles Projekt
        if st.session_state.project_path:
            st.info(f"📁 **Projekt:**\n`{st.session_state.project_path}`")
            if st.button("🔄 Neues Projekt wählen"):
                st.session_state.project_path = ""
                st.session_state.scan_results = None
                st.rerun()
        
        st.markdown("---")
        
        # MCP Status Integration
        st.subheader("🔌 System Status")
        from src.ui.mcp_status import display_mcp_status_in_sidebar
        display_mcp_status_in_sidebar()
        
        st.markdown("---")
        
        # Projekt-Pfad Auswahl mit Dateibrowser
        st.subheader("Projekt-Pfad Auswahl")
        project_path = st.text_input("Projekt-Pfad", value=st.session_state.project_path, 
                                     help="Geben Sie den Pfad zum Projektordner ein oder verwenden Sie den unten stehenden Browser")
        
        # File browser button - This is a workaround since Streamlit doesn't have a native directory picker
        with st.expander("📁 Verzeichnis auswählen"):
            uploaded_file = st.file_uploader(
                "Laden Sie eine Datei aus dem Zielverzeichnis hoch (workaround für Verzeichnisauswahl):", 
                type=None, 
                accept_multiple_files=False
            )
            if uploaded_file is not None:
                # Get the directory of the uploaded file
                file_dir = Path(uploaded_file.name).parent.absolute()
                st.session_state.project_path = str(file_dir)
                st.success(f"Verzeichnis ausgewählt: {file_dir}")
        
        # Button to analyze project
        if st.button("Projekt analysieren"):
            if project_path and Path(project_path).exists():
                if not Path(project_path).is_dir():
                    st.error("Der angegebene Pfad ist kein Verzeichnis.")
                else:
                    # Aktualisiere die Konfiguration basierend auf dem Projektverzeichnis
                    st.session_state.config.config.update_for_project(project_path)

                    analyzer = ProjectAnalyzer(st.session_state.config.get_effective_config())
                    project_type = analyzer.detect_project_type(project_path)
                    st.session_state.project_path = project_path

                    # Update configuration based on project type if needed
                    config = st.session_state.config.get_effective_config()
                    if project_type.startswith('python'):
                        if not any(path in config.scan_paths for path in ['src', 'lib', 'app']):
                            config.scan_paths = analyzer.get_scan_paths(project_path)
                    elif project_type.startswith('javascript'):
                        if not any(path in config.scan_paths for path in ['src', 'lib', 'app']):
                            config.scan_paths = analyzer.get_scan_paths(project_path)

                    st.success(f"Projekttyp erkannt: {project_type}")
                    st.write(f"Scan-Pfade: {config.scan_paths}")
            else:
                st.error("Der angegebene Projekt-Pfad existiert nicht.")
    
    # Hauptbereich
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Analyse")

        if st.button("Projekt scannen", disabled=not st.session_state.project_path):
            if Path(st.session_state.project_path).exists():
                # Initialisiere den Fortschritts-Callback
                from src.scanner.progress_callback import ScanProgressCallback

                # Erstelle einen Fortschritts-Callback mit Streamlit-Integration
                progress_callback = ScanProgressCallback()

                def update_progress(current, total, description):
                    progress_value = current / max(1, total) if total > 0 else 0
                    progress_bar.progress(progress_value, text=f"{description} ({current}/{total})")

                # Setze die Callback-Funktion
                progress_callback.set_progress_callback(update_progress)

                # Initialisiere die Fortschrittsanzeige
                progress_bar = st.progress(0)

                config = st.session_state.config.get_effective_config()
                scanner = UniversalScanner(config, progress_callback=progress_callback)
                results = scanner.scan_project(st.session_state.project_path)
                st.session_state.scan_results = results

                st.success("Scan abgeschlossen!")

                # Entferne die Fortschrittsanzeige nach Abschluss
                progress_bar.empty()

        if st.session_state.scan_results:
            st.write(f"**Zusammenfassung:**")
            summary = st.session_state.scan_results['scan_summary']
            st.write(f"- Gesamte Dateien gescannt: {summary['total_files_scanned']}")
            st.write(f"- Code-Elemente gefunden: {summary['code_files']}")
            st.write(f"- Dokumentations-Elemente gefunden: {summary['doc_files']}")

            # Zeige Filterstatistiken
            if 'scan_report' in st.session_state.scan_results:
                with st.expander("Filterstatistiken"):
                    display_filter_statistics(st.session_state.scan_results['scan_report'])

            # Zeige Performance-Statistiken
            if 'performance_report' in st.session_state.scan_results:
                with st.expander("Performance-Statistiken"):
                    display_performance_statistics(st.session_state.scan_results['performance_report'])

            # Zeige Verzeichnisvisualisierung
            if st.session_state.scan_results:
                with st.expander("Verzeichnisstruktur"):
                    scan_report = st.session_state.scan_results.get('scan_report', {})
                    display_directory_visualization(st.session_state.project_path, scan_report)
    
    with col2:
        st.header("Ergebnisse")
        
        if st.session_state.scan_results:
            results = st.session_state.scan_results
            tab1, tab2 = st.tabs(["Code-Elemente", "Dokumentation"])
            
            with tab1:
                if results['code_elements']:
                    st.write(f"**{len(results['code_elements'])} Code-Elemente gefunden**")
                    for i, elem in enumerate(results['code_elements'][:10]):  # Erste 10 anzeigen
                        with st.expander(f"{elem.type.value}: {elem.name} ({elem.file_path})"):
                            st.write(f"**Signatur:** `{elem.signature}`" if elem.signature else "")
                            if elem.docstring:
                                st.write(f"**Docstring:** {elem.docstring[:200]}...")
                            if elem.api_info:
                                st.write(f"**API:** {elem.api_info}")
                
            with tab2:
                if results['doc_elements']:
                    st.write(f"**{len(results['doc_elements'])} Dokumentations-Elemente gefunden**")
                    for i, elem in enumerate(results['doc_elements'][:10]):  # Erste 10 anzeigen
                        with st.expander(f"{elem.type.value}: {elem.name}"):
                            st.write(f"**Inhalt:** {elem.content[:200]}..." if elem.content else "")
    
    # Matching und Diskrepanz-Analyse
    if st.session_state.scan_results:
        st.header("Diskrepanz-Analyse")
        if st.button("Diskrepanzen analysieren"):
            with st.spinner("Diskrepanzen werden analysiert..."):
                matcher = MatcherEngine()
                results = st.session_state.scan_results
                discrepancies = matcher.find_discrepancies(
                    results['code_elements'],
                    results['doc_elements']
                )
                
                st.session_state.discrepancies = discrepancies
                
                st.write(f"**Gefundene Diskrepanzen:**")
                st.write(f"- Undokumentierter Code: {len(discrepancies['undocumented_code'])}")
                st.write(f"- Veraltete Dokumentation: {len(discrepancies['outdated_documentation'])}")
                st.write(f"- Nicht übereinstimmende Elemente: {len(discrepancies['mismatched_elements'])}")
        
        # ChromaDB Aktualisierung
        st.header("ChromaDB-Aktualisierung")
        if st.button("ChromaDB aktualisieren"):
            with st.spinner("ChromaDB wird aktualisiert..."):
                updater = UpdaterEngine()
                success = updater.update_chroma_db(
                    st.session_state.scan_results['code_elements'],
                    st.session_state.scan_results['doc_elements'],
                    st.session_state.project_path
                )

                if success:
                    st.success("ChromaDB erfolgreich aktualisiert!")
                else:
                    st.error("Fehler bei der ChromaDB-Aktualisierung")

        # Dokumentations-Aktualisierung mit KI
        if st.session_state.get('discrepancies'):
            st.header("KI-gestützte Dokumentations-Aktualisierung")

            col1, col2 = st.columns(2)

            with col1:
                generate_new_docs = st.button("Neue Dokumentation generieren")

            with col2:
                update_existing_docs = st.button("Bestehende Dokumentation aktualisieren")

            # Dateiausgabe-Verzeichnis
            # Verwende das Projektverzeichnis als Basis
            default_output_dir = f"{st.session_state.project_path}/auto_docs"
            output_dir = st.text_input("Ausgabeverzeichnis für neue Dokumentation", value=default_output_dir)

            if generate_new_docs:
                # PRE-CHECK: Coverage vor Generierung
                st.subheader("📊 Coverage-Check (vor Generierung)")
                checker = CoverageChecker(st.session_state.project_path)
                pre_report = checker.check_coverage()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Klassen", f"{pre_report.documented_classes}/{pre_report.total_classes}")
                with col2:
                    st.metric("Fehlend", len(pre_report.missing_classes), delta=f"-{len(pre_report.missing_classes)}", delta_color="inverse")
                with col3:
                    st.metric("Coverage", f"{pre_report.coverage_percentage:.1f}%")

                if pre_report.missing_classes:
                    with st.expander(f"❌ {len(pre_report.missing_classes)} fehlende Klassen anzeigen"):
                        for cls in pre_report.missing_classes[:30]:
                            st.write(f"- {cls}")
                        if len(pre_report.missing_classes) > 30:
                            st.write(f"... und {len(pre_report.missing_classes) - 30} weitere")

                st.divider()

                with st.spinner("KI-Dokumentation wird generiert..."):

                    # Initialisiere Ollama-Client
                    ollama_client = OllamaClient()

                    if ollama_client.health_check():
                        st.info("Verbindung zu Ollama erfolgreich. Starte Dokumentations-Generierung...")

                        updater = UpdaterEngine()
                        results = updater.generate_documentation_updates(
                            st.session_state.discrepancies,
                            ollama_client,
                            output_dir=output_dir,
                            project_path=st.session_state.project_path # NEW: Pass unified project path
                        )

                        # Zeige Ergebnisse
                        if results['generated_files']:
                            st.success(f"{len(results['generated_files'])} Dokumentationsdateien erfolgreich generiert:")
                            for file_path in results['generated_files']:
                                st.write(f"- {file_path}")
                        else:
                            st.info("Keine neuen Dokumentationen generiert.")

                        if results['errors']:
                            st.error(f"Fehler bei der Generierung: {len(results['errors'])}")
                            for error in results['errors']:
                                st.write(f"- {error}")

                        if results['skipped']:
                            st.warning(f"Übersprungene Elemente: {len(results['skipped'])}")
                            for skip in results['skipped']:
                                st.write(f"- {skip}")

                        # POST-CHECK: Coverage nach Generierung
                        st.divider()
                        st.subheader("📊 Coverage-Check (nach Generierung)")
                        post_report = checker.check_coverage()

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Klassen", f"{post_report.documented_classes}/{post_report.total_classes}",
                                     delta=f"+{post_report.documented_classes - pre_report.documented_classes}")
                        with col2:
                            st.metric("Noch fehlend", len(post_report.missing_classes),
                                     delta=f"{len(post_report.missing_classes) - len(pre_report.missing_classes)}")
                        with col3:
                            st.metric("Coverage", f"{post_report.coverage_percentage:.1f}%",
                                     delta=f"+{post_report.coverage_percentage - pre_report.coverage_percentage:.1f}%")

                        if post_report.is_complete():
                            st.success("✅ 100% COVERAGE ERREICHT!")
                        else:
                            st.warning(f"⚠️ Noch {len(post_report.missing_classes)} Klassen fehlen. Bitte erneut generieren.")
                            if post_report.missing_classes:
                                with st.expander("Verbleibende fehlende Klassen"):
                                    for cls in post_report.missing_classes:
                                        st.write(f"- {cls}")

                    else:
                        st.error("Keine Verbindung zu Ollama möglich. Bitte stellen Sie sicher, dass Ollama läuft und Modelle verfügbar sind.")

            if update_existing_docs:
                with st.spinner("Bestehende Dokumentation wird aktualisiert..."):

                    # Initialisiere Ollama-Client
                    ollama_client = OllamaClient()

                    if ollama_client.health_check():
                        st.info("Verbindung zu Ollama erfolgreich. Starte Dokumentations-Aktualisierung...")

                        updater = UpdaterEngine()
                        results = updater.update_existing_documentation(
                            st.session_state.discrepancies,
                            ollama_client,
                            project_path=st.session_state.project_path # NEW: Pass unified project path
                        )

                        # Zeige Ergebnisse
                        if results['updated_files']:
                            st.success(f"{len(results['updated_files'])} Dokumentationsdateien erfolgreich aktualisiert:")
                            for update_info in results['updated_files']:
                                st.write(f"- {update_info['file']} (Element: {update_info['element']})")
                        else:
                            st.info("Keine Dokumentationen aktualisiert.")

                        if results['errors']:
                            st.error(f"Fehler bei der Aktualisierung: {len(results['errors'])}")
                            for error in results['errors']:
                                st.write(f"- {error}")

                        if results['skipped']:
                            st.warning(f"Übersprungene Elemente: {len(results['skipped'])}")
                            for skip in results['skipped']:
                                st.write(f"- {skip}")
                    else:
                        st.error("Keine Verbindung zu Ollama möglich. Bitte stellen Sie sicher, dass Ollama läuft und Modelle verfügbar sind.")

        # Integration von KI-Dokumentation in bestehende Projektdateien
        if st.session_state.get('discrepancies'):
            st.header("Integration in Projektdateien")

            integrate_docs = st.button("KI-Dokumentation in Projektdateien integrieren")

            if integrate_docs:
                with st.spinner("KI-Dokumentation wird in Projektdateien integriert..."):

                    # Initialisiere Ollama-Client
                    ollama_client = OllamaClient()

                    if ollama_client.health_check():
                        st.info("Verbindung zu Ollama erfolgreich. Starte Dokumentations-Integration...")

                        updater = UpdaterEngine()
                        results = updater.integrate_documentation_in_files(
                            st.session_state.discrepancies,
                            ollama_client,
                            st.session_state.project_path
                        )

                        # Zeige Ergebnisse
                        if results['integrated_elements']:
                            st.success(f"{len(results['integrated_elements'])} Elemente erfolgreich integriert:")
                            for integration_info in results['integrated_elements']:
                                if integration_info.get('new_file'):
                                    st.write(f"- Neue Datei: {integration_info['file']} (Element: {integration_info['element']})")
                                else:
                                    st.write(f"- In bestehende Datei: {integration_info['file']} (Element: {integration_info['element']})")
                        else:
                            st.info("Keine Elemente integriert.")

                        if results['errors']:
                            st.error(f"Fehler bei der Integration: {len(results['errors'])}")
                            for error in results['errors']:
                                st.write(f"- {error}")

                        if results['skipped']:
                            st.warning(f"Übersprungene Elemente: {len(results['skipped'])}")
                            for skip in results['skipped']:
                                st.write(f"- {skip}")
                    else:
                        st.error("Keine Verbindung zu Ollama möglich. Bitte stellen Sie sicher, dass Ollama läuft und Modelle verfügbar sind.")

    # Filter-Management
    with st.expander("Filter-Verwaltung"):
        display_filter_management(st.session_state.config)

    # ChromaDB-Konfiguration und -Management
    with st.expander("ChromaDB-Konfiguration"):
        st.subheader("Speicherort-Einstellungen")

        current_persist_dir = st.session_state.service_config.chroma_persist_directory
        new_persist_dir = st.text_input(
            "ChromaDB Speicherort",
            value=current_persist_dir,
            help="Pfad zum ChromaDB Speicherverzeichnis. Kann relativ (./chromadb_data) oder absolut (/mnt/data/chroma) sein."
        )

        if st.button("Speicherort aktualisieren"):
            if new_persist_dir != current_persist_dir:
                st.session_state.service_config.chroma_persist_directory = new_persist_dir
                st.session_state.service_config.save_to_file('src/service_config.json')

                from src.chroma.client import ChromaDBClient
                st.session_state.chroma_client = ChromaDBClient(
                    host=st.session_state.service_config.chroma_host,
                    port=st.session_state.service_config.chroma_port,
                    timeout=st.session_state.service_config.chroma_timeout,
                    persist_directory=new_persist_dir
                )

                st.success(f"Speicherort aktualisiert: {new_persist_dir}")
                st.info("ChromaDB Client wurde neu initialisiert.")
                st.rerun()
            else:
                st.info("Keine Änderung am Speicherort.")

        st.info(f"Aktueller Speicherort: `{current_persist_dir}`")

    # ChromaDB-Status und -Management
    with st.expander("ChromaDB-Status und -Verwaltung"):
        display_chroma_status(service_config=st.session_state.service_config, chroma_client=st.session_state.chroma_client)
        display_chroma_collection_management(service_config=st.session_state.service_config, chroma_client=st.session_state.chroma_client)

    # Export-Funktionalität und erweiterte Optionen
    if st.session_state.scan_results:
        # Neue Export-Optionen mit der neuen Komponente
        create_export_options(
            st.session_state.scan_results.get('scan_report', {}),
            st.session_state.scan_results.get('performance_report', {})
        )

        # Standard-Export
        st.download_button(
            label="Ergebnisse exportieren",
            data=json.dumps(st.session_state.scan_results, indent=2, default=str),
            file_name="daut_scan_results.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()