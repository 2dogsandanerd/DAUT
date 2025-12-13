import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import json


def display_filter_statistics(scan_report: Dict[str, Any]):
    """
    Zeigt die Filterstatistiken im Streamlit-UI an

    Args:
        scan_report: Der Scan-Bericht vom UniversalScanner
    """
    if not scan_report or 'summary' not in scan_report:
        st.warning("Keine Scan-Daten verfügbar")
        return

    summary = scan_report['summary']

    # Hauptzusammenfassung
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gescannte Dateien", summary['total_files_scanned'])
    col2.metric("Eingeschlossene Dateien", summary['included_files'])
    col3.metric("Ausgeschlossene Dateien", summary['excluded_files'])
    col4.metric("Einschlussrate", f"{summary['inclusion_rate']:.2f}%")

    # Dateitypen-Verteilung
    st.subheader("Dateitypen-Verteilung")
    if scan_report.get('file_types'):
        file_types_data = {
            'Typ': list(scan_report['file_types'].keys()),
            'Anzahl': list(scan_report['file_types'].values())
        }
        df_types = pd.DataFrame(file_types_data)
        st.bar_chart(df_types.set_index('Typ'), use_container_width=True)

    # Dateierweiterungen
    st.subheader("Dateierweiterungen")
    if scan_report.get('file_extensions'):
        extensions_data = {
            'Erweiterung': list(scan_report['file_extensions'].keys()),
            'Anzahl': list(scan_report['file_extensions'].values())
        }
        df_ext = pd.DataFrame(extensions_data).nlargest(15, 'Anzahl')  # Nur Top 15
        st.bar_chart(df_ext.set_index('Erweiterung'), use_container_width=True)

    # Ausgeschlossene Verzeichnisse
    st.subheader("Ausgeschlossene Verzeichnisse")
    if scan_report.get('excluded_directories'):
        excluded_dirs_data = {
            'Verzeichnis': list(scan_report['excluded_directories'].keys()),
            'Anzahl': list(scan_report['excluded_directories'].values())
        }
        df_dirs = pd.DataFrame(excluded_dirs_data).nlargest(10, 'Anzahl')  # Nur Top 10
        st.bar_chart(df_dirs.set_index('Verzeichnis'), use_container_width=True)

    # Dateigrößenstatistiken
    if scan_report.get('file_size_stats'):
        st.subheader("Dateigrößen-Statistiken")
        size_stats = scan_report['file_size_stats']
        col1, col2, col3 = st.columns(3)
        col1.metric("Durchschnittliche Größe", f"{size_stats['average_size_bytes']/1024:.2f} KB")
        col2.metric("Maximale Größe", f"{size_stats['max_size_bytes']/1024:.2f} KB")
        col3.metric("Minimale Größe", f"{size_stats['min_size_bytes']/1024:.2f} KB")


def display_performance_statistics(performance_report: Dict[str, Any]):
    """
    Zeigt die Performance-Statistiken im Streamlit-UI an
    
    Args:
        performance_report: Der Performance-Bericht vom PerformanceAnalyzer
    """
    if not performance_report or 'timing' not in performance_report:
        st.warning("Keine Performance-Daten verfügbar")
        return
    
    timing = performance_report['timing']
    resources = performance_report['system_resources']
    processing = performance_report['file_processing']
    indicators = performance_report['performance_indicators']
    
    st.subheader("Performance-Analyse")
    
    # Timing-Informationen
    col1, col2 = st.columns(2)
    col1.metric("Scan-Dauer", timing['duration_readable'])
    col2.metric("Effizienz-Score", f"{indicators['efficiency_score']}/100")
    
    # System-Ressourcen
    col1, col2 = st.columns(2)
    col1.metric("CPU-Auslastung", f"{resources['cpu_percent']:.2f}%")
    col2.metric("Speichernutzung", f"{resources['memory_used_mb']:.2f} MB")
    
    # Dateiverarbeitung
    col1, col2, col3 = st.columns(3)
    col1.metric("Dateien verarbeitet", processing['files_processed'])
    col2.metric("Verzeichnisse gescannt", processing['directories_scanned'])
    col3.metric("Durchsatz", f"{indicators['files_per_second']} Dateien/Sek")


def display_scan_progress(current: int, total: int, description: str = "Scanning..."):
    """
    Zeigt den Scan-Fortschritt im Streamlit-UI an
    
    Args:
        current: Aktueller Fortschritt
        total: Gesamtanzahl
        description: Beschreibungstext
    """
    if total > 0:
        progress = current / total
        st.progress(progress, text=f"{description} ({current}/{total})")


def create_export_options(scan_report: Dict[str, Any], performance_report: Dict[str, Any]):
    """
    Erstellt Exportoptionen für die Filter- und Performance-Ergebnisse

    Args:
        scan_report: Der Scan-Bericht
        performance_report: Der Performance-Bericht
    """
    with st.expander("Export-Optionen"):
        st.write("Exportieren Sie die Scan- und Performance-Ergebnisse in verschiedenen Formaten:")

        col1, col2, col3 = st.columns(3)

        if col1.button("Export als JSON"):
            # Kombiniere die Berichte
            full_report = {
                "scan_report": scan_report,
                "performance_report": performance_report
            }

            json_str = json.dumps(full_report, indent=2, ensure_ascii=False, default=str)
            st.download_button(
                label="Herunterladen als JSON",
                data=json_str,
                file_name="daut_scan_report.json",
                mime="application/json"
            )

        if col2.button("Export als CSV"):
            # Erstelle CSV-Daten für verschiedene Metriken
            csv_data = []
            if scan_report.get('file_extensions'):
                for ext, count in scan_report['file_extensions'].items():
                    csv_data.append({'Typ': 'Dateierweiterung', 'Name': ext, 'Anzahl': count})

            if scan_report.get('excluded_directories'):
                for dir, count in scan_report['excluded_directories'].items():
                    csv_data.append({'Typ': 'Ausgeschlossenes Verzeichnis', 'Name': dir, 'Anzahl': count})

            if csv_data:
                df = pd.DataFrame(csv_data)
                csv_str = df.to_csv(index=False)
                st.download_button(
                    label="Herunterladen als CSV",
                    data=csv_str,
                    file_name="daut_statistics.csv",
                    mime="text/csv"
                )

        if col3.button("Export Dateilisten als CSV"):
            # Exportiere die vollständigen Dateilisten
            csv_data = []

            # Eingeschlossene Dateien
            if scan_report.get('filtered_files'):
                for file_path in scan_report['filtered_files']:
                    csv_data.append({'Datei': file_path, 'Status': 'Eingeschlossen'})

            # Ausgeschlossene Dateien
            if scan_report.get('excluded_files'):
                for file_path in scan_report['excluded_files']:
                    csv_data.append({'Datei': file_path, 'Status': 'Ausgeschlossen'})

            if csv_data:
                df = pd.DataFrame(csv_data)
                csv_str = df.to_csv(index=False)
                st.download_button(
                    label="Dateilisten herunterladen",
                    data=csv_str,
                    file_name="daut_file_lists.csv",
                    mime="text/csv"
                )


def display_file_browser(filtered_files: List[str], excluded_files: List[str]):
    """
    Zeigt einen Datei-Browser im UI an
    
    Args:
        filtered_files: Liste der eingeschlossenen Dateien
        excluded_files: Liste der ausgeschlossenen Dateien
    """
    st.subheader("Datei-Browser")
    
    tab1, tab2 = st.tabs(["Eingeschlossene Dateien", "Ausgeschlossene Dateien"])
    
    with tab1:
        if filtered_files:
            st.write(f"Anzahl eingeschlossener Dateien: {len(filtered_files)}")
            for file_path in filtered_files[:50]:  # Limitiere Anzeige
                st.code(file_path, language="path")
            if len(filtered_files) > 50:
                st.write(f"... und {len(filtered_files) - 50} weitere Dateien")
        else:
            st.info("Keine eingeschlossenen Dateien")
    
    with tab2:
        if excluded_files:
            st.write(f"Anzahl ausgeschlossener Dateien: {len(excluded_files)}")
            for file_path in excluded_files[:50]:  # Limitiere Anzeige
                st.code(file_path, language="path")
            if len(excluded_files) > 50:
                st.write(f"... und {len(excluded_files) - 50} weitere Dateien")
        else:
            st.info("Keine ausgeschlossenen Dateien")


def display_filter_management(config_manager):
    """
    Zeigt eine UI-Komponente zum manuellen Hinzufügen/Ausschließen von Dateien/Ordnern

    Args:
        config_manager: Instanz des ConfigManagers zur Änderung der Konfiguration
    """
    st.subheader("Filter-Verwaltung")

    config = config_manager.get_effective_config()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Ausschlussmuster verwalten**")
        new_exclude_pattern = st.text_input("Neues Ausschlussmuster (z.B. 'node_modules', '*.tmp')", key="new_exclude")
        if st.button("Zum Ausschluss hinzufügen"):
            if new_exclude_pattern and new_exclude_pattern not in config.exclude_patterns:
                config.exclude_patterns.append(new_exclude_pattern)
                st.success(f"Muster '{new_exclude_pattern}' wurde zur Ausschlussliste hinzugefügt")
            elif new_exclude_pattern in config.exclude_patterns:
                st.warning(f"Muster '{new_exclude_pattern}' ist bereits in der Ausschlussliste")

        # Anzeige der aktuellen Ausschlussmuster
        if config.exclude_patterns:
            st.write("Aktuelle Ausschlussmuster:")
            for i, pattern in enumerate(config.exclude_patterns):
                col_del1, col_del2 = st.columns([4, 1])
                with col_del1:
                    st.text(f"• {pattern}")
                with col_del2:
                    if st.button("❌", key=f"del_excl_{i}"):
                        config.exclude_patterns.remove(pattern)
                        st.rerun()

    with col2:
        st.write("**Ausnahmemuster verwalten** (zum Einschließen bestimmter Dateien)")
        new_include_pattern = st.text_input("Neues Einschlussmuster (z.B. '*.env', '*.config')", key="new_include")
        if st.button("Zum Einschluss hinzufügen"):
            if new_include_pattern and new_include_pattern not in config.include_patterns:
                config.include_patterns.append(new_include_pattern)
                st.success(f"Muster '{new_include_pattern}' wurde zur Einschlussliste hinzugefügt")
            elif new_include_pattern in config.include_patterns:
                st.warning(f"Muster '{new_include_pattern}' ist bereits in der Einschlussliste")

        # Anzeige der aktuellen Einschlussmuster
        if config.include_patterns:
            st.write("Aktuelle Einschlussmuster:")
            for i, pattern in enumerate(config.include_patterns):
                col_del3, col_del4 = st.columns([4, 1])
                with col_del3:
                    st.text(f"• {pattern}")
                with col_del4:
                    if st.button("❌", key=f"del_incl_{i}"):
                        config.include_patterns.remove(pattern)
                        st.rerun()

    # Datei- oder Verzeichnisauswahl
    st.write("**Spezifische Dateien/Verzeichnisse hinzufügen**")
    col_path1, col_path2 = st.columns([3, 1])

    with col_path1:
        specific_path = st.text_input("Datei- oder Verzeichnispfad (relativ zum Projektverzeichnis)")

    with col_path2:
        path_type = st.selectbox("Typ", ["Ausschließen", "Einschließen"])

    if st.button("Pfad hinzufügen"):
        if specific_path:
            if path_type == "Ausschließen" and specific_path not in config.exclude_patterns:
                config.exclude_patterns.append(specific_path)
                st.success(f"Pfad '{specific_path}' wurde zur Ausschlussliste hinzugefügt")
            elif path_type == "Einschließen" and specific_path not in config.include_patterns:
                config.include_patterns.append(specific_path)
                st.success(f"Pfad '{specific_path}' wurde zur Einschlussliste hinzugefügt")
            else:
                st.warning(f"Pfad '{specific_path}' ist bereits in der entsprechenden Liste")


def display_directory_visualization(scan_path: str, scan_report: Dict[str, Any] = None):
    """
    Zeigt eine Visualisierung der Verzeichnisstruktur mit Filterinformationen

    Args:
        scan_path: Der Pfad, der gescannt wurde
        scan_report: Optionaler Scan-Bericht mit Filterinformationen
    """
    import os
    from pathlib import Path

    st.subheader("Verzeichnis-Visualisierung")

    # Konvertiere zu Path-Objekt
    scan_path = Path(scan_path)

    if not scan_path.exists() or not scan_path.is_dir():
        st.error(f"Der angegebene Pfad existiert nicht oder ist kein Verzeichnis: {scan_path}")
        return

    # Hole Dateiinformationen aus dem Scan-Bericht, falls verfügbar
    included_files = set(scan_report.get('filtered_files', [])) if scan_report else set()
    excluded_files = set(scan_report.get('excluded_files', [])) if scan_report else set()
    excluded_dirs = set(scan_report.get('excluded_directories', [])) if scan_report else set()

    def render_directory_tree(current_path: Path, level: int = 0, max_depth: int = 5):
        """
        Rekursive Funktion zum Rendern der Verzeichnisstruktur
        """
        if level >= max_depth:
            return

        # Hole die direkten Kinder des aktuellen Verzeichnisses
        try:
            items = list(current_path.iterdir())
        except PermissionError:
            st.write(f"{'    ' * level}📁 {current_path.name} (Zugriff verweigert)")
            return

        # Sortiere: Verzeichnisse zuerst, dann Dateien
        items.sort(key=lambda x: (x.is_file(), x.name.lower()))

        for item in items:
            # Überspringe typische Verzeichnisse, die zu groß sind
            if item.name in ['.git', '__pycache__', 'node_modules', 'venv', '.venv',
                             '.pytest_cache', '.vscode', '.idea', 'dist', 'build', 'target',
                             'out', '.next', 'coverage', 'tmp', 'temp', '.tmp', '.temp']:
                continue

            indent = "    " * level

            if item.is_dir():
                # Prüfe, ob das Verzeichnis im Scan-Bericht als ausgeschlossen ist
                dir_status = ""
                if excluded_dirs and item.name in excluded_dirs:
                    dir_status = " ❌"  # Verzeichnis ist ausgeschlossen
                elif excluded_files and any(str(item) in f for f in excluded_files):
                    dir_status = " ⚠️"  # Mindestens eine Datei im Verzeichnis ist ausgeschlossen
                elif included_files and any(str(item) in f for f in included_files):
                    dir_status = " ✅"  # Mindestens eine Datei im Verzeichnis ist eingeschlossen

                st.write(f"{indent}📁 {item.name}{dir_status}")

                # Rekursiver Aufruf für Unterverzeichnisse
                render_directory_tree(item, level + 1, max_depth)

            elif item.is_file():
                # Prüfe, ob die Datei eingeschlossen oder ausgeschlossen ist
                file_path_str = str(item)
                if included_files and file_path_str in included_files:
                    status = " ✅"  # Datei ist eingeschlossen
                elif excluded_files and file_path_str in excluded_files:
                    status = " ❌"  # Datei ist ausgeschlossen
                else:
                    status = " ⚠️"  # Datei wurde nicht gescannt (wahrscheinlich aufgrund von Filtern)

                # Zeige Dateiname mit Status
                st.write(f"{indent}📄 {item.name}{status}")

    # Rendere die Verzeichnisstruktur ab dem übergebenen Pfad
    st.write(f"📁 **{scan_path.name}/**")
    render_directory_tree(scan_path, level=1, max_depth=4)

    # Zeige Legende
    st.markdown("""
    **Legende:**
    - ✅ Eingeschlossene Datei/Verzeichnis
    - ❌ Ausgeschlossene Datei/Verzeichnis
    - ⚠️ Nicht gescannte Datei/Verzeichnis (wahrscheinlich aufgrund von Filtern)
    """)

    # Zusätzliche Filter-Statistiken
    if scan_report:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Eingeschlossene Dateien", len(included_files))
        with col2:
            st.metric("Ausgeschlossene Dateien", len(excluded_files))
        with col3:
            excluded_dirs_count = len(excluded_dirs) if excluded_dirs else 0
            st.metric("Ausgeschlossene Verzeichnisse", excluded_dirs_count)