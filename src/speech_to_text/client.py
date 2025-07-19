from google.cloud import speech_v2 as speech
from config.config import Config
import os
import json

class SpeechToTextClient:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GOOGLE_APPLICATION_CREDENTIALS
        self.client = speech.SpeechClient()
        # Lies PROJECT_ID aus Credentials
        with open(Config.GOOGLE_APPLICATION_CREDENTIALS, "r") as f:
            creds = json.load(f)
        self.project_id = "bubbly-hexagon-465711-p2"
        self.location = "global"
        self.recognizer_id = "ssdd"

    def streaming_recognize(self, audio_generator, language_code="de-AT", sample_rate=8000):
        config = speech.RecognitionConfig(
            auto_decoding_config=speech.AutoDetectDecodingConfig(),
            language_codes=[language_code],
            model="latest_long",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
        )
        recognizer = f"projects/{self.project_id}/locations/{self.location}/recognizers/{self.recognizer_id}"
        def request_generator():
            # Erstes Paket: Konfiguration + Recognizer
            yield speech.StreamingRecognizeRequest(
                recognizer=recognizer,
                streaming_config=streaming_config
            )
            # Danach: Audiodaten
            for chunk in audio_generator:
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        return self.client.streaming_recognize(requests=request_generator())
