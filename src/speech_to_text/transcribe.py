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
    total_chunks = 0
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
                    logger.info(f"audio_stream_generator: yield BYTES, len={len(msg['bytes'])}, first_bytes={msg['bytes'][:8]}")
                    total_chunks += 1
                    logger.info(f"audio_stream_generator: total_chunks={total_chunks}")
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
                            logger.info(f"audio_stream_generator: yield Twilio media BYTES, len={len(decoded)}, first_bytes={decoded[:8]}")
                            total_chunks += 1
                            logger.info(f"audio_stream_generator: total_chunks={total_chunks}")
                            yield decoded
                        elif event_type in ["connected", "start", "mark", "stop", "disconnect"]:
                            logger.info(f"[{now}] TWILIO NON-MEDIA EVENT: {event_type}, content: {js}")
                        else:
                            logger.warning(f"[{now}] JSON received, but no media.payload field found. Full event: {js}")
                    except Exception:
                        try:
                            decoded = base64.b64decode(msg["text"], validate=True)
                            logger.info(f"[{now}] Decoded base64 text to bytes, len={len(decoded)}")
                            logger.info(f"audio_stream_generator: yield BASE64 BYTES, len={len(decoded)}, first_bytes={decoded[:8]}")
                            total_chunks += 1
                            logger.info(f"audio_stream_generator: total_chunks={total_chunks}")
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
    logger.info("transcribe_audio: gestartet")
    stt_client = SpeechToTextClient()
    q = queue.Queue()

    async def fill_queue():
        chunk_counter = 0
        try:
            async for chunk in audio_stream_generator(websocket):
                chunk_counter += 1
                logger.info(f"fill_queue: Chunk {chunk_counter} aus audio_stream_generator empfangen, len={len(chunk)}, first_bytes={chunk[:8]}")
                q.put(chunk)
                logger.info(f"fill_queue: Chunk {chunk_counter} in Queue gelegt (qsize={q.qsize()})")
        except Exception as e:
            logger.error(f"fill_queue: {e!r}")
        finally:
            logger.info(f"fill_queue: End-Signal (None) wird gesetzt, insgesamt {chunk_counter} Chunks verarbeitet")
            q.put(None)  # End-Signal

    asyncio.create_task(fill_queue())

    try:
        chunk_list = []
        def debug_sync_audio_generator(q):
            chunk_counter = 0
            while True:
                chunk = q.get()
                if chunk is None:
                    logger.info(f"debug_sync_audio_generator: End-Signal empfangen, insgesamt {chunk_counter} Chunks verarbeitet")
                    break
                chunk_counter += 1
                logger.info(f"debug_sync_audio_generator: Chunk {chunk_counter} aus Queue empfangen, type={type(chunk)}, len={len(chunk)}, first_bytes={chunk[:8] if isinstance(chunk, bytes) else str(chunk)[:8]}")
                chunk_list.append(chunk)
                yield chunk
        responses = stt_client.streaming_recognize(debug_sync_audio_generator(q))
        logger.info("transcribe_audio: STT-Streaming gestartet")
        intent_router = IntentRouter()
        found_result = False
        async for response in responses:
            logger.info(f"transcribe_audio: STT-Response erhalten: {response}")
            for result in response.results:
                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    logger.info(f"Final: {transcript}")
                    await websocket.send_json({"type": "final", "text": transcript})
                    # Intent-Router aufrufen und Antwort senden
                    intent_result = intent_router.handle(transcript)
                    await websocket.send_json({"type": "intent", **intent_result})
                    found_result = True
                else:
                    logger.info(f"Interim: {result.alternatives[0].transcript}")
                    await websocket.send_json({"type": "interim", "text": result.alternatives[0].transcript})
        if not found_result:
            logger.warning("transcribe_audio: Kein finales Transkript erkannt!")
        if not chunk_list:
            logger.error("transcribe_audio: KEIN einziger Audio-Chunk im Stream! (Audio-Input leer)")
        elif all((not c or (isinstance(c, bytes) and len(c)==0)) for c in chunk_list):
            logger.error("transcribe_audio: ALLE Audio-Chunks sind leer!")
        else:
            logger.info(f"transcribe_audio: Insgesamt {len(chunk_list)} Audio-Chunks an Google STT geschickt.")
    except Exception as e:
        logger.error(f"transcribe_audio: Exception im STT-Flow: {e!r}")
        if 'Exception serializing request' in str(e):
            logger.error(f"transcribe_audio: Vermutlich ist der Audio-Stream leer oder fehlerhaft kodiert! Prüfe Audioformat und Twilio-Konfiguration.")
