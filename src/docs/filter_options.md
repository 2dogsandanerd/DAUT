# DAUT - Filteroptionen und Konfiguration

## Übersicht

Der Documentation Auto-Update Tool (DAUT) verfügt über umfangreiche Filteroptionen, um sicherzustellen, dass nur relevante Dateien gescannt und verarbeitet werden. Dieses Dokument beschreibt die verschiedenen Filtermechanismen und Konfigurationsmöglichkeiten.

## Standard-Ausschlussmuster

DAUT schließt standardmäßig folgende Dateien und Verzeichnisse aus:

### Verzeichnisse
- `node_modules` - JavaScript-Abhängigkeiten
- `venv`, `.venv`, `env`, `.env` - Python-Virtual-Environments
- `__pycache__` - Python-Cache-Dateien
- `.git` - Git-Metadaten
- `dist`, `build` - Build-Artefakte
- `.pytest_cache`, `.tox`, `.nox` - Test-Caches
- `.vscode`, `.idea` - IDE-spezifische Dateien
- `target`, `out` - Build-Verzeichnisse für andere Sprachen
- `.next`, `.nuxt`, `.vercel`, `.netlify` - Framework-spezifische Verzeichnisse
- `coverage`, `htmlcov` - Test-Abdeckungsberichte
- `tmp`, `temp`, `.tmp`, `.temp` - Temporäre Dateien
- `Pods` - iOS-Abhängigkeiten
- `.npm`, `.yarn` - Paketmanager-Verzeichnisse
- `.serverless`, `.dynamodb` - Serverless-Framework-Dateien
- und viele weitere...

### Dateiendungen
- `*.pyc`, `*.pyo` - Python-Bytecode
- `*.log` - Log-Dateien
- `*.tmp`, `*.temp`, `*.bak` - Temporäre/Backup-Dateien
- `package-lock.json`, `yarn.lock` - Paket-Lock-Dateien
- `*.min.js`, `*.bundle.js` - Minifizierte JavaScript-Dateien
- `*.lock` - Lock-Dateien verschiedener Tools
- Bilddateien: `*.ico`, `*.png`, `*.jpg`, `*.svg`
- und viele weitere...

## Konfigurationsmöglichkeiten

### Konfigurationsdatei

DAUT kann über eine JSON- oder YAML-Konfigurationsdatei angepasst werden. Beispiel:

```json
{
  "project_type": "universal",
  "scan_paths": ["."],
  "exclude_patterns": [
    "node_modules",
    "venv",
    "__pycache__",
    "custom_exclude_dir"
  ],
  "include_patterns": [
    "*.py",
    "*.js",
    "*.jsx",
    "*.ts",
    "*.tsx",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.md",
    "*.rst",
    "*.txt",
    ".env",
    "custom_include_file.txt"
  ],
  "exclude_files": [
    "*.pyc",
    "*.log",
    "*.tmp",
    "*.bak",
    "package-lock.json",
    "custom_exclude_pattern.*"
  ],
  "scan_depth": 10,
  "max_file_size_mb": 10
}
```

### Anpassung über die Benutzeroberfläche

In der UI können Filter während der Laufzeit verwaltet werden:

1. Klicken Sie auf "Filter-Verwaltung" (in einem Ausklappbereich)
2. Fügen Sie neue Ausschlussmuster hinzu
3. Fügen Sie neue Einschlussmuster hinzu
4. Verwalten Sie spezifische Dateipfade

## Gitignore-Integration

DAUT respektiert `.gitignore`-Dateien auf allen Ebenen des Projektverzeichnisses:

- Die Haupt-.gitignore-Datei im Projektverzeichnis
- Verschachtelte .gitignore-Dateien in Unterverzeichnissen
- Standards aus `.git/info/exclude`
- Globale .gitignore-Dateien des Benutzers

## Dateianalyse und Statistiken

Nach jedem Scan werden detaillierte Statistiken bereitgestellt:

### Filterstatistiken
- Gesamtzahl gescannter Dateien
- Anzahl eingeschlossener Dateien
- Anzahl ausgeschlossener Dateien
- Einschlussrate in Prozent
- Verteilung nach Dateitypen
- Verteilung nach Dateierweiterungen
- Liste ausgeschlossener Verzeichnisse

### Performance-Statistiken
- Scan-Dauer
- CPU- und Speicherauslastung
- Anzahl verarbeiteter Dateien pro Sekunde
- Effizienz-Score

## Fortschrittsanzeige

Während des Scans wird der Fortschritt in der UI angezeigt:
- Anzeige des aktuellen Verzeichnisses
- Anzeige der aktuellen Datei
- Fortschrittsbalken mit Prozentangabe

## Exportfunktionen

Alle Filter- und Performance-Daten können exportiert werden:
- Als JSON mit vollständigen Details
- Als CSV mit aggregierten Statistiken
- Als CSV mit vollständigen Dateilisten

## Best Practices

### Auswahl von Scan-Pfaden
- Verwenden Sie spezifische Pfade statt `.` wenn möglich
- Vermeiden Sie übergeordnete Verzeichnisse mit vielen irrelevanten Dateien

### Ausschlussregeln
- Schließen Sie Build- und Distributionsverzeichnisse aus
- Schließen Sie Virtual-Environment-Verzeichnisse aus
- Schließen Sie große Binärdateien aus
- Nutzen Sie spezifische Muster anstelle von `**`

### Performance-Optimierung
- Verwenden Sie die maximale Dateigröße, um riesige Dateien auszuschließen
- Begrenzen Sie die Scan-Tiefe für große Projekte
- Verwenden Sie spezifische Include-Muster für große monolithische Projekte