import streamlit as st
from typing import Dict, Any, List
from src.chroma.client import ChromaDBClient
from src.core.service_config import ServiceConfig





def display_chroma_status(service_config: ServiceConfig = None, chroma_client=None):
    """Zeigt den Status der ChromaDB-Verbindung an"""
    # Wenn kein Client übergeben wird, erstelle einen neuen
    if chroma_client is None:
        from src.core.service_config import ServiceConfig
        if service_config is None:
            service_config = ServiceConfig()
        chroma_client = ChromaDBClient(
            host=service_config.chroma_host,
            port=service_config.chroma_port,
            timeout=service_config.chroma_timeout,
            persist_directory=service_config.chroma_persist_directory
        )

    if chroma_client.health_check():
        st.success("✅ ChromaDB-Verbindung: Verfügbar")

        # Zeige Anzahl Collections
        collections = chroma_client.list_collections()
        st.metric("Anzahl Collections", len(collections) if collections else 0)
    else:
        st.error("❌ ChromaDB-Verbindung: Nicht verfügbar")
        st.info("Hinweis: Stellen Sie sicher, dass ChromaDB auf dem konfigurierten Host und Port läuft.")


def display_chroma_collection_management(service_config: ServiceConfig = None, chroma_client=None):
    """Zeigt eine UI-Komponente zur Verwaltung von ChromaDB Collections"""
    st.subheader("ChromaDB Collection-Verwaltung")

    # Wenn kein Client übergeben wird, erstelle einen neuen
    if chroma_client is None:
        from src.core.service_config import ServiceConfig
        if service_config is None:
            service_config = ServiceConfig()
        chroma_client = ChromaDBClient(
            host=service_config.chroma_host,
            port=service_config.chroma_port,
            timeout=service_config.chroma_timeout,
            persist_directory=service_config.chroma_persist_directory
        )

    # Prüfe Verbindung
    if not chroma_client.health_check():
        st.error("Keine Verbindung zu ChromaDB möglich. Bitte stellen Sie sicher, dass ChromaDB läuft.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Vorhandene Collections")

        # Liste vorhandener Collections
        collections = chroma_client.list_collections()

        if collections:
            for collection in collections:
                col_name = collection.name if hasattr(collection, 'name') else str(collection)
                col_items = collection.count() if hasattr(collection, 'count') else 'Unbekannt'

                col_disp1, col_disp2 = st.columns([3, 1])
                with col_disp1:
                    st.write(f"**{col_name}** ({col_items} Items)" if col_items != 'Unbekannt' else f"**{col_name}**")
                with col_disp2:
                    if st.button("🗑️ Löschen", key=f"del_{col_name}"):
                        if chroma_client.delete_collection(col_name):
                            st.success(f"Collection '{col_name}' erfolgreich gelöscht")
                            st.rerun()
                        else:
                            st.error(f"Fehler beim Löschen der Collection '{col_name}'")
        else:
            st.info("Keine Collections vorhanden")

    with col2:
        st.write("### Neue Collection erstellen")

        new_collection_name = st.text_input("Name der neuen Collection",
                                          placeholder="z.B. mein_projekt_code oder mein_projekt_docs")

        if st.button("Collection erstellen"):
            if new_collection_name:
                # Ersetze ungültige Zeichen im Collection-Namen (ChromaDB erlaubt nur bestimmte Zeichen)
                import re
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', new_collection_name)

                if chroma_client.create_collection(safe_name):
                    st.success(f"Collection '{safe_name}' erfolgreich erstellt")
                else:
                    st.error(f"Konnte Collection '{safe_name}' nicht erstellen")
            else:
                st.warning("Bitte geben Sie einen Namen für die Collection ein")

        st.write("### Collection Details")
        
        # Bereite Liste für Dropdown vor
        collection_names = []
        if collections:
            collection_names = [c.name if hasattr(c, 'name') else str(c) for c in collections]
            
        if collection_names:
            collection_detail_name = st.selectbox("Wähle Collection für Details", options=collection_names)
            
            if st.button("Details anzeigen"):
                if collection_detail_name:
                    col_obj = chroma_client.get_collection(collection_detail_name)
                    if col_obj:
                        # Konvertiere Collection-Objekt in ein Dictionary für st.json
                        details = {
                            "name": col_obj.name,
                            "id": str(col_obj.id),
                            "count": col_obj.count(),
                            "metadata": col_obj.metadata
                        }
                        st.json(details)
                    else:
                        st.error(f"Collection '{collection_detail_name}' nicht gefunden")
        else:
            st.info("Keine Collections verfügbar.")