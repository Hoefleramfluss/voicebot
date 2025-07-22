
import base64
import logging
from fastapi import Request, APIRouter
from fastapi.responses import Response, JSONResponse
from twilio.twiml.voice_response import VoiceResponse
from src.modules.elevenlabs import create_elevenlabs_response
from src.websocket.handlers import get_session_ws

router = APIRouter()

def decode_audio(event):
    return base64.b64decode(event["media"]["payload"]) if "media" in event else None

@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    event = await request.json()
    logging.info(f"Twilio Event: {event.get('event', '')}")
    if event.get("event") == "start":
        logging.info(f"Call started: {event}")
    elif event.get("event") == "media":
        audio = decode_audio(event)
        stream_sid = event.get("streamSid")
        ws = get_session_ws(stream_sid)
        if ws and audio:
            try:
                await ws.send_bytes(audio)
                logging.info(f"Audioframe an WS-Session {stream_sid} weitergeleitet ({len(audio)} bytes)")
            except Exception as e:
                logging.error(f"Fehler beim WS-Senden: {e}")
        else:
            logging.warning(f"Keine aktive WS-Session für streamSid={stream_sid}")
    elif event.get("event") == "stop":
        logging.info(f"Call stopped: {event}")
    return JSONResponse({"status": "ok"})

@router.post("/gather")
async def gather_callback(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    speech_result = form.get("SpeechResult", "").strip()
    confidence = float(form.get("Confidence", 0.0))

    logging.info(f"Gather-Callback: CallSid={call_sid}, SpeechResult='{speech_result}', Confidence={confidence}")

    if not speech_result or confidence < 0.5:
        r = VoiceResponse()
        r.say("Entschuldigung, i hob di ned verstandn. Magst du’s noch amoi probiern?", language="de-AT")
        return Response(content=str(r), media_type="application/xml")

    # GPT-Reaktion (Dummy)
    gpt_output = {"response": "Grüß dich, wie darf ich dich nennen?"}
    gpt_text = gpt_output.get("response", "Des hob i ned ganz verstandn.")

    tts_twiml = create_elevenlabs_response(gpt_text)
    twiml = f"<Response>{tts_twiml}</Response>"
    return Response(content=twiml, media_type="application/xml")
