# src/speech_to_text/transcribe.py

import asyncio
import datetime
import json
import binascii
from loguru import logger
from src.speech_to_text.client import SpeechToTextClient
from src.config.config import Config  # nur nötig, wenn Du Config tatsächlich verwendest

async def audio_stream_generator(websocket, first_chunk_timeout=30):
    """
    Liest Audio‑Chunks (bytes oder base64-Twilio-Payloads) aus dem WebSocket
    und yieldet rohe Bytes für die STT-Pipeline.
    """
    logger.info("audio_stream_generator: started")
    got_data = False
    total_chunks = 0

    while True:
        try:
            msg = (
                await asyncio.wait_for(websocket.receive(), timeout=first_chunk_timeout)
                if not got_data
                else await websocket.receive()
            )
            got_data = True

            now = datetime.datetime.utcnow().isoformat()
            logger.info(f"[{now}] WS EVENT: {msg}")

            # Direktes Byte-Payload
            if msg.get("type") == "websocket.receive" and msg.get("bytes") is not None:
                chunk = msg["bytes"]
            # Twilio JSON-Payload
            elif msg.get("type") == "websocket.receive" and msg.get("text"):
                js = json.loads(msg["text"])
                if media := js.get("media", {}):
                    payload = media.get("payload")
                    chunk = base64.b64decode(payload)
                else:
                    # Falls Text wirklich base64 ist
                    chunk = base64.b64decode(msg["text"], validate=True)
            else:
                # Nicht‑Audio‑Event überspringen
                logger.warning(f"[{now}] Non‑audio message, skipping.")
                continue

            total_chunks += 1
            logger.info(f"audio_stream_generator: Chunk #{total_chunks}, len={len(chunk)}")
            yield chunk

        except asyncio.TimeoutError:
            logger.warning(f"audio_stream_generator: No audio in {first_chunk_timeout}s – closing.")
            break
        except (binascii.Error, ValueError):
            logger.warning("audio_stream_generator: Ungültiges base64, ignoriere Nachricht.")
        except RuntimeError as e:
            logger.warning(f"audio_stream_generator: receive() Error: {e!r}")
            break

async def transcribe_audio(websocket):
    """
    Steuert den kompletten Streaming‑Transkriptions‑Flow:
    1) Audio‑Chunks sammeln
    2) an Google STT schicken
    3) Ergebnisse (interim/final) per WebSocket zurücksenden
    """
    logger.info("transcribe_audio: gestartet")
    stt_client = SpeechToTextClient()

    # Verpacke asynchrone Generator‑Chunks in eine synchrone Queue
    import queue
    q = queue.Queue()

    async def fill_queue():
        count = 0
        async for chunk in audio_stream_generator(websocket):
            count += 1
            logger.info(f"fill_queue: Chunk {count}, len={len(chunk)}")
            q.put(chunk)
        q.put(None)  # End‑Signal
        logger.info(f"fill_queue: Fertig, insgesamt {count} Chunks")

    asyncio.create_task(fill_queue())

    # Sync‑Generator für den STT-Client
    def sync_generator():
        idx = 0
        while True:
            chunk = q.get()
            if chunk is None:
                logger.info("sync_generator: End‑Signal empfangen")
                break
            idx += 1
            logger.info(f"sync_generator: Yield Chunk {idx}, len={len(chunk)}")
            yield chunk

    # Streaming‑Ergebnis von Google STT verarbeiten
    try:
        responses = stt_client.streaming_recognize(sync_generator())
        async for response in responses:
            for result in response.results:
                text = result.alternatives[0].transcript
                if result.is_final:
                    logger.info(f"Final Transcript: {text}")
                    await websocket.send_json({"type": "final", "text": text})
                    # Intent-Routing
                    from src.intents.intent_router import IntentRouter
                    intent = IntentRouter().handle(text)
                    await websocket.send_json({"type": "intent", **intent})
                else:
                    logger.info(f"Interim Transcript: {text}")
                    await websocket.send_json({"type": "interim", "text": text})
    except Exception as e:
        logger.error(f"transcribe_audio: Exception im STT-Flow: {e!r}")
