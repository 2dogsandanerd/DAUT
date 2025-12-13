import re
from pathlib import Path
from typing import List
from ..models.element import DocElement, ElementType
from ..core.config_manager import ProjectConfig

class DocScanner:
    def __init__(self, config: ProjectConfig):
        self.config = config
    
    def scan_file(self, file_path: Path) -> List[DocElement]:
        """Scannt eine Dokumentationsdatei und extrahiert alle relevanten Elemente"""
        elements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return elements
        
        if file_path.suffix.lower() == '.md':
            elements = self._scan_markdown_file(content, file_path)
        elif file_path.suffix.lower() == '.rst':
            elements = self._scan_rst_file(content, file_path)
        elif file_path.suffix.lower() == '.txt':
            elements = self._scan_txt_file(content, file_path)
        
        # Hinzufügen von Dateiinformationen zu jedem Element
        for element in elements:
            element.file_path = str(file_path)
            element.project_path = str(file_path.parent)
        
        return elements
    
    def _scan_markdown_file(self, content: str, file_path: Path) -> List[DocElement]:
        """Scannt eine Markdown-Datei"""
        elements = []
        
        # Überschriften extrahieren
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        code_block_pattern = r'```(\w*)\n(.*?)```'
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                elements.append(DocElement(
                    name=title,
                    type=ElementType.DOC_HEADING,
                    level=level,
                    content=line.strip(),
                    line_number=i + 1
                ))
        
        # Code-Blöcke extrahieren
        for match in re.finditer(code_block_pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            # Find line number by counting newlines before this match
            line_number = content[:match.start()].count('\n') + 1
            elements.append(DocElement(
                name=f"Code block ({language})",
                type=ElementType.DOC_CODE_BLOCK,
                language=language,
                content=code,
                line_number=line_number
            ))
        
        # Dateiweiter Inhalt als allgemeines Dokument
        elements.append(DocElement(
            name=file_path.stem,
            type=ElementType.DOCUMENTATION,
            content=content[:1000],  # Erste 1000 Zeichen als Vorschau
            full_content=content
        ))
        
        return elements
    
    def _scan_rst_file(self, content: str, file_path: Path) -> List[DocElement]:
        """Scannt eine reStructuredText-Datei"""
        elements = []
        
        # RST-Überschriften extrahieren (vereinfachte Variante)
        # RST verwendet verschiedene Zeichen zum Unterstreichen
        rst_heading_pattern = r'^([^\n]+)\n([=]+|-|~|`|#|\*|\.){2,}$'
        
        for match in re.finditer(rst_heading_pattern, content, re.MULTILINE):
            title = match.group(1).strip()
            elements.append(DocElement(
                name=title,
                type=ElementType.DOC_HEADING,
                content=match.group(0),
                line_number=content[:match.start()].count('\n') + 1
            ))
        
        # Dateiweiter Inhalt als allgemeines Dokument
        elements.append(DocElement(
            name=file_path.stem,
            type=ElementType.DOCUMENTATION,
            content=content[:1000],  # Erste 1000 Zeichen als Vorschau
            full_content=content
        ))
        
        return elements
    
    def _scan_txt_file(self, content: str, file_path: Path) -> List[DocElement]:
        """Scannt eine Text-Datei"""
        elements = []
        
        # Einfache Struktur für Textdateien
        elements.append(DocElement(
            name=file_path.stem,
            type=ElementType.DOCUMENTATION,
            content=content[:2000],  # Erste 2000 Zeichen
            full_content=content
        ))
        
        return elements