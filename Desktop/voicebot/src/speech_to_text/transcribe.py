import base64
from src.speech_to_text.client import SpeechToTextClient
from loguru import logger

async def audio_stream_generator(websocket):
    while True:
        data = await websocket.receive_bytes()
        yield base64.b64decode(data)

from src.intents.intent_router import IntentRouter

async def transcribe_audio(websocket):
    stt_client = SpeechToTextClient()
    audio_gen = audio_stream_generator(websocket)
    responses = stt_client.streaming_recognize(audio_gen)
    intent_router = IntentRouter()
    async for response in responses:
        for result in response.results:
            if result.is_final:
                transcript = result.alternatives[0].transcript
                logger.info(f"Final: {transcript}")
                await websocket.send_json({"type": "final", "text": transcript})
                # Intent-Router aufrufen und Antwort senden
                intent_result = intent_router.handle(transcript)
                await websocket.send_json({"type": "intent", **intent_result})
            else:
                await websocket.send_json({"type": "interim", "text": result.alternatives[0].transcript})
