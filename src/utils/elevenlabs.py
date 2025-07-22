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
    if response.status_code == 200:
        # Speichere temporäre Datei und gib URL zurück (hier als Platzhalter)
        # In Produktion: Datei speichern und öffentlich verfügbar machen (z.B. S3, CDN)
        audio_url = f"https://voicebot-cdn.example.com/tts/{hash(text)}.mp3"
        # TODO: Audio-File speichern und bereitstellen
        return f'<Play>{audio_url}</Play>'
    else:
        # Fallback: Text als TwiML zurückgeben
        return f"<Say language='de-AT'>{text}</Say>"
