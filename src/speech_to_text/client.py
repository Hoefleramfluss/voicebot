from google.cloud import speech_v1 as speech
from config.config import Config
import os
import json

class SpeechToTextClient:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GOOGLE_APPLICATION_CREDENTIALS
        self.client = speech.SpeechClient()

    def streaming_recognize(self, audio_generator, language_code="de-DE", sample_rate=8000):
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
        )
        def request_generator():
            yield speech.StreamingRecognizeRequest(streaming_config=speech.StreamingRecognitionConfig(config=config))
            for chunk in audio_generator:
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        return self.client.streaming_recognize(requests=request_generator())
