# src/speech_to_text/client.py

import os
from google.cloud import speech_v1p1beta1 as speech
# korrigierter Import
from src.config.config import Config

class SpeechToTextClient:
    def __init__(self):
        # Beispiel: Config könnte Deinen GCP-Credentials-Pfad enthalten
        credentials_path = Config.GOOGLE_CREDENTIALS_PATH
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
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
        transcripts = [result.alternatives[0].transcript for result in response.results]
        return " ".join(transcripts)
