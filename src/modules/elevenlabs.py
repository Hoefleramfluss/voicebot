import os
import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Heroku: Schreibe TTS nach /tmp/static/tts
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
BASE_URL = os.getenv("BASE_URL")
if not BASE_URL:
    BASE_URL = "https://voicebot1-515ea4753341.herokuapp.com"
    logging.warning(f"[TTS] BASE_URL not gesetzt, benutze Default: {BASE_URL}")
STATIC_DIR = Path("/tmp/static")
TTS_DIR = STATIC_DIR / "tts"

def create_elevenlabs_response(text: str) -> str:
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
        TTS_DIR.mkdir(parents=True, exist_ok=True)
        filepath = TTS_DIR / filename
        try:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logging.info(f"[TTS] Audiofile erzeugt: {filepath}")
        except Exception as e:
            logging.error(f"[TTS] Fehler beim Speichern: {e}")
            return f"<Say language='de-AT'>{text}</Say>"
        audio_url = f"{BASE_URL}/static/tts/{filename}"
        logging.info(f"[TTS] Rückgabe für Twilio: {audio_url}")
        return f"<Play>{audio_url}</Play>"
    else:
        logging.error(f"[TTS] API-Fehler: {response.status_code} - {response.text}")
        return f"<Say language='de-AT'>{text}</Say>"
