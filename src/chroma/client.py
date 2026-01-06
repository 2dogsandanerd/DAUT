import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import requests


class ChromaDBClient:
    def __init__(self, host: str = "localhost", port: int = 8000, timeout: int = 30):
        """
        Initialisiert den ChromaDB Client mit dem offiziellen Python Client.

        Args:
            host: Hostname des ChromaDB Servers
            port: Port des ChromaDB Servers
            timeout: Timeout für Verbindungen
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/api/v2"

        try:
            # Versuche, die Verbindung über HTTP zu testen
            response = requests.get(f"{self.base_url}/heartbeat", timeout=timeout)
            if response.status_code == 200:
                # Verwende den offiziellen ChromaDB HttpClient
                self.client = chromadb.HttpClient(
                    host=host,
                    port=port,
                    settings=Settings(
                        chroma_server_host=host,
                        chroma_server_http_port=port,
                        chroma_server_ssl_enabled=False
                    )
                )
            else:
                raise Exception(f"Unerwarteter Statuscode: {response.status_code}")
        except Exception as e:
            print(f"Warnung: Konnte nicht zum ChromaDB Server verbinden: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Prüft, ob der ChromaDB-Server erreichbar ist"""
        if self.client is None:
            return False
        try:
            self.client.heartbeat()
            return True
        except:
            return False

    def health_check(self) -> bool:
        """Überprüft den Gesundheitsstatus des ChromaDB-Servers"""
        if self.client is None:
            return False
        try:
            # Nutze die direkte HTTP-Anfrage anstatt des Clients
            response = requests.get(f"{self.base_url}/heartbeat", timeout=self.timeout)
            return response.status_code == 200
        except:
            return False

    def get_or_create_collection(self, collection_name: str):
        """Holt oder erstellt eine Collection"""
        if self.client is None:
            print("ChromaDB Client nicht initialisiert")
            return None
        try:
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Empfohlen für Embeddings
            )
        except Exception as e:
            print(f"Fehler beim Erstellen oder Abrufen der Collection '{collection_name}': {e}")
            return None

    def add_documents(self, collection_name: str, documents: List[str], metadatas: List[Dict] = None, ids: List[str] = None):
        """Fügt Dokumente zu einer Collection hinzu"""
        collection = self.get_or_create_collection(collection_name)
        if collection is None:
            return

        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Fehler beim Hinzufügen von Dokumenten zur Collection '{collection_name}': {e}")

    def add_embeddings(self, collection_name: str, embeddings: List[List[float]],
                      documents: List[str] = None, metadatas: List[Dict] = None,
                      ids: List[str] = None):
        """Fügt Embeddings zu einer Collection hinzu"""
        collection = self.get_or_create_collection(collection_name)
        if collection is None:
            print(f"Konnte Collection '{collection_name}' nicht erstellen/abrufen")
            return False

        if ids is None:
            ids = [f"emb_{i}" for i in range(len(embeddings))]

        try:
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Fehler beim Hinzufügen von Embeddings zur Collection '{collection_name}': {e}")
            return False

    def create_collection(self, collection_name: str) -> bool:
        """Erstellt eine neue Collection"""
        try:
            collection = self.client.create_collection(name=collection_name)
            return collection is not None
        except Exception as e:
            if "already exists" in str(e).lower():
                # Wenn die Collection bereits existiert, ist das kein Fehler
                return True
            print(f"Fehler beim Erstellen der Collection '{collection_name}': {e}")
            return False

    def query(self, collection_name: str, query_text: str, n_results: int = 5):
        """Sucht in einer Collection"""
        collection = self.get_or_create_collection(collection_name)
        if collection is None:
            return None
            
        try:
            return collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
        except Exception as e:
            print(f"Fehler bei der Abfrage der Collection '{collection_name}': {e}")
            return None

    def get_collections(self):
        """Gibt alle vorhandenen Collections zurück"""
        if self.client is None:
            print("ChromaDB Client nicht initialisiert")
            return []
        try:
            return self.client.list_collections()
        except Exception as e:
            print(f"Fehler beim Abrufen der Collections: {e}")
            return []

    def get_collection_stats(self, collection_name: str):
        """Gibt Statistiken zu einer spezifischen Collection zurück"""
        collection = self.get_or_create_collection(collection_name)
        if collection is None:
            return None
        try:
            return collection.count()
        except Exception as e:
            print(f"Fehler beim Abrufen der Collection-Statistik: {e}")
            return None