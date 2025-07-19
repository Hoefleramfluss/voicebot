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
            sample_rate_hertz=sample_rate,

            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            enable_spoken_punctuation=True,
            enable_spoken_emojis=True,
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )
        return self.client.streaming_recognize(
            config=streaming_config,
            requests=(speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in audio_generator)
        )
