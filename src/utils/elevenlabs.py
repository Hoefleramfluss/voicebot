import os
import requests
import logging
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)

# Projekt‑Root (zwei Ebenen über src/modules)
BASE_DIR = Path(__file__).resolve().parents[2]

# ENV‑Variablen
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
BASE_URL = os.getenv("BASE_URL", "https://hoefler-voicebot.herokuapp.com")

def create_elevenlabs_response(text: str) -> str:
    """
    Erzeugt eine MP3 via ElevenLabs und liefert ein TwiML <Play>-Element zurück.
    Speichert die Datei in /app/static/tts.
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

    # API‑Request
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        # Datei unter /app/static/tts speichern
        filename = f"tts_{abs(hash(text))}.mp3"
        tts_dir = BASE_DIR / 'static' / 'tts'
        tts_dir.mkdir(parents=True, exist_ok=True)
        filepath = tts_dir / filename

        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            logging.info(f"[TTS] Audiofile erzeugt: {filepath}")
        except Exception as e:
            logging.error(f"[TTS] Fehler beim Speichern: {e}")
            # Fallback auf Twilio‑TTS
            return f"<Say language='de-AT'>{text}</Say>"

        # Öffentlich abrufbare URL
        audio_url = f"{BASE_URL}/static/tts/{filename}"
        logging.info(f"[TTS] Rückgabe für Twilio: {audio_url}")
        return f"<Play>{audio_url}</Play>"

    else:
        logging.error(f"[TTS] API-Fehler: {response.status_code} - {response.text}")
        return f"<Say language='de-AT'>{text}</Say>"

# Debug‑Aufruf
if __name__ == "__main__":
    print(create_elevenlabs_response("Grüß dich, i bin da Toni vom Höfler!"))

