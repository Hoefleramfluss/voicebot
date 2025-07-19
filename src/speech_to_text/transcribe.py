import base64
from src.speech_to_text.client import SpeechToTextClient
from loguru import logger

async def audio_stream_generator(websocket):
    logger.info("audio_stream_generator: started")
    got_data = False
    while True:
        try:
            data = await websocket.receive_bytes()
            got_data = True
            logger.info(f"Raw WS data: type={type(data)}, len={len(data)}")
            yield base64.b64decode(data)
        except RuntimeError as e:
            logger.warning(f"audio_stream_generator: receive_bytes() failed: {e!r}")
            if not got_data:
                logger.warning("audio_stream_generator: No data received before disconnect!")
            break

from src.intents.intent_router import IntentRouter

import queue
import threading
import asyncio

def sync_audio_generator(q):
    while True:
        chunk = q.get()
        if chunk is None:
            break
        logger.info(f"Audio chunk: type={type(chunk)}, len={len(chunk)}")
        yield chunk

async def transcribe_audio(websocket):
    stt_client = SpeechToTextClient()
    q = queue.Queue()

    async def fill_queue():
        try:
            async for chunk in audio_stream_generator(websocket):
                q.put(chunk)
        except Exception as e:
            logger.warning(f"fill_queue: {e!r}")
        finally:
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
