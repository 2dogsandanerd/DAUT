import os
import re
from pathlib import Path
from typing import List, Set
from git import Repo, GitCommandError


class GitIgnoreHandler:
    """
    Klasse zur Behandlung von .gitignore-Dateien, einschließlich verschachtelter .gitignore-Dateien
    """
    
    def __init__(self, base_path: Path):
        """
        Initialisiert den GitIgnoreHandler
        
        Args:
            base_path: Basisverzeichnis des Projekts
        """
        self.base_path = Path(base_path)
        self.repo = None
        
        # Versuche, ein Git-Repository zu finden
        try:
            self.repo = Repo(self.base_path, search_parent_directories=True)
        except:
            # Kein Git-Repository vorhanden
            pass
            
        self.ignored_patterns = {}
        self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """
        Lädt .gitignore-Muster rekursiv für jedes Verzeichnis
        """
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Prüfe auf .gitignore-Datei im aktuellen Verzeichnis
            gitignore_path = root_path / '.gitignore'
            if gitignore_path.exists():
                # Lese Muster aus der .gitignore-Datei
                patterns = self._read_gitignore_patterns(gitignore_path)
                self.ignored_patterns[str(root_path)] = patterns
    
    def _read_gitignore_patterns(self, gitignore_path: Path) -> List[str]:
        """
        Liest Muster aus einer .gitignore-Datei
        
        Args:
            gitignore_path: Pfad zur .gitignore-Datei
            
        Returns:
            Liste von Muster-Strings
        """
        patterns = []
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Überspringe Kommentare und leere Zeilen
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception:
            pass  # Ignoriere Datei, wenn nicht lesbar
        
        return patterns

    def _matches_pattern(self, file_path: Path, pattern: str) -> bool:
        """
        Prüft, ob ein Dateipfad mit einem .gitignore-Muster übereinstimmt
        
        Args:
            file_path: Zu prüfender Dateipfad
            pattern: .gitignore-Muster
            
        Returns:
            True, wenn der Pfad mit dem Muster übereinstimmt
        """
        # Konvertiere alle Backslashes zu Slashes (für Windows-Kompatibilität)
        path_str = str(file_path).replace('\\', '/')
        pattern = pattern.replace('\\', '/')
        
        # Behandle absolute Pfade relativ zum Basisverzeichnis
        try:
            rel_path = file_path.relative_to(self.base_path).as_posix()
        except ValueError:
            # Pfad ist nicht innerhalb des Basisverzeichnisses
            return False
        
        # Prüfe auf Übereinstimmung mit dem Muster
        return self._path_matches_pattern(rel_path, pattern)

    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Prüft, ob ein Pfad mit einem .gitignore-Muster übereinstimmt
        
        Args:
            path: Relativer Pfad (zum Basisverzeichnis)
            pattern: .gitignore-Muster
            
        Returns:
            True, wenn der Pfad mit dem Muster übereinstimmt
        """
        # Entferne führende Slashes
        path = path.lstrip('/')
        
        # Konvertiere .gitignore-Muster zu regulären Ausdrücken
        # Dies ist eine vereinfachte Implementierung; für vollständige .gitignore-Unterstützung
        # müsste man eine komplexere Musteranpassung implementieren
        
        # Entferne führende ! (für Negationen), die wir hier vorerst ignorieren
        if pattern.startswith('!'):
            return False  # Ignoriere Negationen vorerst
            
        # Ersetze .gitignore-spezifische Symbole durch reguläre Ausdrücke
        regex_pattern = pattern
        
        # Behandle Muster, die mit / beginnen (nur im aktuellen Verzeichnis)
        if pattern.startswith('/'):
            regex_pattern = f'^{self._convert_to_regex(pattern[1:])}'
        # Globale Muster, die überall gelten
        elif pattern.startswith('**/'):
            regex_pattern = f'{self._convert_to_regex(pattern)}'
        # Standardmuster
        else:
            regex_pattern = f'{self._convert_to_regex(pattern)}'
            
        # Füge .* hinzu, wenn das Muster keinen globalen Match beinhaltet
        if not pattern.startswith('**/'):
            if '/' in pattern:
                # Wenn Muster Schrägstriche enthält, prüfe als exakter Pfad
                pass
            else:
                # Wenn Muster keinen Schrägstrich enthält, kann es überall vorkommen
                regex_pattern = f'.*/{regex_pattern}'
        
        # Versuche, mit regulärem Ausdruck zu matchen
        try:
            return re.match(regex_pattern, path, re.IGNORECASE) is not None
        except re.error:
            # Falls das Muster ungültigen Regex enthält
            return False

    def _convert_to_regex(self, pattern: str) -> str:
        """
        Konvertiert ein .gitignore-Muster zu einem regulären Ausdruck
        
        Args:
            pattern: .gitignore-Muster
            
        Returns:
            Regulärer Ausdruck
        """
        # Escape spezielle Regex-Zeichen, aber lasse .gitignore-Symbole zu
        regex = re.escape(pattern)
        
        # Wandele .gitignore-Symbole zurück
        # ** -> .*
        regex = regex.replace('\\*\\*\\/', '.*\/')
        regex = regex.replace('\\*\\*', '.*')
        
        # * -> [^/]* (beliebige Zeichen außer Schrägstrich)
        regex = regex.replace('\\*', '[^/]*')
        
        # ? -> [^/] (ein beliebiges Zeichen außer Schrägstrich)
        regex = regex.replace('\\?', '[^/]')
        
        # [] werden bereits escaped, also belassen wir es dabei
        
        return f"({regex})"

    def is_ignored(self, file_path: Path) -> bool:
        """
        Prüft, ob eine Datei von .gitignore ignoriert wird
        
        Args:
            file_path: Zu prüfender Dateipfad
            
        Returns:
            True, wenn die Datei ignoriert wird
        """
        # Kurzschluss, wenn Git-Repository vorhanden und Datei durch Git ignoriert wird
        if self.repo:
            try:
                relative_path = str(file_path.relative_to(self.repo.working_dir).as_posix())
                if self.repo.ignored(relative_path):
                    return True
            except ValueError:
                # Datei liegt außerhalb des Repositorys
                pass
            except GitCommandError:
                # Wenn Git-Fehler auftritt, verwende unsere Implementierung
                pass
        
        # Prüfe das Dateipfad relativ zu den .gitignore-Dateien
        file_path = Path(file_path)
        
        # Prüfe für alle relevanten Verzeichnisse
        # Gehe von der Datei aus nach oben bis zur Wurzel
        current_dir = file_path.parent
        while current_dir != current_dir.parent and self.base_path in current_dir.parents:
            dir_str = str(current_dir)
            if dir_str in self.ignored_patterns:
                patterns = self.ignored_patterns[dir_str]
                for pattern in patterns:
                    if self._matches_pattern(file_path, pattern):
                        return True
            
            # Gehe eine Ebene höher
            parent = current_dir.parent
            if parent == current_dir:  # Hat die Wurzel erreicht
                break
            current_dir = parent
        
        # Prüfe auch das Basisverzeichnis
        base_dir_str = str(self.base_path)
        if base_dir_str in self.ignored_patterns:
            for pattern in self.ignored_patterns[base_dir_str]:
                if self._matches_pattern(file_path, pattern):
                    return True
        
        return False