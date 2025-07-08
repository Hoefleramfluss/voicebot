#!/bin/bash

# Öffne das Terminal-Fenster auf die richtige Umgebung
cd ~/Downloads

# Aktiviert das virtuelle Python-Environment
source susi-venv/bin/activate

# Installiert alle nötigen Pakete (macht nix, wenn sie schon da sind)
pip install --upgrade pip
pip install openai sounddevice soundfile scipy requests

# Starte den Susi-Voicebot (neues Fenster, damit du parallel arbeiten kannst)
echo "Starte Susi-Voicebot..."
python3 Susi_Voicebot.py &

# Warte kurz, damit der Bot startet
sleep 2

# Optional: Starte das Resmio-Testskript parallel (oder # davor für nur Bot)
echo "Starte Resmio-Testskript..."
python3 test_resmio.py &

echo ""
echo "Alle Komponenten laufen! Du kannst im Terminal die Ausgaben beobachten."
echo "Drück [ctrl]+[c] zum Beenden!"
read -n 1 -s -r -p "Taste drücken zum Schließen..."
