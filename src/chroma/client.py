import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import requests
import os
from pathlib import Path


class ChromaDBClient:
    def __init__(self, host: str = "localhost", port: int = 8000, timeout: int = 30, persist_directory: Optional[str] = None):
        """
        Initialisiert den ChromaDB Client mit dem offiziellen Python Client.

        Args:
            host: Hostname des ChromaDB Servers
            port: Port des ChromaDB Servers
            timeout: Timeout für Verbindungen
            persist_directory: Optionaler Pfad für persistente Speicherung (wenn lokal verwendet)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.persist_directory = persist_directory or "./chromadb_data"
        self.base_url = f"http://{host}:{port}/api/v2"

        # Versuche zuerst lokale persistente Speicherung, falls Host=localhost
        if host == "localhost" or host == "127.0.0.1":
            try:
                # Stelle sicher, dass das Persistenz-Verzeichnis existiert
                persist_path = Path(self.persist_directory)
                persist_path.mkdir(parents=True, exist_ok=True)

                # Versuche, einen PersistentClient zu erstellen
                self.client = chromadb.PersistentClient(
                    path=str(persist_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                print(f"✅ Verwende lokale persistente ChromaDB in: {self.persist_directory}")
            except Exception as e:
                print(f"⚠️ Lokale persistente ChromaDB nicht verfügbar: {e}, versuche HTTP-Verbindung...")
                self._try_http_connection()
        else:
            # Für entfernte Server verwende HTTP-Client
            self._try_http_connection()

    def _try_http_connection(self):
        """Versucht, eine Verbindung zu einem HTTP-ChromaDB-Server herzustellen"""
        try:
            response = requests.get(f"{self.base_url}/heartbeat", timeout=self.timeout)
            if response.status_code == 200:
                # Verwende den offiziellen ChromaDB HttpClient
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=Settings(
                        chroma_server_host=self.host,
                        chroma_server_http_port=self.port,
                        chroma_server_ssl_enabled=False
                    )
                )
                print(f"✅ Verbinde mit ChromaDB-Server unter: {self.host}:{self.port}")
            else:
                raise Exception(f"Unerwarteter Statuscode: {response.status_code}")
        except Exception as e:
            print(f"❌ Konnte nicht zum ChromaDB Server verbinden: {e}")
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
            # Für PersistentClient gibt es keine HTTP-Heartbeat-Prüfung
            # Stattdessen versuchen wir, eine einfache Operation auszuführen
            self.client.heartbeat()
            return True
        except:
            # Als Fallback versuchen wir die HTTP-Methode
            try:
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

    def list_collections(self):
        """Alias für get_collections - gibt alle vorhandenen Collections zurück"""
        return self.get_collections()

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

    def get_collection(self, collection_name: str):
        """Gibt eine Collection zurück oder None wenn sie nicht existiert"""
        try:
            if self.client is None:
                print("ChromaDB Client nicht initialisiert")
                return None

            collections = self.list_collections()
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                return None

            return self.client.get_collection(name=collection_name)
        except Exception as e:
            print(f"Fehler beim Abrufen der Collection '{collection_name}': {e}")
            return None

    def delete_collection(self, collection_name: str) -> bool:
        """Löscht eine Collection"""
        try:
            if self.client is None:
                print("ChromaDB Client nicht initialisiert")
                return False

            collections = self.list_collections()
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                print(f"Collection '{collection_name}' existiert nicht")
                return True

            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Fehler beim Löschen der Collection '{collection_name}': {e}")
            return False