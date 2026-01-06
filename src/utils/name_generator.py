"""
Modul für eindeutige Dateinamensgenerierung basierend auf Dateipfad und Namensräume
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
import re


class UniqueNameGenerator:
    """Klasse zur Generierung eindeutiger Dateinamen basierend auf Dateipfad und Namensräume"""
    
    def __init__(self):
        self.used_names = set()
        self.namespace_map = {}  # Mapping von Dateipfaden zu Namensräumen
    
    def generate_unique_filename(self, 
                                base_name: str, 
                                file_extension: str, 
                                source_file_path: Optional[str] = None,
                                namespace: Optional[str] = None) -> str:
        """
        Generiert einen eindeutigen Dateinamen
        
        Args:
            base_name: Basisname für die Datei
            file_extension: Dateierweiterung (z.B. '.md', '.txt')
            source_file_path: Optionaler Pfad zur Quelldatei zur Namensraumbestimmung
            namespace: Optionaler Namensraum (überschreibt die aus source_file_path abgeleitete)
        
        Returns:
            Ein eindeutiger Dateiname
        """
        # Bereinige den Basisnamen
        clean_base_name = self._sanitize_name(base_name)
        
        # Bestimme den Namensraum
        if namespace:
            ns = namespace
        elif source_file_path:
            ns = self._derive_namespace_from_path(source_file_path)
        else:
            ns = "global"
        
        # Erstelle einen eindeutigen Namen mit Namensraum
        unique_name = self._create_unique_name(clean_base_name, file_extension, ns)
        
        # Merke den Namen als verwendet
        self.used_names.add(unique_name)
        
        # Speichere das Namensraum-Mapping
        if source_file_path:
            self.namespace_map[source_file_path] = ns
        
        return unique_name
    
    def _sanitize_name(self, name: str) -> str:
        """Bereinigt einen Dateinamen von ungültigen Zeichen"""
        # Entferne oder ersetze ungültige Dateinamezeichen
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Entferne führende und nachfolgende Leerzeichen
        sanitized = sanitized.strip()
        # Ersetze Leerzeichen mit Unterstrichen
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized
    
    def _derive_namespace_from_path(self, file_path: str) -> str:
        """Leitet einen Namensraum aus dem Dateipfad ab"""
        path_obj = Path(file_path)
        
        # Verwende die letzten beiden Verzeichnisebenen als Namensraum
        parts = path_obj.parts
        
        # Entferne das Wurzelverzeichnis und wähle die letzten 2 Ebenen
        relevant_parts = [part for part in parts if part and part != '/']
        
        if len(relevant_parts) >= 2:
            # Verwende die letzten beiden Verzeichnisebenen
            namespace = '.'.join(relevant_parts[-2:])
        elif len(relevant_parts) == 1:
            # Verwende das Verzeichnis oder den Dateinamen
            namespace = relevant_parts[0]
        else:
            # Standard-Namensraum
            namespace = "global"
        
        # Bereinige den Namensraum
        namespace = re.sub(r'[^\w_.-]', '_', namespace)
        
        return namespace
    
    def _create_unique_name(self, base_name: str, file_extension: str, namespace: str) -> str:
        """Erstellt einen eindeutigen Dateinamen"""
        # Erstelle den Basisnamen mit Namensraum
        if namespace and namespace != "global":
            candidate_name = f"{namespace}.{base_name}{file_extension}"
        else:
            candidate_name = f"{base_name}{file_extension}"
        
        # Falls der Name bereits verwendet wird, füge einen Zähler hinzu
        counter = 1
        original_candidate = candidate_name
        
        while candidate_name in self.used_names:
            # Erstelle einen Namen mit Zähler
            name_part = f"{base_name}_{counter}"
            if namespace and namespace != "global":
                candidate_name = f"{namespace}.{name_part}{file_extension}"
            else:
                candidate_name = f"{name_part}{file_extension}"
            counter += 1
        
        return candidate_name
    
    def generate_unique_filename_from_element(self, 
                                           element_name: str, 
                                           element_type: str, 
                                           source_file_path: str,
                                           custom_suffix: Optional[str] = None) -> str:
        """
        Generiert einen eindeutigen Dateinamen basierend auf einem Code-Element
        
        Args:
            element_name: Name des Code-Elements (z.B. Funktion, Klasse)
            element_type: Typ des Elements (z.B. 'function', 'class', 'api_endpoint')
            source_file_path: Pfad zur Quelldatei
            custom_suffix: Optionaler benutzerdefinierter Suffix
        
        Returns:
            Ein eindeutiger Dateiname für die Dokumentation
        """
        # Bestimme die Dateierweiterung basierend auf dem Elementtyp
        file_extension = self._get_file_extension_for_element_type(element_type)
        
        # Erstelle einen Basisnamen mit Elementtyp und Name
        if custom_suffix:
            base_name = f"{element_name}_{custom_suffix}"
        else:
            base_name = f"{element_type}_{element_name}"
        
        # Generiere den eindeutigen Dateinamen
        return self.generate_unique_filename(
            base_name=base_name,
            file_extension=file_extension,
            source_file_path=source_file_path
        )
    
    def _get_file_extension_for_element_type(self, element_type: str) -> str:
        """Gibt die passende Dateierweiterung für einen Elementtyp zurück"""
        type_to_ext = {
            'function': '.md',
            'class': '.class.md',
            'api_endpoint': '.api.md',
            'struct': '.struct.md',
            'enum': '.enum.md',
            'interface': '.interface.md',
            'trait': '.trait.md',
            'module': '.module.md',
            'package': '.package.md',
            'documentation': '.md'
        }
        
        return type_to_ext.get(element_type, '.md')
    
    def reset(self):
        """Setzt den Generator zurück und löscht alle gespeicherten Namen"""
        self.used_names.clear()
        self.namespace_map.clear()


class DocumentationFileOrganizer:
    """Organisiert Dokumentationsdateien mit eindeutigen Namen und Namensräumen"""
    
    def __init__(self):
        self.name_generator = UniqueNameGenerator()
    
    def organize_documentation_files(self, 
                                   elements: List[Dict], 
                                   output_dir: str,
                                   naming_strategy: str = "namespace") -> Dict[str, str]:
        """
        Organisiert Dokumentationsdateien mit eindeutigen Namen
        
        Args:
            elements: Liste von Code-Elementen, die dokumentiert werden sollen
            output_dir: Ausgabeverzeichnis für die Dokumentationsdateien
            naming_strategy: Strategie für die Namensgebung ('namespace', 'hash', 'path')
        
        Returns:
            Dictionary mit Zuordnung von Elementnamen zu Dateipfaden
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_mapping = {}
        
        for element in elements:
            element_name = element.get('name', 'unknown')
            element_type = element.get('type', 'documentation')
            source_file = element.get('file_path', 'unknown')
            
            # Generiere einen eindeutigen Dateinamen
            unique_filename = self.name_generator.generate_unique_filename_from_element(
                element_name=element_name,
                element_type=element_type,
                source_file_path=source_file
            )
            
            # Erstelle den vollständigen Dateipfad
            full_path = output_path / unique_filename
            
            # Speichere die Zuordnung
            file_mapping[f"{element_type}:{element_name}"] = str(full_path)
        
        return file_mapping
    
    def get_namespace_for_file(self, file_path: str) -> str:
        """Gibt den Namensraum für eine Datei zurück"""
        return self.name_generator._derive_namespace_from_path(file_path)
    
    def reset_generator(self):
        """Setzt den Namensgenerator zurück"""
        self.name_generator.reset()


# Funktionen für verschiedene Namensstrategien
def create_namespace_based_name(element_name: str, 
                              element_type: str, 
                              source_file_path: str,
                              custom_suffix: Optional[str] = None) -> str:
    """Erstellt einen namensraumbasierten Dateinamen"""
    generator = UniqueNameGenerator()
    return generator.generate_unique_filename_from_element(
        element_name=element_name,
        element_type=element_type,
        source_file_path=source_file_path,
        custom_suffix=custom_suffix
    )


def create_hash_based_name(element_name: str, 
                          element_type: str, 
                          source_file_path: str,
                          custom_suffix: Optional[str] = None) -> str:
    """Erstellt einen hashbasierten Dateinamen (für maximale Eindeutigkeit)"""
    # Erstelle einen Hash aus dem Elementnamen, Typ und Dateipfad
    hash_input = f"{element_name}_{element_type}_{source_file_path}_{custom_suffix or ''}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    # Bestimme die Dateierweiterung
    type_to_ext = {
        'function': '.md',
        'class': '.class.md',
        'api_endpoint': '.api.md',
        'struct': '.struct.md',
        'enum': '.enum.md',
        'interface': '.interface.md',
        'trait': '.trait.md',
        'module': '.module.md',
        'package': '.package.md',
        'documentation': '.md'
    }
    
    file_extension = type_to_ext.get(element_type, '.md')
    
    # Erstelle den Dateinamen
    if custom_suffix:
        base_name = f"{element_name}_{custom_suffix}_{hash_value}"
    else:
        base_name = f"{element_name}_{hash_value}"
    
    return f"{base_name}{file_extension}"