from fastapi import APIRouter, Request
from loguru import logger
from starlette.responses import JSONResponse
import base64

router = APIRouter()

from src.websocket.handlers import get_session_ws

def decode_audio(event):
    # Twilio liefert base64-kodierte mu-law-Frames
    return base64.b64decode(event["media"]["payload"]) if "media" in event else None

@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    event = await request.json()
    logger.info(f"Twilio Event: {event.get('event', '')}")
    if event.get("event") == "start":
        logger.info(f"Call started: {event}")
    elif event.get("event") == "media":
        audio = decode_audio(event)
        stream_sid = event.get("streamSid")
        ws = get_session_ws(stream_sid)
        if ws and audio:
            try:
                await ws.send_bytes(audio)
                logger.info(f"Audioframe an WS-Session {stream_sid} weitergeleitet ({len(audio)} bytes)")
            except Exception as e:
                logger.error(f"Fehler beim WS-Senden: {e}")
        else:
            logger.warning(f"Keine aktive WS-Session für streamSid={stream_sid}")
    elif event.get("event") == "stop":
        logger.info(f"Call stopped: {event}")
    return JSONResponse({"status": "ok"})
