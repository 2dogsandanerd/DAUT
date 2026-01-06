"""
Parser für Go und Rust Dateien
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import re


class GoParser:
    """Parser für Go-Dateien"""
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine Go-Datei und extrahiert Funktionen, Strukturen und Methoden"""
        elements = []
        
        if file_path.suffix.lower() != '.go':
            return elements
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return elements
        
        # Extrahiere Paketname
        package_match = re.search(r'package\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        package_name = package_match.group(1) if package_match else "main"
        
        # Extrahiere Funktionen
        function_pattern = r'func\s+(?:\([^)]+\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:[^{;]*{?|[^{;]*;)'
        function_matches = re.finditer(function_pattern, content)
        
        lines = content.split('\n')
        
        for match in function_matches:
            func_name = match.group(1)
            
            # Finde die Zeile, in der die Funktion definiert ist
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': func_name,
                'type': 'function',
                'signature': line_content.strip(),
                'package': package_name,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        # Extrahiere Strukturen
        struct_pattern = r'type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct\s*{'
        struct_matches = re.finditer(struct_pattern, content)
        
        for match in struct_matches:
            struct_name = match.group(1)
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': struct_name,
                'type': 'struct',
                'signature': line_content.strip(),
                'package': package_name,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        # Extrahiere Interfaces
        interface_pattern = r'type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+interface\s*{'
        interface_matches = re.finditer(interface_pattern, content)
        
        for match in interface_matches:
            interface_name = match.group(1)
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': interface_name,
                'type': 'interface',
                'signature': line_content.strip(),
                'package': package_name,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        return elements
    
    def _get_code_snippet(self, lines: List[str], start_line: int, context_lines: int = 5) -> str:
        """Extrahiert einen Code-Snippet um eine bestimmte Zeile"""
        start = max(0, start_line - context_lines // 2)
        end = min(len(lines), start_line + context_lines // 2 + 1)
        return '\n'.join(lines[start:end]).strip()


class RustParser:
    """Parser für Rust-Dateien"""
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine Rust-Datei und extrahiert Funktionen, Strukturen, Enums und Traits"""
        elements = []
        
        if file_path.suffix.lower() != '.rs':
            return elements
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return elements
        
        lines = content.split('\n')
        
        # Extrahiere Funktionen (inkl. async, unsafe, etc.)
        function_pattern = r'(?P<attrs>(?:#\[[^\]]*\]\s*)*)\s*(?P<visibility>pub\s+)?(?:async\s+|unsafe\s+|const\s+)?fn\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:->\s*[^{;]*)?'
        function_matches = re.finditer(function_pattern, content)
        
        for match in function_matches:
            func_name = match.group('name')
            visibility = match.group('visibility')
            attrs = match.group('attrs').strip() if match.group('attrs') else ""
            
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': func_name,
                'type': 'function',
                'signature': line_content.strip(),
                'visibility': visibility.strip() if visibility else 'private',
                'attributes': attrs,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        # Extrahiere Strukturen
        struct_pattern = r'(?P<attrs>(?:#\[[^\]]*\]\s*)*)\s*(?P<visibility>pub\s+)?struct\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'
        struct_matches = re.finditer(struct_pattern, content)
        
        for match in struct_matches:
            struct_name = match.group('name')
            visibility = match.group('visibility')
            attrs = match.group('attrs').strip() if match.group('attrs') else ""
            
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': struct_name,
                'type': 'struct',
                'signature': line_content.strip(),
                'visibility': visibility.strip() if visibility else 'private',
                'attributes': attrs,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        # Extrahiere Enums
        enum_pattern = r'(?P<attrs>(?:#\[[^\]]*\]\s*)*)\s*(?P<visibility>pub\s+)?enum\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'
        enum_matches = re.finditer(enum_pattern, content)
        
        for match in enum_matches:
            enum_name = match.group('name')
            visibility = match.group('visibility')
            attrs = match.group('attrs').strip() if match.group('attrs') else ""
            
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': enum_name,
                'type': 'enum',
                'signature': line_content.strip(),
                'visibility': visibility.strip() if visibility else 'private',
                'attributes': attrs,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        # Extrahiere Traits
        trait_pattern = r'(?P<attrs>(?:#\[[^\]]*\]\s*)*)\s*(?P<visibility>pub\s+)?trait\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'
        trait_matches = re.finditer(trait_pattern, content)
        
        for match in trait_matches:
            trait_name = match.group('name')
            visibility = match.group('visibility')
            attrs = match.group('attrs').strip() if match.group('attrs') else ""
            
            line_start = content[:match.start()].count('\n')
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            element = {
                'name': trait_name,
                'type': 'trait',
                'signature': line_content.strip(),
                'visibility': visibility.strip() if visibility else 'private',
                'attributes': attrs,
                'line_number': line_start + 1,
                'file_path': str(file_path),
                'code_snippet': self._get_code_snippet(lines, line_start)
            }
            
            elements.append(element)
        
        return elements
    
    def _get_code_snippet(self, lines: List[str], start_line: int, context_lines: int = 5) -> str:
        """Extrahiert einen Code-Snippet um eine bestimmte Zeile"""
        start = max(0, start_line - context_lines // 2)
        end = min(len(lines), start_line + context_lines // 2 + 1)
        return '\n'.join(lines[start:end]).strip()


# Funktionen zur Erkennung der Sprache anhand des Dateiinhalts
def is_go_file(file_path: Path) -> bool:
    """Prüft, ob es sich um eine Go-Datei handelt"""
    if file_path.suffix.lower() != '.go':
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # Nur die ersten 1000 Zeichen lesen
        return 'package ' in content and 'import' in content
    except:
        return False


def is_rust_file(file_path: Path) -> bool:
    """Prüft, ob es sich um eine Rust-Datei handelt"""
    if file_path.suffix.lower() != '.rs':
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # Nur die ersten 1000 Zeichen lesen
        return 'fn ' in content and ('mod ' in content or 'use ' in content)
    except:
        return False