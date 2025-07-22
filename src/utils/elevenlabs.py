import os
import requests

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Toni-Wrapper: Gibt eine TTS-Antwort von ElevenLabs zurück

def create_elevenlabs_response(text):
    """
    Wandelt den gegebenen Text in ein Audiofile um (Toni-Stimme, Niederösterreich),
    gibt TwiML <Play> Tag mit URL zur generierten Audiodatei zurück.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.8
        },
        "model_id": "eleven_multilingual_v2"
    }
    response = requests.post(url, json=payload, headers=headers)
    import logging
    if response.status_code == 200:
        filename = f"tts_{abs(hash(text))}.mp3"
        tts_dir = os.path.join(os.path.dirname(__file__), '../../static/tts')
        os.makedirs(tts_dir, exist_ok=True)
        filepath = os.path.join(tts_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logging.info(f"[TTS] Audiofile erzeugt: {filepath}")
        except Exception as e:
            logging.error(f"[TTS] Fehler beim Schreiben der Datei: {filepath} - {e}")
        # Baue die öffentliche URL (Heroku/Prod: /static/tts/...)
        audio_url = f"/static/tts/{filename}"
        logging.info(f"[TTS] Rückgabe-URL für Twilio: {audio_url}")
        return f'<Play>{audio_url}</Play>'
    else:
        logging.error(f"[TTS] ElevenLabs API-Fehler: {response.status_code} - {response.text}")
        # Fallback: Text als TwiML zurückgeben
        return f"<Say language='de-AT'>{text}</Say>"
