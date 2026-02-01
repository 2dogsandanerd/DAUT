#!/bin/bash
# Skript zur Installation der Abhängigkeiten für DAUT

echo "Installiere DAUT Abhängigkeiten..."

# Wechsle zum Projektverzeichnis
cd /mnt/dev/eingang/doc_updater_app

# Aktiviere das Virtual Environment
source venv/bin/activate

# Installiere die Abhängigkeiten
pip install -r requirements.txt

echo "Abhängigkeiten wurden installiert!"
echo "Du kannst jetzt die Anwendung starten mit:"
echo "  source venv/bin/activate"
echo "  streamlit run src/ui/main.py"