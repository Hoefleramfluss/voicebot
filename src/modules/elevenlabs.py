# src/utils/elevenlabs.py

import os
import requests
import logging
from pathlib import Path
from fastapi import Request

logging.basicConfig(level=logging.INFO)

# Projekt‐Root (drei Ebenen über utils → /app)
BASE_DIR = Path(__file__).resolve().parents[3]

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def create_elevenlabs_response(text: str, request: Request) -> str:
    """
    Erzeugt eine MP3 via ElevenLabs, speichert sie unter /static/tts
    und liefert ein TwiML-<Play>-Element zurück.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        filename = f"tts_{abs(hash(text))}.mp3"
        tts_dir = BASE_DIR / "static" / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        filepath = tts_dir / filename

        try:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logging.info(f"[TTS] Audiofile erzeugt: {filepath}")
        except Exception as e:
            logging.error(f"[TTS] Fehler beim Speichern: {e}")
            return f"<Say language='de-AT'>{text}</Say>"

        # absolute URL basierend auf FastAPI-Mount
        audio_url = request.url_for("static", path=f"tts/{filename}")
        logging.info(f"[TTS] Rückgabe für Twilio: {audio_url}")
        return f"<Play>{audio_url}</Play>"

    logging.error(f"[TTS] API-Fehler: {response.status_code} - {response.text}")
    return f"<Say language='de-AT'>{text}</Say>"
