from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import yaml
from pathlib import Path

class ProjectConfig(BaseModel):
    project_type: str = "universal"
    scan_paths: List[str] = ["."]
    exclude_patterns: List[str] = [
        "node_modules", "venv", ".venv", "__pycache__", ".git",
        "dist", "build", ".pytest_cache", ".vscode", ".idea",
        "target", "out", ".next", "coverage", ".tox", ".nox",
        "env", ".env", "env.bak", ".env.bak", "venv.bak", ".venv",
        "__bundle", "Pods", ".dart_tool", ".pub", "vendor", "bower_components",
        ".npm", ".yarn", "jspm_packages", ".angular", ".nuxt", ".vercel",
        ".netlify", ".cache", "tmp", "temp", ".tmp", ".temp", ".serverless",
        ".dynamodb", ".fusebox", ".nyc_output", ".sass-cache", "lib-cov",
        "e2e", "nightwatch", "webdriver", ".grunt", ".lock-wscript",
        ".yarn-integrity", ".yarn-metadata", ".node_repl_history", ".nvm",
        ".rbenv", ".ruby-version", ".bundle", "TestResults", ".pypirc",
        ".python-history", ".hypothesis", "site-packages", "pip-log.txt",
        "pip-delete-this-directory.txt", "packages.lock.json", "htmlcov", ".cover",
        "*.pyc", "*.pyo", "*.pyd", ".Python", ".spyderproject", ".spyproject",
        ".ropeproject", ".mypy_cache", "mypy_cache", ".dmypy.json", "dmypy.json",
        ".pyre", ".pytype", "pyrightconfig.json", ".vs", ".sublime-workspace",
        ".sublimelintcache", "*.sublime-project", ".project", ".c9", "*.c9revisions",
        "*_c9s", ".settings", ".history", ".vagrant", "vagrant-*.out", "vagrant-*.err",
        "CACHEDIR.TAG", "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*",
        "coverage/lcov-report", "nyc_output", ".istanbul", "vendor/bundle",
        "vendor/cache", "vendor/gems", "vendor/ruby", "paket-files", ".paket",
        "packages", "lib", "obj", "*.nupkg", ".nuget", "CMakeFiles", "CMakeCache.txt",
        ".swp", ".swo", "*.swp", "*.swo", "pip-delete-this-directory.txt", ".tox",
        ".coverage", "htmlcov", ".cover", ".hypothesis", ".pytest_cache", ".pyre",
        ".pytype", "mypy_cache", ".mypy_cache", "venv", "ENV", "env", "env.bak",
        ".env", ".env.bak", "venv.bak", ".venv", "ENV", ".ENV", "env", "venv",
        "ENV", "env.bak", ".env", ".env.bak", "venv.bak", ".venv", ".venv",
        ".pytest_cache", ".coverage", "htmlcov", ".cover", ".hypothesis",
        "__pycache__", "*.pyc", "__pycache__", "*.pyc", "*.pyo", "*.pyd",
        ".Python", "pip-log.txt", "pip-delete-this-directory.txt", ".spyderproject",
        ".spyproject", ".ropeproject", "site-packages", ".mypy_cache",
        "mypy_cache", ".dmypy.json", "dmypy.json", ".pyre", ".pytype",
        "pyrightconfig.json", ".vs", ".vscode", ".idea", ".sublime-workspace",
        ".sublimelintcache", "*.sublime-project", ".project", ".c9", "*.c9revisions",
        "*_c9s", ".settings", ".history", ".vagrant", "vagrant-*.out",
        "vagrant-*.err", "CACHEDIR.TAG"
    ]
    include_patterns: List[str] = [
        "*.py", "*.js", "*.jsx", "*.ts", "*.tsx",
        "*.json", "*.yaml", "*.yml", "*.md", "*.rst", "*.txt",
        ".env", ".env.example"
    ]
    exclude_files: List[str] = [
        "*.pyc", "*.log", "*.tmp", "*.bak", "package-lock.json",
        "yarn.lock", "*.min.js", "*.bundle.js", "*.lock",
        "*.ico", "*.png", "*.jpg", "*.svg", "*.pyo", "*.pyd",
        "*.swp", "*.swo", "*~", "#*#", ".DS_Store", "Thumbs.db",
        "*.lcov", "*.coverage", "coverage.xml", "nosetests.xml",
        ".coverage.*", "lcov.info", "jacoco*.xml", "*.gcda", "*.gcno",
        "coverage-final.json", ".nfs*", ".fuse_hidden*", ".dropbox", ".Spotlight-V100",
        ".Trashes", "ehthumbs.db", "Thumbs.db", ".AppleDouble", ".LSOverride",
        "Icon?", "._*", ".DocumentRevisions-V100", ".fseventsd", ".Spotlight-V100",
        ".TemporaryItems", ".Trashes", ".VolumeIcon.icns", ".com.apple.timemachine.donotpresent",
        ".AppleDB", ".AppleDesktop", "Network Trash Folder", "Temporary Items",
        ".apdisk", ".gradle", ".sonar", ".sonarqube", "*.tmproj", "*.xcodeproj",
        "*.xcworkspace", "*.swp", "*.swo", "*~", ".#*", "*.tmp", "*.temp",
        ".*.swp", ".*.swo", ".*~", "flycheck_*.py", ".ccls-cache",
        "*.pid", "*.seed", "*.pid.lock", "-lock.json", "*.webapp", "*.webmanifest",
        "key.pem", "pem", "secret", "*.secret", ".configrc", ".netrwhist",
        "*._js", "*.bundle", "*.a", "*.o", "*.so", "*.dll", "*.class", "*.o",
        "*.obj", "*.exe", "*.a", "*.lib", "*.dylib", "*.so", "*.dll", "*.dSYM",
        "*.egg-info", ".Python", "*.egg-info", "pip-log.txt", "pip-delete-this-directory.txt",
        ".python-history", ".python-version", ".rvmrc", ".gem", ".node-version",
        ".nvmrc", "*.lcov", "coverage", "coverage/lcov-report", ".nyc_output",
        "nyc_output", ".istanbul", ".nyc_output", ".istanbul", "npm-debug.log*",
        "yarn-debug.log*", "yarn-error.log*", ".yarn-integrity", ".yarn-metadata",
        ".node_repl_history", ".nvm", ".rbenv", ".ruby-version", ".bundle",
        "vendor/bundle", "vendor/cache", "vendor/gems", "vendor/ruby", "Pods",
        ".paket", "paket-files", "packages", "lib", "obj", "TestResults",
        "*.nupkg", ".nuget", "packages.lock.json", ".pypirc", ".python-history",
        ".pytest_cache", ".hypothesis", "site-packages", "pip-log.txt",
        "pip-delete-this-directory.txt", ".tox", ".coverage", "htmlcov", ".cover",
        ".hypothesis", ".pytest_cache", ".pyre", ".pytype", "mypy_cache",
        ".mypy_cache", "venv", "ENV", "env", "env.bak", ".env", ".env.bak",
        "venv.bak", ".venv", "ENV", ".ENV", "env", "venv", "ENV", "env.bak",
        ".env", ".env.bak", "venv.bak", ".venv", ".venv", ".pytest_cache",
        ".coverage", "htmlcov", ".cover", ".hypothesis", "__pycache__", "*.pyc",
        "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python", "pip-log.txt",
        "pip-delete-this-directory.txt", ".spyderproject", ".spyproject",
        ".ropeproject", "site-packages", ".mypy_cache", "mypy_cache", ".dmypy.json",
        "dmypy.json", ".pyre", ".pytype", "pyrightconfig.json", ".vs", ".vscode",
        ".idea", ".sublime-workspace", ".sublimelintcache", "*.sublime-project",
        ".project", ".c9", "*.c9revisions", "*_c9s", ".settings", ".history",
        ".vagrant", "vagrant-*.out", "vagrant-*.err", "CACHEDIR.TAG"
    ]
    scan_depth: int = 10  # Maximale Unterverzeichnisse
    max_file_size_mb: int = 10  # Maximale Dateigröße in MB für gescannte Dateien
    framework_detection: Dict[str, List[str]] = {
        "python": ["requirements.txt", "pyproject.toml", "setup.py"],
        "javascript": ["package.json"],
        "python_fastapi": ["fastapi", "uvicorn"],
        "python_flask": ["flask"],
        "javascript_express": ["express"]
    }
    
    def update_for_project(self, project_path: str) -> None:
        """Aktualisiert die Konfiguration basierend auf dem Projektverzeichnis"""
        project_dir = Path(project_path)

        # Framework-Detection basierend auf Dateien im Projekt
        detected_frameworks = []

        # Überprüfe auf spezifische Dateien
        if (project_dir / "requirements.txt").exists() or (project_dir / "pyproject.toml").exists() or (project_dir / "setup.py").exists():
            detected_frameworks.append("python")

        if (project_dir / "package.json").exists():
            detected_frameworks.append("javascript")

        # Überprüfe requirements.txt oder pyproject.toml auf spezifische Frameworks
        req_file = project_dir / "requirements.txt"
        pyproject_file = project_dir / "pyproject.toml"

        if req_file.exists():
            content = req_file.read_text(encoding='utf-8', errors='ignore')
            if "fastapi" in content.lower():
                detected_frameworks.append("python_fastapi")
            elif "flask" in content.lower():
                detected_frameworks.append("python_flask")
            elif "django" in content.lower():
                detected_frameworks.append("python_django")

        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8', errors='ignore')
            if "fastapi" in content.lower():
                detected_frameworks.append("python_fastapi")
            elif "flask" in content.lower():
                detected_frameworks.append("python_flask")
            elif "django" in content.lower():
                detected_frameworks.append("python_django")

        # Aktualisiere die Konfiguration basierend auf erkannten Frameworks
        if "python_fastapi" in detected_frameworks or "python_flask" in detected_frameworks:
            # Für Python-Webframeworks, füge API-spezifische Dateiendungen hinzu
            if "*.py" in self.include_patterns and "*.api.py" not in self.include_patterns:
                self.include_patterns.extend(["*.api.py", "*.router.py", "*.endpoint.py"])

        if "javascript" in detected_frameworks:
            # Für JavaScript-Projekte, füge typische Dateiendungen hinzu
            if "*.js" in self.include_patterns and "*.jsx" in self.include_patterns:
                self.include_patterns.extend(["*.cjs", "*.mjs", "*.ts", "*.tsx"])

        # Setze den Projekttyp basierend auf den Erkennungen
        if detected_frameworks:
            self.project_type = "_".join(detected_frameworks)

        # Setze intelligente Pfade basierend auf Projekttyp
        if "python" in detected_frameworks:
            if "." in self.scan_paths or ["."] in self.scan_paths:
                # Ersetze generischen Pfad durch spezifischere Pfade, wenn vorhanden
                potential_paths = ["src", "lib", "app", project_dir.name]
                for path in potential_paths:
                    if (project_dir / path).is_dir():
                        if path not in self.scan_paths:
                            self.scan_paths.append(path)
                        break

    class Config:
        arbitrary_types_allowed = True

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None, project_path: Optional[str] = None):
        if config_path and Path(config_path).exists():
            self.config = self.load_config(config_path)
        else:
            self.config = ProjectConfig()

        # Wenn ein Projektverzeichnis angegeben ist, aktualisiere die Konfiguration
        if project_path:
            self.config.update_for_project(project_path)

    def load_config(self, config_path: str) -> ProjectConfig:
        """Lädt Konfiguration aus Datei (JSON oder YAML)"""
        path = Path(config_path)
        if path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif path.suffix.lower() in ['.yml', '.yaml']:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

        return ProjectConfig(**data)
    
    def save_config(self, config_path: str):
        """Speichert Konfiguration in Datei"""
        path = Path(config_path)
        if path.suffix.lower() == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config.dict(), f, indent=2, ensure_ascii=False)
        elif path.suffix.lower() in ['.yml', '.yaml']:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config.dict(), f, default_flow_style=False, allow_unicode=True)
    
    def get_effective_config(self) -> ProjectConfig:
        """Gibt die aktuelle Konfiguration zurück"""
        return self.config