"""
Integration des Smart-Ingest-Kits mit der ChromaDB-Integration
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.chroma.client import ChromaDBClient
from src.smart_ingestor import SmartDoclingLoader, IngestHeuristics
from src.llm.client import OllamaClient
from src.core.service_config import ServiceConfig
import numpy as np


class SmartChromaIngestor:
    """
    Integriert das Smart-Ingest-Kit mit ChromaDB für intelligente Datentyp-spezifische Verarbeitung
    """
    
    def __init__(self, service_config: ServiceConfig):
        self.service_config = service_config
        self.chroma_client = ChromaDBClient(
            host=service_config.chroma_host,
            port=service_config.chroma_port,
            timeout=service_config.chroma_timeout,
            persist_directory=service_config.chroma_persist_directory
        )
        self.ollama_client = OllamaClient(host=service_config.ollama_host)
        self.heuristics = IngestHeuristics()
    
    def process_and_store_file(self, file_path: str, project_path: str) -> bool:
        """
        Verarbeitet eine Datei intelligent und speichert sie in der entsprechenden ChromaDB-Collection
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Bestimme den Dateityp und lade die Datei intelligent
            if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs']:
                # Behandle als Code-Datei
                return self._process_code_file(file_path, project_path)
            elif file_ext in ['.md', '.txt', '.rst']:
                # Behandle als Dokumentationsdatei
                return self._process_documentation_file(file_path, project_path)
            elif file_ext in ['.pdf', '.docx', '.html']:
                # Verwende SmartDoclingLoader für komplexe Dokumente
                return self._process_complex_document(file_path, project_path)
            else:
                # Standardverarbeitung für andere Dateitypen
                return self._process_generic_file(file_path, project_path)
                
        except Exception as e:
            print(f"Fehler bei der Verarbeitung von {file_path}: {e}")
            return False
    
    def _process_code_file(self, file_path: str, project_path: str) -> bool:
        """
        Verarbeitet Code-Dateien mit speziellen Code-Embedding-Heuristiken
        """
        try:
            # Lade die Datei und extrahiere Code-Elemente (diese Logik würde aus dem Scanner kommen)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Bestimme Projektname für Collection-Namen
            project_name = Path(project_path).name
            collection_name = f"{project_name}_code"
            
            # Hole die optimalen Einstellungen für Code
            config = self.heuristics.code
            
            # Erstelle Embeddings für den Code
            embedding_data = self._create_code_embedding_data(content, file_path, config)
            
            if embedding_data:
                # Füge zu ChromaDB hinzu
                return self._add_to_chroma(collection_name, embedding_data)
            
            return False
        except Exception as e:
            print(f"Fehler bei der Verarbeitung der Code-Datei {file_path}: {e}")
            return False
    
    def _process_documentation_file(self, file_path: str, project_path: str) -> bool:
        """
        Verarbeitet Dokumentationsdateien mit speziellen Text-Embedding-Heuristiken
        """
        try:
            # Lade die Dokumentationsdatei
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Bestimme Projektname für Collection-Namen
            project_name = Path(project_path).name
            collection_name = f"{project_name}_docs"
            
            # Hole die optimalen Einstellungen für Markdown/Text
            config = self.heuristics.markdown
            
            # Erstelle Embeddings für die Dokumentation
            embedding_data = self._create_documentation_embedding_data(content, file_path, config)
            
            if embedding_data:
                # Füge zu ChromaDB hinzu
                return self._add_to_chroma(collection_name, embedding_data)
            
            return False
        except Exception as e:
            print(f"Fehler bei der Verarbeitung der Dokumentations-Datei {file_path}: {e}")
            return False
    
    def _process_complex_document(self, file_path: str, project_path: str) -> bool:
        """
        Verwendet SmartDoclingLoader für komplexe Dokumente wie PDF, DOCX, etc.
        """
        try:
            # Verwende den SmartDoclingLoader
            loader = SmartDoclingLoader(file_path)
            docs = loader.load()
            
            if not docs:
                print(f"Keine Dokumente geladen aus {file_path}")
                return False
            
            # Bestimme Projektname für Collection-Namen
            project_name = Path(project_path).name
            collection_name = f"{project_name}_docs"
            
            success = True
            for doc in docs:
                # Erstelle Embeddings für das geladene Dokument
                embedding_data = self._create_documentation_embedding_data(
                    doc.text, 
                    file_path, 
                    IngestHeuristics.get_config_for_file(file_path)
                )
                
                if embedding_data:
                    # Füge zu ChromaDB hinzu
                    if not self._add_to_chroma(collection_name, embedding_data):
                        success = False
                else:
                    success = False
            
            return success
        except Exception as e:
            print(f"Fehler bei der Verarbeitung des komplexen Dokuments {file_path}: {e}")
            return False
    
    def _process_generic_file(self, file_path: str, project_path: str) -> bool:
        """
        Standardverarbeitung für andere Dateitypen
        """
        try:
            # Lade die Datei
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Bestimme Projektname für Collection-Namen
            project_name = Path(project_path).name
            collection_name = f"{project_name}_docs"
            
            # Hole die Standard-Einstellungen
            config = self.heuristics.default
            
            # Erstelle Embeddings für die Datei
            embedding_data = self._create_documentation_embedding_data(content, file_path, config)
            
            if embedding_data:
                # Füge zu ChromaDB hinzu
                return self._add_to_chroma(collection_name, embedding_data)
            
            return False
        except Exception as e:
            print(f"Fehler bei der Verarbeitung der generischen Datei {file_path}: {e}")
            return False
    
    def _create_code_embedding_data(self, content: str, file_path: str, config: Any) -> Optional[Dict[str, Any]]:
        """
        Erstellt Embedding-Daten für Code-Dateien mit speziellen Heuristiken
        """
        try:
            # Erstelle Inhalt für das Code-Element
            content_parts = [
                f"Dateipfad: {file_path}",
                f"Inhalt: {content}"
            ]
            
            full_content = "\n".join(content_parts)
            
            # Generiere Embedding mit dem konfigurierten Modell
            embedding = self.ollama_client.create_embedding(
                self.service_config.embedding_model, 
                full_content
            )
            
            if not embedding:
                print(f"Warnung: Konnte kein Embedding generieren für {file_path}. Verwende Placeholder.")
                # Verwende ein Standard-Embedding mit der korrekten Dimension
                embedding = [0.0] * 384  # Oder welche Dimension das Modell erwartet
            
            metadata = {
                'file_path': file_path,
                'file_type': 'code',
                'chunk_size': config.chunk_size,
                'overlap': config.overlap,
                'splitter_type': config.splitter_type,
                'project_path': str(Path(file_path).parent)
            }
            
            return {
                'content': full_content,
                'metadata': metadata,
                'embedding': embedding
            }
        except Exception as e:
            print(f"Fehler bei der Erstellung von Code-Embedding-Daten: {e}")
            return None
    
    def _create_documentation_embedding_data(self, content: str, file_path: str, config: Any) -> Optional[Dict[str, Any]]:
        """
        Erstellt Embedding-Daten für Dokumentations-Dateien mit speziellen Heuristiken
        """
        try:
            # Erstelle Inhalt für das Dokumentations-Element
            content_parts = [
                f"Dateipfad: {file_path}",
                f"Inhalt: {content}"
            ]
            
            full_content = "\n".join(content_parts)
            
            # Generiere Embedding mit dem konfigurierten Modell
            embedding = self.ollama_client.create_embedding(
                self.service_config.embedding_model, 
                full_content
            )
            
            if not embedding:
                print(f"Warnung: Konnte kein Embedding generieren für {file_path}. Verwende Placeholder.")
                # Verwende ein Standard-Embedding mit der korrekten Dimension
                embedding = [0.0] * 384  # Oder welche Dimension das Modell erwartet
            
            metadata = {
                'file_path': file_path,
                'file_type': 'documentation',
                'chunk_size': config.chunk_size,
                'overlap': config.overlap,
                'splitter_type': config.splitter_type,
                'project_path': str(Path(file_path).parent)
            }
            
            return {
                'content': full_content,
                'metadata': metadata,
                'embedding': embedding
            }
        except Exception as e:
            print(f"Fehler bei der Erstellung von Dokumentations-Embedding-Daten: {e}")
            return None
    
    def _add_to_chroma(self, collection_name: str, embedding_data: Dict[str, Any]) -> bool:
        """
        Fügt Embedding-Daten zur ChromaDB hinzu
        """
        try:
            # Erstelle oder hole die Collection
            collection = self.chroma_client.get_or_create_collection(collection_name)
            if collection is None:
                print(f"Konnte Collection '{collection_name}' nicht erstellen/abrufen")
                return False
            
            # Erstelle eine eindeutige ID für das Dokument
            import hashlib
            content_hash = hashlib.md5(embedding_data['content'].encode()).hexdigest()
            doc_id = f"{collection_name}_{content_hash}"
            
            # Füge das Dokument zur Collection hinzu
            collection.add(
                embeddings=[embedding_data['embedding']],
                documents=[embedding_data['content']],
                metadatas=[embedding_data['metadata']],
                ids=[doc_id]
            )
            
            return True
        except Exception as e:
            print(f"Fehler beim Hinzufügen zu ChromaDB Collection '{collection_name}': {e}")
            return False
    
    def process_project_directory(self, project_path: str) -> Dict[str, Any]:
        """
        Verarbeitet ein komplettes Projektverzeichnis intelligent
        """
        project_path = Path(project_path)
        results = {
            'processed_files': [],
            'failed_files': [],
            'collections_created': set()
        }
        
        # Durchlaufe alle relevanten Dateien im Projekt
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                # Prüfe Dateiendung
                file_ext = file_path.suffix.lower()
                
                # Überspringe bestimmte Dateitypen
                if file_ext in ['.pyc', '.pyo', '.log', '.tmp', '.bak', '.git', '.venv', 'venv']:
                    continue
                
                # Verarbeite die Datei
                if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.md', '.txt', '.rst', '.pdf', '.docx', '.html']:
                    success = self.process_and_store_file(str(file_path), str(project_path))
                    
                    if success:
                        results['processed_files'].append(str(file_path))
                        # Füge Collection-Namen zu den erstellten hinzu
                        project_name = project_path.name
                        if file_ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs']:
                            results['collections_created'].add(f"{project_name}_code")
                        else:
                            results['collections_created'].add(f"{project_name}_docs")
                    else:
                        results['failed_files'].append(str(file_path))
        
        return results