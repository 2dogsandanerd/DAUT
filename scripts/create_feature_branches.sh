#!/bin/bash
# Skript zum Erstellen der Feature-Branches für die DAUT-Verbesserungen

echo "Erstelle Feature-Branches für DAUT-Verbesserungen..."

# Überprüfe, ob wir in einem Git-Repository sind
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Fehler: Nicht in einem Git-Repository"
    exit 1
fi

# Haupt-Branch sichern
MAIN_BRANCH=$(git branch --show-current)
echo "Aktueller Branch: $MAIN_BRANCH"

# Liste der Feature-Branches gemäß unserem Verbesserungsplan
FEATURE_BRANCHES=(
    "feature/config-flexibility"           # Phase 1: Konfigurationsflexibilität
    "feature/intelligent-defaults"         # Phase 1: Intelligente Defaults
    "feature/doc-quality-system"           # Phase 1: Dokumentationsqualität
    "feature/structured-logging"           # Phase 1: Strukturiertes Logging
    "feature/framework-parsers"            # Phase 2: Framework-Parser
    "feature/conflict-resolution"          # Phase 2: Konfliktlösung
    "feature/parallel-processing"          # Phase 2: Parallele Verarbeitung
    "feature/go-rust-support"              # Phase 3: Go/Rust-Unterstützung
    "feature/git-hooks-integration"        # Phase 3: Git-Hooks
    "feature/unique-naming-system"        # Phase 3: Eindeutige Namensgebung
)

# Erstelle jeden Feature-Branch
for branch in "${FEATURE_BRANCHES[@]}"; do
    echo "Erstelle Branch: $branch"
    
    # Wechsle zum Hauptbranch, bevor wir einen neuen Branch erstellen
    git checkout "$MAIN_BRANCH" > /dev/null 2>&1
    
    # Erstelle den neuen Branch
    if git checkout -b "$branch" > /dev/null 2>&1; then
        echo "  ✓ Branch $branch erfolgreich erstellt"
        
        # Füge eine README-Datei hinzu, um den Zweck des Branches zu dokumentieren
        echo "# $branch

Dieser Branch implementiert Verbesserungen für:

- Detaillierte Beschreibung der Änderungen
- Implementierung gemäß dem Verbesserungsplan
- Tests und Validierung

## Status
- [ ] Geplant
- [ ] In Entwicklung
- [ ] Getestet
- [ ] Bereit zur Integration

## Änderungen
- Liste der geplanten/umgesetzten Änderungen
" > "BRANCH_INFO.md"
        
        git add "BRANCH_INFO.md" > /dev/null 2>&1
        git commit -m "docs: Add branch info for $branch" > /dev/null 2>&1
        
        # Lösche die temporäre Datei
        rm "BRANCH_INFO.md" > /dev/null 2>&1
        
    else
        echo "  ✗ Fehler beim Erstellen von Branch $branch"
    fi
done

# Wechsle zurück zum ursprünglichen Branch
git checkout "$MAIN_BRANCH" > /dev/null 2>&1

echo "Alle Feature-Branches wurden erstellt!"
echo ""
echo "Übersicht der erstellten Branches:"
git branch | grep feature/

echo ""
echo "Verwendung:"
echo "- Wechsle in einen Branch: git checkout <branch-name>"
echo "- Implementiere die geplanten Änderungen"
echo "- Committe deine Änderungen"
echo "- Erstelle einen Pull Request in den Hauptbranch"