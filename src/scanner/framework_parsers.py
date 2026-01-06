"""
Basisklasse und Implementierungen für Framework-spezifische Code-Parser
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import ast
import re


class FrameworkParser(ABC):
    """Abstrakte Basisklasse für Framework-spezifische Parser"""
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine Datei und gibt eine Liste von Code-Elementen zurück"""
        pass
    
    @abstractmethod
    def get_framework_name(self) -> str:
        """Gibt den Namen des Frameworks zurück"""
        pass


class FastAPIParser(FrameworkParser):
    """Parser für FastAPI-Anwendungen"""
    
    def get_framework_name(self) -> str:
        return "fastapi"
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine Python-Datei auf FastAPI-Elemente"""
        elements = []
        
        if file_path.suffix.lower() != '.py':
            return elements
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return elements
        
        # Suche nach FastAPI-spezifischen Mustern
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Prüfe auf FastAPI-Router-Dekoratoren
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        decorator_name = self._get_decorator_name(decorator)
                        if decorator_name in ['app.get', 'app.post', 'app.put', 'app.delete', 'app.patch', 
                                            'router.get', 'router.post', 'router.put', 'router.delete', 'router.patch']:
                            # Extrahiere API-Informationen
                            api_info = self._extract_api_info(decorator, node)
                            element = {
                                'name': node.name,
                                'type': 'api_endpoint',
                                'signature': ast.unparse(node),
                                'api_info': api_info,
                                'line_number': node.lineno,
                                'file_path': str(file_path),
                                'code_snippet': self._get_code_snippet(content, node)
                            }
                            elements.append(element)
        
        return elements
    
    def _get_decorator_name(self, decorator) -> str:
        """Extrahiert den Namen eines Dekorators"""
        if isinstance(decorator.func, ast.Attribute):
            # z.B. app.get oder router.get
            attr_chain = []
            current = decorator.func
            while isinstance(current, ast.Attribute):
                attr_chain.insert(0, current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                attr_chain.insert(0, current.id)
            return '.'.join(attr_chain)
        elif isinstance(decorator.func, ast.Name):
            return decorator.func.id
        return ""
    
    def _extract_api_info(self, decorator, func_node) -> Dict[str, Any]:
        """Extrahiert API-Informationen aus einem Dekorator"""
        api_info = {
            'method': 'GET',  # Standardwert
            'path': '/',
            'summary': '',
            'description': ''
        }
        
        # Extrahiere Pfad aus den Argumenten
        if decorator.args:
            try:
                path_arg = ast.literal_eval(decorator.args[0])
                api_info['path'] = path_arg
            except:
                api_info['path'] = 'unknown'
        
        # Bestimme die Methode aus dem Dekoratornamen
        decorator_name = self._get_decorator_name(decorator).lower()
        if 'get' in decorator_name:
            api_info['method'] = 'GET'
        elif 'post' in decorator_name:
            api_info['method'] = 'POST'
        elif 'put' in decorator_name:
            api_info['method'] = 'PUT'
        elif 'delete' in decorator_name:
            api_info['method'] = 'DELETE'
        elif 'patch' in decorator_name:
            api_info['method'] = 'PATCH'
        
        # Extrahiere Docstring
        docstring = ast.get_docstring(func_node)
        if docstring:
            lines = docstring.split('\n')
            api_info['summary'] = lines[0].strip() if lines else ''
            api_info['description'] = docstring.strip()
        
        return api_info
    
    def _get_code_snippet(self, content: str, node) -> str:
        """Extrahiert einen Code-Snippet für das Node"""
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 10)
        # Begrenze den Snippet auf maximal 20 Zeilen
        end_line = min(end_line, start_line + 20)
        return '\n'.join(lines[start_line:end_line])


class FlaskParser(FrameworkParser):
    """Parser für Flask-Anwendungen"""
    
    def get_framework_name(self) -> str:
        return "flask"
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine Python-Datei auf Flask-Elemente"""
        elements = []
        
        if file_path.suffix.lower() != '.py':
            return elements
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return elements
        
        # Suche nach Flask-spezifischen Mustern
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Prüfe auf Flask-Route-Dekoratoren
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr == 'route':
                            # Extrahiere Route-Informationen
                            route_info = self._extract_route_info(decorator, node)
                            element = {
                                'name': node.name,
                                'type': 'api_endpoint',
                                'signature': ast.unparse(node),
                                'api_info': route_info,
                                'line_number': node.lineno,
                                'file_path': str(file_path),
                                'code_snippet': self._get_code_snippet(content, node)
                            }
                            elements.append(element)
        
        return elements
    
    def _extract_route_info(self, decorator, func_node) -> Dict[str, Any]:
        """Extrahiert Route-Informationen aus einem @app.route-Dekorator"""
        route_info = {
            'method': 'GET',  # Standardwert
            'path': '/',
            'methods': ['GET'],
            'summary': '',
            'description': ''
        }
        
        # Extrahiere Pfad aus den Argumenten
        if decorator.args:
            try:
                path_arg = ast.literal_eval(decorator.args[0])
                route_info['path'] = path_arg
            except:
                route_info['path'] = 'unknown'
        
        # Extrahiere Methoden aus den Keywords
        for keyword in decorator.keywords:
            if keyword.arg == 'methods' and isinstance(keyword.value, ast.List):
                methods = []
                for elt in keyword.value.elts:
                    try:
                        method = ast.literal_eval(elt)
                        methods.append(method.upper())
                    except:
                        pass
                if methods:
                    route_info['methods'] = methods
                    route_info['method'] = methods[0]  # Nimm die erste Methode als Hauptmethode
        
        # Extrahiere Docstring
        docstring = ast.get_docstring(func_node)
        if docstring:
            lines = docstring.split('\n')
            route_info['summary'] = lines[0].strip() if lines else ''
            route_info['description'] = docstring.strip()
        
        return route_info
    
    def _get_code_snippet(self, content: str, node) -> str:
        """Extrahiert einen Code-Snippet für das Node"""
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 10)
        # Begrenze den Snippet auf maximal 20 Zeilen
        end_line = min(end_line, start_line + 20)
        return '\n'.join(lines[start_line:end_line])


class ExpressParser(FrameworkParser):
    """Parser für Express.js-Anwendungen"""
    
    def get_framework_name(self) -> str:
        return "express"
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine JavaScript-Datei auf Express-Elemente"""
        elements = []
        
        if file_path.suffix.lower() not in ['.js', '.ts']:
            return elements
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return elements
        
        # Reguläre Ausdrücke für Express-Router
        # Muster für app.get('/path', handler) oder router.post('/path', handler)
        patterns = [
            r'(app|router|express)\.(get|post|put|delete|patch|all)\s*\(\s*["\']([^"\']+)["\']\s*,\s*([a-zA-Z_$][a-zA-Z0-9_$]*)',
            r'(app|router|express)\.(get|post|put|delete|patch|all)\s*\(\s*["\']([^"\']+)["\']\s*,\s*function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            r'(app|router|express)\.(get|post|put|delete|patch|all)\s*\(\s*["\']([^"\']+)["\']\s*,\s*\([^)]*\)\s*=>'
        ]
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    method = match.group(2).upper()
                    path = match.group(3)
                    
                    element = {
                        'name': f"{method}_{path.replace('/', '_').strip('_')}",  # Generiere einen Namen
                        'type': 'api_endpoint',
                        'api_info': {
                            'method': method,
                            'path': path,
                            'summary': f'{method} endpoint for {path}',
                            'description': f'Express {method} endpoint for path: {path}'
                        },
                        'line_number': i,
                        'file_path': str(file_path),
                        'code_snippet': line.strip()
                    }
                    elements.append(element)
        
        return elements


class DjangoParser(FrameworkParser):
    """Parser für Django-Anwendungen"""
    
    def get_framework_name(self) -> str:
        return "django"
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parst eine Python-Datei auf Django-Elemente"""
        elements = []
        
        if file_path.suffix.lower() != '.py':
            return elements
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return elements
        
        # Suche nach Django Views
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Prüfe auf Django-spezifische Klassen oder Funktionen
                is_django_view = False
                
                # Funktionen mit bestimmten Mustern
                if isinstance(node, ast.FunctionDef):
                    # Prüfe auf common Django view patterns
                    if any(pattern in node.name.lower() for pattern in ['view', 'get', 'post', 'put', 'delete']):
                        is_django_view = True
                
                # Klassen, die von Django-Klassen erben
                elif isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Attribute):
                            base_name = self._get_attribute_name(base)
                            if any(django_base in base_name.lower() for django_base in 
                                   ['view', 'apiview', 'generic', 'django']):
                                is_django_view = True
                        elif isinstance(base, ast.Name) and 'view' in base.id.lower():
                            is_django_view = True
                
                if is_django_view:
                    element = {
                        'name': node.name,
                        'type': 'django_view',
                        'signature': ast.unparse(node),
                        'line_number': node.lineno,
                        'file_path': str(file_path),
                        'code_snippet': self._get_code_snippet(content, node)
                    }
                    elements.append(element)
        
        return elements
    
    def _get_attribute_name(self, attr_node) -> str:
        """Hilfsmethode, um den Namen eines Attributs zu erhalten"""
        if isinstance(attr_node, ast.Attribute):
            return attr_node.attr
        elif isinstance(attr_node, ast.Name):
            return attr_node.id
        return ""
    
    def _get_code_snippet(self, content: str, node) -> str:
        """Extrahiert einen Code-Snippet für das Node"""
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 10)
        # Begrenze den Snippet auf maximal 20 Zeilen
        end_line = min(end_line, start_line + 20)
        return '\n'.join(lines[start_line:end_line])


# Factory-Funktion zur Erstellung von Framework-Parsern
def get_framework_parser(framework_name: str) -> Optional[FrameworkParser]:
    """Gibt einen Parser für das angegebene Framework zurück"""
    parsers = {
        'fastapi': FastAPIParser(),
        'flask': FlaskParser(),
        'express': ExpressParser(),
        'django': DjangoParser()
    }
    
    return parsers.get(framework_name.lower())