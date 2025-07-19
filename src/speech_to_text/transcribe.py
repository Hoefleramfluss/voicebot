import base64
from src.speech_to_text.client import SpeechToTextClient
from loguru import logger

async def audio_stream_generator(websocket):
    while True:
        data = await websocket.receive_bytes()
        yield base64.b64decode(data)

from src.intents.intent_router import IntentRouter

import queue
import threading
import asyncio

def sync_audio_generator(q):
    while True:
        chunk = q.get()
        if chunk is None:
            break
        yield chunk

async def transcribe_audio(websocket):
    stt_client = SpeechToTextClient()
    q = queue.Queue()

    async def fill_queue():
        async for chunk in audio_stream_generator(websocket):
            q.put(chunk)
        q.put(None)  # End-Signal

    asyncio.create_task(fill_queue())

    responses = stt_client.streaming_recognize(sync_audio_generator(q))
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
