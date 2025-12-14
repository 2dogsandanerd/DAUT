from pathlib import Path
from typing import List, Dict, Any, Optional
from src.models.element import CodeElement, DocElement
from src.chroma.client import ChromaDBClient
from src.core.service_config import ServiceConfig

class ChromaUpdater:
    def __init__(self, service_config: ServiceConfig):
        self.chroma_client = ChromaDBClient(
            host=service_config.chroma_host,
            port=service_config.chroma_port,
            timeout=service_config.chroma_timeout
        )
        # Initialize Ollama Client for embeddings
        # We need check if we can import it, avoiding circular imports if any
        from src.llm.client import OllamaClient
        # Default embedding model - can be made configurable
        self.embedding_model = "nomic-embed-text" 
        self.ollama_client = OllamaClient(host=service_config.ollama_host if hasattr(service_config, 'ollama_host') else "http://localhost:11434")

    def update_chroma_with_elements(self, code_elements: List[CodeElement], 
                                  doc_elements: List[DocElement], 
                                  project_path: str) -> bool:
        """
        Aktualisiert die ChromaDB mit den aktuellen Code- und Dokumentationselementen
        """
        try:
            # Prüfe Verbindung zu ChromaDB
            if not self.chroma_client.health_check():
                print("ChromaDB ist nicht erreichbar")
                return False

            print("Aktualisiere ChromaDB mit Code-Elementen...")
            # Bestimme Collection-Namen basierend auf Projektname
            project_name = Path(project_path).name
            collection_name = f"{project_name}_code"

            # Erstelle Collection, falls sie nicht existiert
            if not self.chroma_client.create_collection(collection_name):
                print(f"Konnte Collection '{collection_name}' nicht erstellen. Überspringe Code-Elemente.")
            else:
                # Füge Code-Elemente hinzu
                for elem in code_elements:
                    # Erstelle Embeddings für Code-Elemente
                    embedding_data = self._create_embedding_data_for_code(elem, project_path)
                    if embedding_data:
                        # Konvertiere zu dem Format, das die API erwartet
                        embeddings_formatted = [{
                            "ids": [f"code_{elem.name}_{elem.file_path}"],
                            "embeddings": [embedding_data.get('embedding', [0.0])],  # Placeholder für echte Embeddings
                            "metadatas": [embedding_data.get('metadata', {})],
                            "documents": [embedding_data.get('content', '')]
                        }]

                        for emb in embeddings_formatted:
                            self.chroma_client.add_embeddings(
                                collection_name=collection_name,
                                embeddings=emb['embeddings'],
                                documents=emb['documents'],
                                metadatas=emb['metadatas'],
                                ids=emb['ids']
                            )

            print("Aktualisiere ChromaDB mit Dokumentations-Elementen...")
            # Bestimme Collection-Namen basierend auf Projektname
            project_name = Path(project_path).name
            collection_name = f"{project_name}_docs"

            # Erstelle Collection, falls sie nicht existiert
            if not self.chroma_client.create_collection(collection_name):
                print(f"Konnte Collection '{collection_name}' nicht erstellen. Überspringe Dokumentations-Elemente.")
            else:
                # Füge Dokumentations-Elemente hinzu
                for elem in doc_elements:
                    # Erstelle Embeddings für Dokumentations-Elemente
                    embedding_data = self._create_embedding_data_for_doc(elem, project_path)
                    if embedding_data:
                        # Konvertiere zu dem Format, das die API erwartet
                        embeddings_formatted = [{
                            "ids": [f"doc_{elem.name}"],
                            "embeddings": [embedding_data.get('embedding', [0.0])],  # Placeholder für echte Embeddings
                            "metadatas": [embedding_data.get('metadata', {})],
                            "documents": [embedding_data.get('content', '')]
                        }]

                        for emb in embeddings_formatted:
                            self.chroma_client.add_embeddings(
                                collection_name=collection_name,
                                embeddings=emb['embeddings'],
                                documents=emb['documents'],
                                metadatas=emb['metadatas'],
                                ids=emb['ids']
                            )

            print("ChromaDB erfolgreich aktualisiert")
            return True

        except Exception as e:
            print(f"Fehler bei der Aktualisierung der ChromaDB: {e}")
            return False

    def _create_embedding_data_for_code(self, code_elem: CodeElement, project_path: str) -> Optional[Dict[str, Any]]:
        """Erstellt Embedding-Daten für ein Code-Element"""
        try:
            # Erstelle Inhalt für das Code-Element
            content_parts = []
            if code_elem.name:
                content_parts.append(f"Name: {code_elem.name}")
            if code_elem.type:
                content_parts.append(f"Typ: {code_elem.type.value}")
            if code_elem.signature:
                content_parts.append(f"Signatur: {code_elem.signature}")
            if code_elem.parameters:
                content_parts.append(f"Parameter: {', '.join([str(p) for p in code_elem.parameters])}")
            if code_elem.docstring:
                content_parts.append(f"Docstring: {code_elem.docstring}")
            if code_elem.code_snippet:
                content_parts.append(f"Code: {code_elem.code_snippet}")

            content = "\n".join(content_parts)

            metadata = {
                'name': code_elem.name,
                'type': code_elem.type.value if code_elem.type else '',
                'file_path': code_elem.file_path,
                'signature': code_elem.signature or '',
                'line_number': code_elem.line_number,
                'project_path': project_path
            }

            # Embeddings generieren
            embedding = self.ollama_client.create_embedding(self.embedding_model, content)
            
            if not embedding:
                print(f"Warnung: Konnte kein Embedding generieren für {code_elem.name}. Verwende Placeholder.")
                embedding = [0.0] * 384
                
            return {
                'content': content,
                'metadata': metadata,
                'embedding': embedding
            }
        except Exception as e:
            print(f"Fehler bei der Erstellung von Embedding-Daten für Code-Element: {e}")
            return None

    def _create_embedding_data_for_doc(self, doc_elem: DocElement, project_path: str) -> Optional[Dict[str, Any]]:
        """Erstellt Embedding-Daten für ein Dokumentations-Element"""
        try:
            # Erstelle Inhalt für das Dokumentations-Element
            content = f"Name: {doc_elem.name}\nTyp: {doc_elem.type.value}\nInhalt: {doc_elem.content}"

            metadata = {
                'name': doc_elem.name,
                'type': doc_elem.type.value if doc_elem.type else '',
                'file_path': doc_elem.file_path,
                'format': doc_elem.format,
                'project_path': project_path
            }

            # Embeddings generieren
            embedding = self.ollama_client.create_embedding(self.embedding_model, content)
            
            if not embedding:
                print(f"Warnung: Konnte kein Embedding generieren für {doc_elem.name}. Verwende Placeholder.")
                embedding = [0.0] * 384

            return {
                'content': content,
                'metadata': metadata,
                'embedding': embedding
            }
        except Exception as e:
            print(f"Fehler bei der Erstellung von Embedding-Daten für Dokumentations-Element: {e}")
            return None