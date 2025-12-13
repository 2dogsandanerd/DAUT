from pathlib import Path
from typing import Dict, List, Tuple
import re
from .config_manager import ProjectConfig

class ProjectAnalyzer:
    def __init__(self, config: ProjectConfig):
        self.config = config
    
    def detect_project_type(self, project_path: str) -> str:
        """Erkennt den Projekttyp basierend auf Dateien und Ordnern"""
        project_path = Path(project_path)
        
        # Suchen nach spezifischen Dateien und Ordnern
        files = [f.name.lower() for f in project_path.rglob('*') if f.is_file()]
        dirs = [d.name.lower() for d in project_path.rglob('*') if d.is_dir()]
        
        # Überprüfe mehrere Projekttypen in einem Monorepo
        detected_types = []
        
        # Python-Projekte
        if 'requirements.txt' in files or 'pyproject.toml' in files or 'setup.py' in files:
            if any('fastapi' in f for f in files if 'requirements.txt' in f) or \
               any('fastapi' in f for f in files if 'pyproject.toml' in f):
                detected_types.append('python_fastapi')
            elif any('flask' in f for f in files if 'requirements.txt' in f):
                detected_types.append('python_flask')
            else:
                detected_types.append('python')
        
        # JavaScript-Projekte
        if 'package.json' in files:
            package_json_path = project_path / 'package.json'
            if package_json_path.exists():
                import json
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    try:
                        pkg_data = json.load(f)
                        dependencies = pkg_data.get('dependencies', {})
                        dev_dependencies = pkg_data.get('devDependencies', {})
                        
                        all_deps = {**dependencies, **dev_dependencies}
                        
                        if 'express' in all_deps:
                            detected_types.append('javascript_express')
                        elif 'react' in all_deps:
                            detected_types.append('javascript_react')
                        elif 'vue' in all_deps:
                            detected_types.append('javascript_vue')
                        elif 'angular' in all_deps:
                            detected_types.append('javascript_angular')
                        else:
                            detected_types.append('javascript')
                    except:
                        detected_types.append('javascript')
            else:
                detected_types.append('javascript')
        
        # Sonstige Projekttypen
        if any('.cs' in f for f in files):
            detected_types.append('csharp')
        elif any('.java' in f for f in files):
            detected_types.append('java')
        elif any('.go' in f for f in files):
            detected_types.append('go')
        
        # Wenn mehrere Typen gefunden wurden, gib einen Monorepo-Typ zurück
        if len(detected_types) > 1:
            return 'monorepo_' + '_'.join(detected_types)
        elif detected_types:
            return detected_types[0]
        else:
            return 'universal'  # Fallback
    
    def get_scan_paths(self, project_path: str) -> List[str]:
        """Bestimmt die zu scannenden Pfade basierend auf Projekttyp"""
        project_type = self.detect_project_type(project_path)
        project_path = Path(project_path)
        
        scan_paths = []
        
        # Behandle Monorepo-Szenarien
        if 'monorepo' in project_type:
            # Durchsuche typische Projektverzeichnisse für beide Sprachökosysteme
            monorepo_paths = ['.', 'backend', 'frontend', 'api', 'services', 'packages']
            for path in monorepo_paths:
                full_path = project_path / path
                if full_path.exists():
                    scan_paths.append(str(full_path))
        elif project_type in ['python', 'python_fastapi', 'python_flask']:
            # Typische Python-Pfade
            python_paths = ['.', 'src', 'lib', 'app', 'backend', 'api']
            for path in python_paths:
                full_path = project_path / path
                if full_path.exists():
                    scan_paths.append(str(full_path))
        
        elif project_type in ['javascript', 'javascript_express', 'javascript_react', 'javascript_vue', 'javascript_angular']:
            # Typische JavaScript-Pfade
            js_paths = ['.', 'src', 'lib', 'app', 'backend', 'frontend', 'api', 'components', 'services', 'utils', 'hooks', 'pages', 'routes']
            for path in js_paths:
                full_path = project_path / path
                if full_path.exists():
                    scan_paths.append(str(full_path))
        
        else:
            # Für andere Projekttypen oder universelle Erkennung
            scan_paths = ['.']
        
        # Ergänze spezifische Verzeichnisse, die gefunden wurden
        # z.B. wenn ein frontend oder backend Verzeichnis existiert, aber nicht automatisch erkannt wurde
        if not scan_paths or scan_paths == ['.']:
            # Suche nach typischen Projektverzeichnissen
            potential_paths = ['frontend', 'backend', 'src', 'app', 'api', 'services', 'packages']
            for path in potential_paths:
                full_path = project_path / path
                if full_path.exists():
                    path_str = str(full_path)
                    if path_str not in scan_paths:
                        scan_paths.append(path_str)
        
        return scan_paths or ['.']  # Fallback