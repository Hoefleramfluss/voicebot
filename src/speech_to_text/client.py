# src/speech_to_text/client.py

import os
from google.cloud import speech_v1p1beta1 as speech
# <<< richtiger Pfad zum Config-Modul
from src.config.config import Config

class SpeechToTextClient:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GOOGLE_CREDENTIALS_PATH
        self.client = speech.SpeechClient()

    def transcribe(self, audio_bytes: bytes, sample_rate_hertz: int = 8000):
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=sample_rate_hertz,
            language_code="de-DE",
            model="phone_call",
            enable_automatic_punctuation=True
        )
        response = self.client.recognize(config=config, audio=audio)
        return " ".join(r.alternatives[0].transcript for r in response.results)
