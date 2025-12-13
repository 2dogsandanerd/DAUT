import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Union
from ..models.element import CodeElement, ElementType
from ..core.config_manager import ProjectConfig

class CodeScanner:
    def __init__(self, config: ProjectConfig):
        self.config = config
    
    def scan_file(self, file_path: Path) -> List[CodeElement]:
        """Scannt eine Code-Datei und extrahiert alle relevanten Elemente"""
        elements = []
        
        if file_path.suffix.lower() == '.py':
            elements = self._scan_python_file(file_path)
        elif file_path.suffix.lower() in ['.js', '.jsx', '.ts', '.tsx']:
            elements = self._scan_javascript_file(file_path)
        
        # Hinzufügen von Dateiinformationen zu jedem Element
        for element in elements:
            element.file_path = str(file_path)
            element.project_path = str(file_path.parent)
        
        return elements
    
    def _scan_python_file(self, file_path: Path) -> List[CodeElement]:
        """Scannt eine Python-Datei mit AST"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception as e:
            print(f"Fehler beim Parsen von {file_path}: {e}")
            return []
        
        elements = []
        
        for node in ast.walk(tree):
            element = None
            
            if isinstance(node, ast.FunctionDef):
                element = self._extract_function_info(node, file_path, content)
            elif isinstance(node, ast.AsyncFunctionDef):
                element = self._extract_function_info(node, file_path, content)
            elif isinstance(node, ast.ClassDef):
                element = self._extract_class_info(node, file_path, content)
            elif isinstance(node, ast.Import):
                element = self._extract_import_info(node, file_path)
            elif isinstance(node, ast.ImportFrom):
                element = self._extract_import_from_info(node, file_path)
            
            if element:
                elements.append(element)
        
        return elements
    
    def _extract_function_info(self, node: ast.AST, file_path: Path, content: str) -> CodeElement:
        """Extrahiert Informationen aus einer Python-Funktion"""
        # Parameter extrahieren
        args = []
        defaults = node.args.defaults
        num_defaults = len(defaults)
        
        for i, arg in enumerate(node.args.args):
            default = None
            if i >= len(node.args.args) - num_defaults:
                default_idx = i - (len(node.args.args) - num_defaults)
                if default_idx < len(defaults):
                    default = ast.unparse(defaults[default_idx])
            
            args.append({
                'name': arg.arg,
                'type_annotation': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': default
            })
        
        # Rückgabetyp extrahieren
        return_annotation = ast.unparse(node.returns) if node.returns else None
        
        # Docstring extrahieren
        docstring = ast.get_docstring(node) or ""
        
        # API-Endpunkt-Erkennung
        api_endpoint = None
        api_method = None
        api_path = None
        is_api = False
        
        # Suche nach Decorator-ähnlichen Mustern
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                decorator_id = ast.unparse(decorator.func)
                if any(api_marker in decorator_id.lower() for api_marker in ['app.get', 'app.post', 'app.put', 'app.delete', 'router.get', 'router.post', 'router.put', 'router.delete']):
                    is_api = True
                    # Versuche API-Pfad zu extrahieren
                    if decorator.args:
                        try:
                            api_path = ast.literal_eval(decorator.args[0])
                        except:
                            api_path = "unknown"
                    api_method = decorator_id.split('.')[-1].upper()
            elif isinstance(decorator, ast.Name):
                if decorator.id in ['get', 'post', 'put', 'delete']:
                    is_api = True
                    api_method = decorator.id.upper()
        
        # Code-Snippet extrahieren
        lines = content.split('\n')
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', node.lineno + 10)  # Falls end_lineno nicht verfügbar
        code_snippet = '\n'.join(lines[start_line-1:end_line])
        
        return CodeElement(
            name=node.name,
            type=ElementType.API_ENDPOINT if is_api else ElementType.FUNCTION,
            signature=ast.unparse(node),
            parameters=args,
            return_type=return_annotation,
            docstring=docstring,
            api_info={
                'endpoint': api_path,
                'method': api_method
            } if is_api else None,
            line_number=node.lineno,
            code_snippet=code_snippet
        )
    
    def _extract_class_info(self, node: ast.AST, file_path: Path, content: str) -> CodeElement:
        """Extrahiert Informationen aus einer Python-Klasse"""
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    'name': item.name,
                    'is_private': item.name.startswith('_')
                })
        
        docstring = ast.get_docstring(node) or ""
        
        lines = content.split('\n')
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', node.lineno + len(node.body) * 5)
        code_snippet = '\n'.join(lines[start_line-1:end_line])
        
        return CodeElement(
            name=node.name,
            type=ElementType.CLASS,
            signature=ast.unparse(node),
            methods=methods,
            docstring=docstring,
            line_number=node.lineno,
            code_snippet=code_snippet
        )
    
    def _extract_import_info(self, node: ast.AST, file_path: Path) -> CodeElement:
        """Extrahiert Import-Informationen"""
        names = [alias.name for alias in node.names]
        return CodeElement(
            name=', '.join(names),
            type=ElementType.IMPORT,
            imports=names,
            line_number=node.lineno
        )
    
    def _extract_import_from_info(self, node: ast.AST, file_path: Path) -> CodeElement:
        """Extrahiert Import-from-Informationen"""
        module = node.module or ''
        names = [alias.name for alias in node.names]
        return CodeElement(
            name=f"from {module}: {', '.join(names)}",
            type=ElementType.IMPORT,
            imports=names,
            import_from=module,
            line_number=node.lineno
        )
    
    def _scan_javascript_file(self, file_path: Path) -> List[CodeElement]:
        """Scannt eine JavaScript-Datei"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return []
        
        elements = []
        
        # Funktionen (inkl. Arrow-Funktionen)
        function_pattern = r'(?:function\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)'
        arrow_function_pattern = r'const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\([^)]*\)\s*=>'
        class_pattern = r'(?:export\s+)?class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
        
        # Funktionen finden
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            line_start = content[:match.start()].count('\n') + 1
            elements.append(CodeElement(
                name=func_name,
                type=ElementType.FUNCTION,
                line_number=line_start,
                signature=match.group(0)
            ))
        
        # Arrow-Funktionen finden
        for match in re.finditer(arrow_function_pattern, content):
            func_name = match.group(1)
            line_start = content[:match.start()].count('\n') + 1
            elements.append(CodeElement(
                name=func_name,
                type=ElementType.FUNCTION,
                line_number=line_start,
                signature=match.group(0)
            ))
        
        # Klassen finden
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            line_start = content[:match.start()].count('\n') + 1
            elements.append(CodeElement(
                name=class_name,
                type=ElementType.CLASS,
                line_number=line_start,
                signature=match.group(0)
            ))
        
        return elements