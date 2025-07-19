from google.cloud import speech_v1 as speech
from config.config import Config
import os
import json

class SpeechToTextClient:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GOOGLE_APPLICATION_CREDENTIALS
        self.client = speech.SpeechClient()

    def streaming_recognize(self, audio_generator, language_code="de-DE", sample_rate=8000):
        from loguru import logger
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
        )
        logger.info(f"SpeechToTextClient: RecognitionConfig: encoding={config.encoding}, sample_rate_hertz={config.sample_rate_hertz}, language_code={config.language_code}")
        def request_generator():
            chunk_count = 0
            for chunk in audio_generator:
                chunk_count += 1
                if chunk_count <= 3:
                    logger.info(f"SpeechToTextClient: Audio-Chunk {chunk_count}: type={type(chunk)}, len={len(chunk)}, first_bytes={chunk[:8] if isinstance(chunk, bytes) else str(chunk)[:8]}")
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        return self.client.streaming_recognize(config=config, requests=request_generator())
