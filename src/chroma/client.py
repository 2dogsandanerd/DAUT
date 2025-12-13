from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

class ChromaDBClient:
    def __init__(self, host: str = "localhost", port: int = 8000, timeout: int = 30):
        """
        Initialisiert den ChromaDB Client mit dem offiziellen Python Client.

        Args:
            host: Hostname des ChromaDB Servers
            port: Port des ChromaDB Servers
            timeout: Timeout für Requests (wird derzeit nicht verwendet)
        """
        self.host = host
        self.port = port
        self.timeout = timeout

        # Verwende den offiziellen ChromaDB HttpClient
        try:
            self.client = chromadb.HttpClient(host=host, port=port)
        except Exception as e:
            print(f"Warnung: Konnte nicht zum ChromaDB Server verbinden: {e}")
            self.client = None

    def health_check(self) -> bool:
        """Prüft, ob der ChromaDB-Server erreichbar ist"""
        if not self.client:
            return False
        try:
            # Versuche, Collections aufzulisten als Health-Check
            self.client.heartbeat()
            return True
        except Exception as e:
            print(f"Health check fehlgeschlagen: {e}")
            return False

    def collection_exists(self, collection_name: str) -> bool:
        """Prüft, ob eine Collection bereits existiert"""
        if not self.client:
            return False
        try:
            collections = self.client.list_collections()
            return any(col.name == collection_name for col in collections)
        except Exception as e:
            print(f"Fehler beim Prüfen der Collection: {e}")
            return False

    def create_collection(self, collection_name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Erstellt eine neue Collection

        Args:
            collection_name: Name der Collection
            metadata: Optionale Metadaten für die Collection

        Returns:
            True wenn erfolgreich, False sonst
        """
        if not self.client:
            print("ChromaDB Client nicht initialisiert")
            return False

        # Prüfe zuerst, ob die Collection bereits existiert
        if self.collection_exists(collection_name):
            print(f"Collection '{collection_name}' existiert bereits")
            return True

        try:
            # Standardmäßig cosine similarity verwenden
            if metadata is None:
                metadata = {"hnsw:space": "cosine"}

            self.client.create_collection(
                name=collection_name,
                metadata=metadata
            )
            print(f"Collection '{collection_name}' erfolgreich erstellt")
            return True
        except Exception as e:
            print(f"Fehler beim Erstellen der Collection '{collection_name}': {e}")
            return False

    def get_collection(self, collection_name: str):
        """
        Ruft eine Collection ab

        Args:
            collection_name: Name der Collection

        Returns:
            Collection Objekt oder None
        """
        if not self.client:
            return None

        try:
            return self.client.get_collection(name=collection_name)
        except Exception as e:
            print(f"Collection '{collection_name}' existiert nicht oder Fehler: {e}")
            return None

    def add_embeddings(self, collection_name: str, embeddings: List[List[float]],
                      documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None,
                      ids: Optional[List[str]] = None) -> bool:
        """
        Fügt Embeddings zu einer Collection hinzu

        Args:
            collection_name: Name der Collection
            embeddings: Liste von Embedding-Vektoren
            documents: Liste von Dokumenten (Texten)
            metadatas: Optionale Liste von Metadaten
            ids: Optionale Liste von IDs (werden automatisch generiert wenn nicht angegeben)

        Returns:
            True wenn erfolgreich, False sonst
        """
        if not self.client:
            print("ChromaDB Client nicht initialisiert")
            return False

        try:
            # Prüfe, ob Collection existiert
            collection = self.get_collection(collection_name)
            if not collection:
                print(f"Collection '{collection_name}' existiert nicht. Erstelle sie zuerst...")
                if not self.create_collection(collection_name):
                    return False
                collection = self.get_collection(collection_name)

            # Generiere IDs wenn nicht angegeben
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]

            # Füge Embeddings hinzu
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ {len(embeddings)} Embeddings erfolgreich zur Collection '{collection_name}' hinzugefügt")
            return True
        except Exception as e:
            print(f"Fehler beim Hinzufügen der Embeddings: {e}")
            return False

    def query_collection(self, collection_name: str, query_embeddings: Optional[List[List[float]]] = None,
                        query_texts: Optional[List[str]] = None, n_results: int = 10,
                        auto_create: bool = True, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Führt eine Abfrage in der Collection durch

        Args:
            collection_name: Name der Collection
            query_embeddings: Embedding-Vektoren für die Abfrage
            query_texts: Texte für die Abfrage (wenn keine Embeddings angegeben)
            query: DEPRECATED - Verwende query_texts stattdessen (für Rückwärtskompatibilität)
            n_results: Anzahl der Ergebnisse
            auto_create: Collection erstellen falls sie nicht existiert

        Returns:
            Dictionary mit Ergebnissen oder leeres Dict bei Fehler
        """
        # Rückwärtskompatibilität: query -> query_texts
        if query is not None and query_texts is None:
            query_texts = [query] if isinstance(query, str) else query

        if not self.client:
            print("ChromaDB Client nicht initialisiert")
            return {}

        try:
            # Prüfe, ob Collection existiert
            collection = self.get_collection(collection_name)
            if not collection:
                if auto_create:
                    print(f"Collection '{collection_name}' existiert nicht, wird erstellt...")
                    if self.create_collection(collection_name):
                        collection = self.get_collection(collection_name)
                        print(f"Collection '{collection_name}' erfolgreich erstellt für Abfrage.")
                    else:
                        print(f"Konnte Collection '{collection_name}' nicht erstellen.")
                        return {}
                else:
                    print(f"Collection '{collection_name}' existiert nicht.")
                    return {}

            # Führe Query aus
            results = collection.query(
                query_embeddings=query_embeddings,
                query_texts=query_texts,
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"Fehler bei der Abfrage: {e}")
            return {}

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        Listet alle Collections auf

        Returns:
            Liste von Dictionaries mit Collection-Informationen
        """
        if not self.client:
            print("ChromaDB Client nicht initialisiert")
            return []

        try:
            collections = self.client.list_collections()
            # Konvertiere zu Dictionary-Format für Kompatibilität
            return [{"name": col.name, "metadata": col.metadata} for col in collections]
        except Exception as e:
            print(f"Fehler bei der Auflistung der Collections: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """
        Löscht eine Collection

        Args:
            collection_name: Name der Collection

        Returns:
            True wenn erfolgreich, False sonst
        """
        if not self.client:
            print("ChromaDB Client nicht initialisiert")
            return False

        try:
            self.client.delete_collection(name=collection_name)
            print(f"Collection '{collection_name}' erfolgreich gelöscht")
            return True
        except Exception as e:
            print(f"Fehler beim Löschen der Collection '{collection_name}': {e}")
            return False
