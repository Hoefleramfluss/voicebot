import os
import requests
import logging
import pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

def create_elevenlabs_response(text: str) -> str:
    # …
    if response.status_code == 200:
        filename = f"tts_{abs(hash(text))}.mp3"
        tts_dir = BASE_DIR / 'static' / 'tts'
        tts_dir.mkdir(parents=True, exist_ok=True)
        filepath = tts_dir / filename

        with open(filepath, 'wb') as f:
            f.write(response.content)
        logging.info(f"[TTS] Audiofile erzeugt: {filepath}")

        audio_url = f"{BASE_URL}/static/tts/{filename}"
        logging.info(f"[TTS] Rückgabe für Twilio: {audio_url}")
        return f"<Play>{audio_url}</Play>"

logging.basicConfig(level=logging.INFO)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
BASE_URL = os.getenv("BASE_URL", "https://hoefler-voicebot.herokuapp.com")

def create_elevenlabs_response(text):
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
        tts_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/tts')
        os.makedirs(tts_dir, exist_ok=True)
        filepath = os.path.join(tts_dir, filename)

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

# Debug
if __name__ == "__main__":
    print(create_elevenlabs_response("Grüß dich, i bin da Toni vom Höfler!"))
