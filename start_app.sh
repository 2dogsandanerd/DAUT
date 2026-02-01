#!/bin/bash
# Startskript für DAUT

echo "Starte DAUT Anwendung..."

# Wechsle zum Projektverzeichnis
cd /mnt/dev/eingang/doc_updater_app

# Aktiviere das Virtual Environment
source venv/bin/activate

# Starte die Streamlit-Anwendung
streamlit run src/ui/main.py