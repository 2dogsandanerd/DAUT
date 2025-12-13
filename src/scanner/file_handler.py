from pathlib import Path
from typing import List
import os
from fnmatch import fnmatch
import git
from .gitignore_handler import GitIgnoreHandler
from ..core.config_manager import ProjectConfig

class FileHandler:
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.gitignore_handler = None

    def get_filtered_files(self, scan_path: Path) -> List[Path]:
        """Gibt eine Liste von Dateien zurück, die den Filterkriterien entsprechen"""
        files = []

        # Initialisiere den GitIgnoreHandler
        self.gitignore_handler = GitIgnoreHandler(scan_path)

        for root, dirs, filenames in os.walk(scan_path):
            root_path = Path(root)

            # Entferne auszuschließende Verzeichnisse bereits hier,
            # bevor Dateien darin untersucht werden
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d, root_path, self.config.exclude_patterns)]

            # Entferne .git-verzeichnisse wenn .git nicht in include_patterns ist
            if '.git' not in self.config.include_patterns:
                dirs[:] = [d for d in dirs if d != '.git']

            # Dateien filtern
            for filename in filenames:
                file_path = Path(root) / filename

                # Größe prüfen
                if file_path.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
                    continue

                # Prüfen, ob Datei in Gitignore ist (verwendet den GitIgnoreHandler)
                if self.gitignore_handler and self.gitignore_handler.is_ignored(file_path):
                    continue

                # Datei-Filter anwenden
                if self._should_include_file(file_path):
                    files.append(file_path)

        return files
    
    def _is_git_ignored(self, file_path: Path, git_repo) -> bool:
        """Prüft, ob eine Datei von Git ignoriert wird"""
        try:
            # Konvertiere Pfad relativ zum Git-Repository
            relative_path = str(file_path.relative_to(git_repo.working_dir).as_posix())
            # Prüfe, ob Git die Datei ignoriert
            return git_repo.ignored(relative_path)
        except ValueError:
            # Datei liegt außerhalb des Git-Repositorys
            return False
        except Exception:
            # Irgendetwas ist schiefgegangen, keine Git-Ignore-Prüfung
            return False
    
    def _should_exclude(self, name: str, patterns: List[str]) -> bool:
        """Prüft, ob ein Name aufgrund der Ausschlussmuster ausgeschlossen werden sollte"""
        for pattern in patterns:
            if fnmatch(name.lower(), pattern.lower()):
                return True
        return False
    
    def _should_exclude_dir(self, dir_name: str, parent_path: Path, patterns: List[str]) -> bool:
        """Prüft, ob ein Verzeichnis basierend auf Ausschlussmustern ausgeschlossen werden sollte"""
        # Prüfe den Verzeichnisnamen selbst
        if self._should_exclude(dir_name, patterns):
            return True

        # Prüfe den vollständigen Pfad
        full_path = parent_path / dir_name
        full_path_str = str(full_path).lower()

        exclude_indicators = ['venv', 'node_modules', '__pycache__', '.git', 'dist', 'build',
                             '.pytest_cache', '.vscode', '.idea', 'target', 'out', '.next',
                             'coverage', '.tox', '.nox', 'env', '.env', 'env.bak', '.env.bak',
                             '__bundle', 'Pods', '.dart_tool', '.pub', 'vendor', 'bower_components',
                             '.npm', '.yarn', 'jspm_packages', '.angular', '.nuxt', '.next',
                             '.vercel', '.netlify', '.cache', 'tmp', 'temp', '.tmp', '.temp',
                             '__pycache__', '.python-version', '.rvmrc', '.gem', 'CMakeFiles',
                             'CMakeCache.txt', '.swp', '.swo', '*.swp', '*.swo', 'node_modules',
                             '.serverless', '.dynamodb', '.fusebox', '.nyc_output', '.sass-cache',
                             'coverage', 'lib-cov', '*.lcov', '.nyc_output', '.istanbul', 'e2e',
                             'nightwatch', 'webdriver', '.grunt', '.lock-wscript', 'npm-debug.log',
                             'yarn-debug.log', 'yarn-error.log', '.yarn-integrity', '.yarn-metadata',
                             'node_modules', '.npm', '.node_repl_history', '.nvm', '.rbenv',
                             '.ruby-version', '.bundle', 'vendor/bundle', 'vendor/cache', 'vendor/gems',
                             'vendor/ruby', 'Pods', '.paket', 'paket-files', '.paket', 'packages',
                             'lib', 'obj', 'TestResults', '*.nupkg', '.nuget', 'packages.lock.json',
                             '.pypirc', '.python-history', '.pytest_cache', '.hypothesis', 'site-packages',
                             'pip-log.txt', 'pip-delete-this-directory.txt', '.tox', '.coverage',
                             'htmlcov', '.cover', '.hypothesis', '.pytest_cache', '.pyre', '.pytype',
                             'mypy_cache', '.mypy_cache', 'venv', 'ENV', 'env', 'env.bak', '.env',
                             '.env.bak', 'venv.bak', '.venv', 'ENV', '.ENV', 'env', 'venv',
                             'ENV', 'env.bak', '.env', '.env.bak', 'venv.bak', '.venv', '.venv',
                             '.pytest_cache', '.coverage', 'htmlcov', '.cover', '.hypothesis',
                             '__pycache__', '*.pyc', '__pycache__', '*.pyc', '*.pyo', '*.pyd',
                             '.Python', 'pip-log.txt', 'pip-delete-this-directory.txt', '.spyderproject',
                             '.spyproject', '.ropeproject', 'site-packages', '.mypy_cache',
                             'mypy_cache', '.dmypy.json', 'dmypy.json', '.pyre', '.pytype',
                             'pyrightconfig.json', '.vs', '.vscode', '.idea', '.sublime-workspace',
                             '.sublimelintcache', '*.sublime-project', '.project', '.c9', '*.c9revisions',
                             '*_c9s', '.settings', '.vscode', '.history', '.vagrant', 'vagrant-*.out',
                             'vagrant-*.err', 'CACHEDIR.TAG', 'node_modules', '.npm', '.node_repl_history',
                             'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*', '.nyc_output',
                             'coverage', 'coverage/lcov-report', '.nyc_output', 'nyc_output',
                             '.istanbul', 'e2e', 'nightwatch', 'webdriver', 'node_modules', '.npm',
                             '.node_repl_history', '.nvm', '.rbenv', '.ruby-version', '.bundle',
                             'vendor/bundle', 'vendor/cache', 'vendor/gems', 'vendor/ruby',
                             'paket-files', '.paket', 'packages', 'lib', 'obj', 'TestResults',
                             '*.nupkg', '.nuget', 'packages.lock.json', '.paket', '.pypirc',
                             '.python-history', '.pytest_cache', '.hypothesis', 'site-packages',
                             'pip-log.txt', 'pip-delete-this-directory.txt', '.tox', '.coverage',
                             'htmlcov', '.cover', '.hypothesis', '.pytest_cache', '.pyre', '.pytype',
                             'mypy_cache', '.mypy_cache', 'venv', 'ENV', 'env', 'env.bak', '.env',
                             '.env.bak', 'venv.bak', '.venv']

        for indicator in exclude_indicators:
            if f'/{indicator}/' in full_path_str or full_path_str.endswith('/' + indicator) or \
               full_path_str.startswith(indicator + '/') or indicator == os.path.basename(full_path_str):
                return True

        return False

    def _should_include_file(self, file_path: Path) -> bool:
        """Prüft, ob eine Datei eingeschlossen werden sollte"""
        filename = file_path.name.lower()

        # Ausschlussdateien prüfen
        for exclude_pattern in self.config.exclude_files:
            if fnmatch(filename, exclude_pattern.lower()):
                return False

        # Ausschluss für bestimmte Verzeichnisse (z.B. venv, node_modules)
        # Prüfe, ob der Dateipfad bestimmte Ausschluss-Verzeichnisse enthält
        file_path_str = str(file_path).lower()
        exclude_dirs = ['venv', 'node_modules', '__pycache__', '.git', 'dist', 'build', '.pytest_cache', '.vscode', '.idea', 'target', 'out', '.next', 'coverage', '.tox', '.nox', 'env', '.env', 'env.bak', '.env.bak', '__bundle', 'Pods', '.dart_tool', '.pub', 'vendor', 'bower_components', '.npm', '.yarn', 'jspm_packages', '.angular', '.nuxt', '.next', '.vercel', '.netlify', '.cache', 'tmp', 'temp', '.tmp', '.temp']
        for exclude_dir in exclude_dirs:
            if f'/{exclude_dir}/' in file_path_str or file_path_str.startswith(exclude_dir + '/') or file_path_str.endswith('/' + exclude_dir) or exclude_dir == os.path.basename(file_path_str):
                return False

        # Einschlussmuster prüfen
        for include_pattern in self.config.include_patterns:
            if fnmatch(filename, include_pattern.lower()):
                return True

        return False