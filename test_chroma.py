#!/usr/bin/env python3
"""
Testskript, um die ChromaDB-Verbindung und die Collections zu überprüfen
"""
import sys
import os

# Füge den src-Ordner zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.chroma.client import ChromaDBClient
from src.core.service_config import ServiceConfig

def test_chroma_connection():
    """Testet die Verbindung zur ChromaDB und zeigt Collections an"""
    print("Teste ChromaDB-Verbindung...")
    
    # Verwende die Standard-Service-Konfiguration
    config = ServiceConfig()
    
    # Initialisiere den ChromaDB-Client
    chroma_client = ChromaDBClient(
        host=config.chroma_host,
        port=config.chroma_port,
        timeout=config.chroma_timeout
    )
    
    # Überprüfe Verbindung
    print(f"Versuche, mit ChromaDB zu verbinden unter {config.chroma_host}:{config.chroma_port}...")
    
    if chroma_client.health_check():
        print("✓ ChromaDB-Verbindung erfolgreich hergestellt")
    else:
        print("✗ Keine Verbindung zur ChromaDB möglich")
        return False
    
    # Liste alle Collections auf
    try:
        collections = chroma_client.client.list_collections()
        print(f"\nVorhandene Collections: {len(collections)}")
        for col in collections:
            count = col.count() if hasattr(col, 'count') else 'N/A'
            print(f"- {col.name}: {count} Datensätze")
    except Exception as e:
        print(f"Fehler beim Abrufen der Collections: {e}")
    
    # Erstelle eine Test-Collection
    print(f"\nErstelle Test-Collection 'test_collection'...")
    success = chroma_client.create_collection('test_collection')
    if success:
        print("✓ Test-Collection erfolgreich erstellt oder bereits vorhanden")
        
        # Füge ein Test-Dokument hinzu
        print("Füge Test-Dokument hinzu...")
        try:
            test_collection = chroma_client.get_or_create_collection('test_collection')
            test_collection.add(
                embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]],  # Beispiel-Embedding
                documents=["Dies ist ein Testdokument"],
                metadatas=[{"test": "data", "source": "test_script"}],
                ids=["test_id_1"]
            )
            print("✓ Test-Dokument erfolgreich hinzugefügt")
            
            # Überprüfe den Inhalt der Collection
            count = test_collection.count()
            print(f"Anzahl Dokumente in 'test_collection': {count}")
            
        except Exception as e:
            print(f"✗ Fehler beim Hinzufügen des Test-Dokuments: {e}")
    else:
        print("✗ Fehler beim Erstellen der Test-Collection")
    
    return True

if __name__ == "__main__":
    test_chroma_connection()