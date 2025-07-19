from google.cloud import speech_v2 as speech
from config.config import Config
import os

class SpeechToTextClient:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GOOGLE_APPLICATION_CREDENTIALS
        self.client = speech.SpeechClient()

    def streaming_recognize(self, audio_generator, language_code="de-AT", sample_rate=8000):
        config = speech.RecognitionConfig(
            auto_decoding_config=speech.AutoDetectDecodingConfig(),
            language_codes=[language_code],
            model="latest_long",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
        )
        def request_generator():
            # Erstes Paket: Konfiguration
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
            # Danach: Audiodaten
            for chunk in audio_generator:
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        return self.client.streaming_recognize(requests=request_generator())
