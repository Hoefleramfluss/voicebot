# src/speech_to_text/transcribe.py

import asyncio
import datetime
import json
import base64
import binascii
from loguru import logger
from src.speech_to_text.client import SpeechToTextClient
# <<< falls Config hier gebraucht wird
from src.config.config import Config

async def audio_stream_generator(websocket, first_chunk_timeout=30):
    logger.info("audio_stream_generator: started")
    got = False
    count = 0
    while True:
        try:
            msg = (await asyncio.wait_for(websocket.receive(), timeout=first_chunk_timeout)) if not got else await websocket.receive()
            got = True
            now = datetime.datetime.utcnow().isoformat()
            logger.info(f"[{now}] WS EVENT: {msg}")

            if msg.get("bytes") is not None:
                chunk = msg["bytes"]
            elif txt := msg.get("text"):
                js = json.loads(txt)
                if media := js.get("media"):
                    chunk = base64.b64decode(media["payload"])
                else:
                    chunk = base64.b64decode(txt, validate=True)
            else:
                continue

            count += 1
            logger.info(f"audio_stream_generator: Chunk #{count}, len={len(chunk)}")
            yield chunk

        except asyncio.TimeoutError:
            logger.warning("No audio in time – closing stream.")
            break
        except (binascii.Error, ValueError):
            logger.warning("Invalid base64 payload, skipping.")
        except RuntimeError as e:
            logger.warning(f"Receive error: {e}")
            break

async def transcribe_audio(websocket):
    logger.info("transcribe_audio: gestartet")
    stt = SpeechToTextClient()
    import queue
    q = queue.Queue()

    async def fill():
        c = 0
        async for chunk in audio_stream_generator(websocket):
            c += 1
            q.put(chunk)
        q.put(None)
        logger.info(f"fill_queue done, {c} chunks")

    asyncio.create_task(fill())

    def sync_gen():
        i = 0
        while True:
            ch = q.get()
            if ch is None:
                break
            i += 1
            yield ch

    responses = stt.streaming_recognize(sync_gen())
    async for resp in responses:
        for res in resp.results:
            txt = res.alternatives[0].transcript
            if res.is_final:
                await websocket.send_json({"type": "final", "text": txt})
                from src.intents.intent_router import IntentRouter
                intent = IntentRouter().handle(txt)
                await websocket.send_json({"type": "intent", **intent})
            else:
                await websocket.send_json({"type": "interim", "text": txt})
