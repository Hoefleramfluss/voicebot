import base64
from src.speech_to_text.client import SpeechToTextClient
from loguru import logger

import asyncio

import base64
import binascii

async def audio_stream_generator(websocket, first_chunk_timeout=30):
    import datetime
    logger.info("audio_stream_generator: started")
    got_data = False
    while True:
        try:
            if not got_data:
                msg = await asyncio.wait_for(websocket.receive(), timeout=first_chunk_timeout)
            else:
                msg = await websocket.receive()
            got_data = True
            now = datetime.datetime.utcnow().isoformat()
            logger.info(f"[{now}] WS EVENT: type={msg['type']}, full: {msg}")
            if msg["type"] == "websocket.receive":
                if "bytes" in msg and msg["bytes"] is not None:
                    logger.info(f"[{now}] WS EVENT: type=bytes, len={len(msg['bytes'])}")
                    yield msg["bytes"]
                elif "text" in msg and msg["text"] is not None:
                    logger.info(f"[{now}] WS EVENT: type=str, len={len(msg['text'])}")
                    import json
                    try:
                        js = json.loads(msg["text"])
                        event_type = js.get("event", "unknown")
                        logger.info(f"[{now}] TWILIO EVENT: {event_type}, full: {js}")
                        if "media" in js and "payload" in js["media"]:
                            payload = js["media"]["payload"]
                            decoded = base64.b64decode(payload)
                            logger.info(f"[{now}] Decoded Twilio media.payload to bytes, len={len(decoded)}")
                            yield decoded
                        # Log all other Twilio event types explizit
                        elif event_type in ["connected", "start", "mark", "stop", "disconnect"]:
                            logger.info(f"[{now}] TWILIO NON-MEDIA EVENT: {event_type}, content: {js}")
                        else:
                            logger.warning(f"[{now}] JSON received, but no media.payload field found. Full event: {js}")
                    except Exception:
                        try:
                            decoded = base64.b64decode(msg["text"], validate=True)
                            logger.info(f"[{now}] Decoded base64 text to bytes, len={len(decoded)}")
                            yield decoded
                        except (binascii.Error, ValueError):
                            logger.warning(f"[{now}] Text message is not valid base64 or Twilio media JSON, ignoring.")
        except asyncio.TimeoutError:
            logger.warning(f"audio_stream_generator: No audio received in {first_chunk_timeout}s, closing.")
            break
        except RuntimeError as e:
            logger.warning(f"audio_stream_generator: receive() failed: {e!r}")
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
