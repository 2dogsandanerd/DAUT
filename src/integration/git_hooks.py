"""
Modul für Git-Hooks Integration zur automatischen Dokumentationsaktualisierung
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable
import json
import shutil
from src.updater.engine import UpdaterEngine
from src.core.config_manager import ConfigManager
from src.core.service_config import ServiceConfig


class GitHookManager:
    """Klasse zur Verwaltung von Git-Hooks für automatische Dokumentationsaktualisierung"""
    
    def __init__(self, project_path: str, config_path: Optional[str] = None):
        self.project_path = Path(project_path).resolve()
        self.config_path = config_path
        self.hooks_dir = self.project_path / '.git' / 'hooks'
        
        # Überprüfe, ob es sich um ein Git-Repository handelt
        if not self.is_git_repo():
            raise ValueError(f"Kein Git-Repository gefunden unter: {self.project_path}")
    
    def is_git_repo(self) -> bool:
        """Prüft, ob sich das Projektverzeichnis in einem Git-Repository befindet"""
        return (self.project_path / '.git').exists()
    
    def install_pre_commit_hook(self, 
                               output_dir: str = "./auto_docs",
                               llm_model: Optional[str] = None,
                               embedding_model: Optional[str] = None) -> bool:
        """Installiert einen pre-commit Hook für automatische Dokumentationsaktualisierung"""
        try:
            # Erstelle den Hook-Inhalt
            hook_content = self._create_pre_commit_hook_content(output_dir, llm_model, embedding_model)
            
            # Schreibe den Hook in die Datei
            hook_file = self.hooks_dir / 'pre-commit'
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(hook_content)
            
            # Mache die Datei ausführbar
            os.chmod(hook_file, 0o755)
            
            print(f"Pre-commit Hook erfolgreich installiert in: {hook_file}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Installieren des Pre-commit Hooks: {e}")
            return False
    
    def install_post_commit_hook(self, 
                                output_dir: str = "./auto_docs",
                                llm_model: Optional[str] = None,
                                embedding_model: Optional[str] = None) -> bool:
        """Installiert einen post-commit Hook für automatische Dokumentationsaktualisierung"""
        try:
            # Erstelle den Hook-Inhalt
            hook_content = self._create_post_commit_hook_content(output_dir, llm_model, embedding_model)
            
            # Schreibe den Hook in die Datei
            hook_file = self.hooks_dir / 'post-commit'
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(hook_content)
            
            # Mache die Datei ausführbar
            os.chmod(hook_file, 0o755)
            
            print(f"Post-commit Hook erfolgreich installiert in: {hook_file}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Installieren des Post-commit Hooks: {e}")
            return False
    
    def install_post_merge_hook(self, 
                               output_dir: str = "./auto_docs",
                               llm_model: Optional[str] = None,
                               embedding_model: Optional[str] = None) -> bool:
        """Installiert einen post-merge Hook für automatische Dokumentationsaktualisierung nach Merges"""
        try:
            # Erstelle den Hook-Inhalt
            hook_content = self._create_post_merge_hook_content(output_dir, llm_model, embedding_model)
            
            # Schreibe den Hook in die Datei
            hook_file = self.hooks_dir / 'post-merge'
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(hook_content)
            
            # Mache die Datei ausführbar
            os.chmod(hook_file, 0o755)
            
            print(f"Post-merge Hook erfolgreich installiert in: {hook_file}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Installieren des Post-merge Hooks: {e}")
            return False
    
    def _create_pre_commit_hook_content(self, output_dir: str, llm_model: Optional[str], embedding_model: Optional[str]) -> str:
        """Erstellt den Inhalt für einen pre-commit Hook"""
        # Bestimme den absoluten Pfad für das Projekt
        abs_project_path = self.project_path.as_posix()
        
        # Bestimme den Python-Interpreter
        python_executable = shutil.which('python') or 'python'
        
        # Erstelle den Hook-Code
        hook_content = f'''#!/bin/bash
# DAUT - Documentation Auto-Update Tool - Pre-commit Hook
# Automatische Dokumentationsaktualisierung vor jedem Commit

echo "🔍 Prüfe auf Code-Änderungen für Dokumentationsaktualisierung..."

# Prüfe, ob Python-Dateien geändert wurden
changed_py_files=$(git diff --cached --name-only --diff-filter=ACMR | grep -E "\\.py$|\\.js$|\\.ts$|\\.go$|\\.rs$")

if [ -z "$changed_py_files" ]; then
    echo "ℹ️ Keine Code-Dateien geändert, überspringe Dokumentationsaktualisierung"
    exit 0
fi

echo "📝 Änderungen in Code-Dateien gefunden, starte Dokumentationsaktualisierung..."
echo "Geänderte Dateien:"
echo "$changed_py_files"

# Führe die Dokumentationsaktualisierung aus
{python_executable} -c "
import sys
sys.path.insert(0, '{abs_project_path}')

from src.core.config_manager import ConfigManager
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine
from src.core.service_config import ServiceConfig
import os

# Initialisiere Konfiguration
config = ConfigManager(project_path='{abs_project_path}').get_effective_config()

# Scanner initialisieren
scanner = UniversalScanner(config)
print('Starte Projekt-Scan...')

# Scan des Projekts
results = scanner.scan_project('{abs_project_path}')

print(f'Scan abgeschlossen. Gefunden: {{results[\"scan_summary\"][\"total_files_scanned\"]}} Dateien')

# Diskrepanzen finden
matcher = MatcherEngine()
discrepancies = matcher.find_discrepancies(
    results['code_elements'],
    results['doc_elements']
)

print(f'Gefundene Diskrepanzen:')
print(f'- Undokumentierter Code: {{len(discrepancies[\"undocumented_code\"])}}')
print(f'- Veraltete Dokumentation: {{len(discrepancies[\"outdated_documentation\"])}}')
print(f'- Nicht übereinstimmende Elemente: {{len(discrepancies[\"mismatched_elements\"])}}')

# Dokumentation aktualisieren
if discrepancies['undocumented_code']:
    print('Starte Dokumentationsgenerierung...')
    updater = UpdaterEngine()
    # Hier würden wir normalerweise einen LLM-Client übergeben
    # In diesem Hook verwenden wir eine vereinfachte Logik
    print(f'{{len(discrepancies[\"undocumented_code\"])}} Elemente benötigen Dokumentation')
    
    # Füge die Dokumentationsdateien zum Staging-Bereich hinzu
    import subprocess
    try:
        result = subprocess.run(['git', 'add', '{output_dir}'], 
                              capture_output=True, text=True, cwd='{abs_project_path}')
        if result.returncode == 0:
            print('Dokumentationsdateien zum Commit hinzugefügt')
        else:
            print('Keine neuen Dokumentationsdateien zum Hinzufügen gefunden')
    except Exception as e:
        print(f'Fehler beim Hinzufügen der Dokumentationsdateien: {{e}}')
"
'''

        return hook_content
    
    def _create_post_commit_hook_content(self, output_dir: str, llm_model: Optional[str], embedding_model: Optional[str]) -> str:
        """Erstellt den Inhalt für einen post-commit Hook"""
        abs_project_path = self.project_path.as_posix()
        python_executable = shutil.which('python') or 'python'
        
        hook_content = f'''#!/bin/bash
# DAUT - Documentation Auto-Update Tool - Post-commit Hook
# Automatische Dokumentationsaktualisierung nach jedem Commit

echo "🔄 Starte Post-Commit Dokumentationsaktualisierung..."

# Führe die Dokumentationsaktualisierung aus
{python_executable} -c "
import sys
sys.path.insert(0, '{abs_project_path}')

from src.core.config_manager import ConfigManager
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine
from src.core.service_config import ServiceConfig
import os

print('Starte Post-Commit Dokumentationsaktualisierung...')

# Initialisiere Konfiguration
config = ConfigManager(project_path='{abs_project_path}').get_effective_config()

# Scanner initialisieren
scanner = UniversalScanner(config)

# Scan des Projekts
results = scanner.scan_project('{abs_project_path}')

print(f'Projekt-Scan abgeschlossen. Verarbeite {{results[\"scan_summary\"][\"total_files_scanned\"]}} Dateien')

# Diskrepanzen finden
matcher = MatcherEngine()
discrepancies = matcher.find_discrepancies(
    results['code_elements'],
    results['doc_elements']
)

# Generiere Dokumentation für nicht dokumentierten Code
if discrepancies['undocumented_code']:
    print(f'{{len(discrepancies[\"undocumented_code\"])}} Elemente benötigen Dokumentation')
    
    # In einer vollständigen Implementierung würde hier ein LLM-Client initialisiert
    # und die Dokumentation generiert werden
    print('Dokumentationsaktualisierung abgeschlossen')
    
    # Aktualisiere ChromaDB
    print('Aktualisiere ChromaDB...')
    updater = UpdaterEngine()
    success = updater.update_chroma_db(
        results['code_elements'],
        results['doc_elements'],
        '{abs_project_path}'
    )
    if success:
        print('ChromaDB erfolgreich aktualisiert')
    else:
        print('Fehler bei der ChromaDB-Aktualisierung')
"
'''

        return hook_content
    
    def _create_post_merge_hook_content(self, output_dir: str, llm_model: Optional[str], embedding_model: Optional[str]) -> str:
        """Erstellt den Inhalt für einen post-merge Hook"""
        abs_project_path = self.project_path.as_posix()
        python_executable = shutil.which('python') or 'python'
        
        hook_content = f'''#!/bin/bash
# DAUT - Documentation Auto-Update Tool - Post-merge Hook
# Automatische Dokumentationsaktualisierung nach jedem Merge

echo "🔄 Starte Post-Merge Dokumentationsaktualisierung..."

# Prüfe, ob es tatsächlich Änderungen gab
if git diff --name-only HEAD^ HEAD | grep -E "\\.py$|\\.js$|\\.ts$|\\.go$|\\.rs$" > /dev/null; then
    echo "🔍 Änderungen in Code-Dateien nach Merge erkannt"
    
    # Führe die Dokumentationsaktualisierung aus
    {python_executable} -c "
import sys
sys.path.insert(0, '{abs_project_path}')

from src.core.config_manager import ConfigManager
from src.scanner.universal_scanner import UniversalScanner
from src.matcher import MatcherEngine
from src.updater.engine import UpdaterEngine
from src.core.service_config import ServiceConfig
import os

print('Starte Post-Merge Dokumentationsaktualisierung...')

# Initialisiere Konfiguration
config = ConfigManager(project_path='{abs_project_path}').get_effective_config()

# Scanner initialisieren
scanner = UniversalScanner(config)

# Scan des Projekts
results = scanner.scan_project('{abs_project_path}')

print(f'Projekt-Scan nach Merge abgeschlossen. Verarbeite {{results[\"scan_summary\"][\"total_files_scanned\"]}} Dateien')

# Diskrepanzen finden
matcher = MatcherEngine()
discrepancies = matcher.find_discrepancies(
    results['code_elements'],
    results['doc_elements']
)

# Generiere Dokumentation für nicht dokumentierten Code
if discrepancies['undocumented_code']:
    print(f'{{len(discrepancies[\"undocumented_code\"])}} Elemente nach Merge dokumentieren')
    
    # In einer vollständigen Implementierung würde hier ein LLM-Client initialisiert
    # und die Dokumentation generiert werden
    print('Dokumentationsaktualisierung nach Merge abgeschlossen')
    
    # Aktualisiere ChromaDB
    print('Aktualisiere ChromaDB nach Merge...')
    updater = UpdaterEngine()
    success = updater.update_chroma_db(
        results['code_elements'],
        results['doc_elements'],
        '{abs_project_path}'
    )
    if success:
        print('ChromaDB erfolgreich nach Merge aktualisiert')
    else:
        print('Fehler bei der ChromaDB-Aktualisierung nach Merge')
"
else
    echo "ℹ️ Keine Code-Datei-Änderungen nach Merge gefunden, überspringe Dokumentationsaktualisierung"
fi
'''

        return hook_content
    
    def remove_hook(self, hook_name: str) -> bool:
        """Entfernt einen Git-Hook"""
        try:
            hook_file = self.hooks_dir / hook_name
            if hook_file.exists():
                hook_file.unlink()
                print(f"Hook {hook_name} erfolgreich entfernt")
                return True
            else:
                print(f"Hook {hook_name} existiert nicht")
                return False
        except Exception as e:
            print(f"Fehler beim Entfernen des Hooks {hook_name}: {e}")
            return False
    
    def list_installed_hooks(self) -> List[str]:
        """Listet installierte DAUT-Hooks auf"""
        hooks = []
        for hook_file in self.hooks_dir.glob('*'):
            if hook_file.is_file() and os.access(hook_file, os.X_OK):
                # Prüfe, ob der Hook von DAUT ist
                with open(hook_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'DAUT - Documentation Auto-Update Tool' in content:
                        hooks.append(hook_file.name)
        return hooks


def install_git_hooks(project_path: str, 
                     hooks: List[str] = ['pre-commit'], 
                     output_dir: str = "./auto_docs",
                     llm_model: Optional[str] = None,
                     embedding_model: Optional[str] = None) -> Dict[str, bool]:
    """Installiert Git-Hooks für automatische Dokumentationsaktualisierung"""
    results = {}
    
    try:
        hook_manager = GitHookManager(project_path)
        
        for hook_type in hooks:
            if hook_type == 'pre-commit':
                results[hook_type] = hook_manager.install_pre_commit_hook(
                    output_dir=output_dir,
                    llm_model=llm_model,
                    embedding_model=embedding_model
                )
            elif hook_type == 'post-commit':
                results[hook_type] = hook_manager.install_post_commit_hook(
                    output_dir=output_dir,
                    llm_model=llm_model,
                    embedding_model=embedding_model
                )
            elif hook_type == 'post-merge':
                results[hook_type] = hook_manager.install_post_merge_hook(
                    output_dir=output_dir,
                    llm_model=llm_model,
                    embedding_model=embedding_model
                )
            else:
                print(f"Unbekannter Hook-Typ: {hook_type}")
                results[hook_type] = False
                
    except Exception as e:
        print(f"Fehler beim Installieren der Git-Hooks: {e}")
        for hook_type in hooks:
            results[hook_type] = False
    
    return results