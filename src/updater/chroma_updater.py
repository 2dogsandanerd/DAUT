from pathlib import Path
from typing import List, Dict, Any, Optional
from src.models.element import CodeElement, DocElement
from src.chroma.client import ChromaDBClient
from src.core.service_config import ServiceConfig
from src.integration.smart_chroma_ingestor import SmartChromaIngestor

class ChromaUpdater:
    def __init__(self, service_config: ServiceConfig):
        self.service_config = service_config
        self.chroma_client = ChromaDBClient(
            host=service_config.chroma_host,
            port=service_config.chroma_port,
            timeout=service_config.chroma_timeout,
            persist_directory=service_config.chroma_persist_directory
        )
        # Initialize Ollama Client for embeddings
        # We need check if we can import it, avoiding circular imports if any
        from src.llm.client import OllamaClient
        self.embedding_model = service_config.embedding_model
        self.ollama_client = OllamaClient(host=service_config.ollama_host if hasattr(service_config, 'ollama_host') else "http://localhost:11434")

    def update_chroma_with_elements(self, code_elements: List[CodeElement],
                                  doc_elements: List[DocElement],
                                  project_path: str) -> bool:
        """
        Aktualisiert die ChromaDB mit den aktuellen Code- und Dokumentationselementen
        """
        try:
            # Verwende den SmartChromaIngestor für intelligente Verarbeitung
            smart_ingestor = SmartChromaIngestor(self.service_config)

            # Verarbeite alle Elemente intelligent
            success = True

            # Verarbeite Code-Elemente
            print("Intelligente Verarbeitung von Code-Elementen...")
            for elem in code_elements:
                # Erstelle temporäre Datei für das Code-Element, um den SmartIngestor nutzen zu können
                # Alternativ: Erweitere den SmartIngestor, um direkt mit CodeElementen zu arbeiten
                try:
                    # Erstelle Embeddings für Code-Elemente mit intelligenter Verarbeitung
                    embedding_data = self._create_embedding_data_for_code(elem, project_path)
                    if embedding_data:
                        # Bestimme Collection-Namen basierend auf Projektname
                        project_name = Path(project_path).name
                        collection_name = f"{project_name}_code"

                        # Füge zu ChromaDB hinzu
                        if not self.chroma_client.create_collection(collection_name):
                            print(f"Konnte Collection '{collection_name}' nicht erstellen.")
                            success = False
                        else:
                            # Erstelle Collection und füge hinzu
                            collection = self.chroma_client.get_or_create_collection(collection_name)
                            if collection:
                                import hashlib
                                content_hash = hashlib.md5(embedding_data['content'].encode()).hexdigest()
                                doc_id = f"code_{elem.name}_{content_hash}"

                                collection.add(
                                    embeddings=[embedding_data.get('embedding', [0.0])],
                                    documents=[embedding_data.get('content', '')],
                                    metadatas=[embedding_data.get('metadata', {})],
                                    ids=[doc_id]
                                )
                            else:
                                success = False
                except Exception as e:
                    print(f"Fehler bei der Verarbeitung von Code-Element {elem.name}: {e}")
                    success = False

            # Verarbeite Dokumentations-Elemente
            print("Intelligente Verarbeitung von Dokumentations-Elementen...")
            for elem in doc_elements:
                try:
                    # Erstelle Embeddings für Dokumentations-Elemente mit intelligenter Verarbeitung
                    embedding_data = self._create_embedding_data_for_doc(elem, project_path)
                    if embedding_data:
                        # Bestimme Collection-Namen basierend auf Projektname
                        project_name = Path(project_path).name
                        collection_name = f"{project_name}_docs"

                        # Füge zu ChromaDB hinzu
                        if not self.chroma_client.create_collection(collection_name):
                            print(f"Konnte Collection '{collection_name}' nicht erstellen.")
                            success = False
                        else:
                            # Erstelle Collection und füge hinzu
                            collection = self.chroma_client.get_or_create_collection(collection_name)
                            if collection:
                                import hashlib
                                content_hash = hashlib.md5(embedding_data['content'].encode()).hexdigest()
                                doc_id = f"doc_{elem.name}_{content_hash}"

                                collection.add(
                                    embeddings=[embedding_data.get('embedding', [0.0])],
                                    documents=[embedding_data.get('content', '')],
                                    metadatas=[embedding_data.get('metadata', {})],
                                    ids=[doc_id]
                                )
                            else:
                                success = False
                except Exception as e:
                    print(f"Fehler bei der Verarbeitung von Dokumentations-Element {elem.name}: {e}")
                    success = False

            print("ChromaDB erfolgreich aktualisiert")
            return success

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
            # Bevorzuge full_content für das Embedding, falls verfügbar (damit nicht nur die Vorschau embeddet wird)
            text_to_embed = doc_elem.full_content if doc_elem.full_content else doc_elem.content
            
            content = f"Name: {doc_elem.name}\nTyp: {doc_elem.type.value}\nInhalt: {text_to_embed}"

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