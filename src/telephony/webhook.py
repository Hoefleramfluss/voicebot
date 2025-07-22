from fastapi import Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from src.modules.elevenlabs import create_elevenlabs_response
import logging

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


from fastapi import Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from src.modules.elevenlabs import create_elevenlabs_response
import logging

@router.post("/gather")
async def gather_callback(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    speech_result = form.get("SpeechResult", "").strip()
    confidence = float(form.get("Confidence", 0.0))

    logging.info(f"Gather-Callback: CallSid={call_sid}, SpeechResult='{speech_result}', Confidence={confidence}")

    r = VoiceResponse()

    if not speech_result or confidence < 0.5:
        r.say("Entschuldigung, i hob di ned verstandn. Magst du’s noch amoi probiern?", language="de-AT")
        return Response(content=str(r), media_type="application/xml")

    # Beispielhafte GPT-Reaktion (Placeholder)
    gpt_output = {"response": "Grüß dich, wie darf ich dich nennen?"}
    gpt_text = gpt_output.get("response", "Des hob i jetzt leider ned ganz verstandn.")

    # ElevenLabs TTS erzeugen
    tts_twiml = create_elevenlabs_response(gpt_text)
    r.append(VoiceResponse().from_xml(f"<Response>{tts_twiml}</Response>"))

    return Response(content=str(r), media_type="application/xml")

@router.post("/gather")
async def gather_callback(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    speech_result = form.get("SpeechResult", "").strip()
    confidence = float(form.get("Confidence", 0.0))

    logging.info(f"Gather-Callback: CallSid={call_sid}, SpeechResult='{speech_result}', Confidence={confidence}")

    r = VoiceResponse()

    if not speech_result or confidence < 0.5:
        r.say("Entschuldigung, i hob di ned verstandn. Magst du’s noch amoi probiern?", language="de-AT")
        return Response(content=str(r), media_type="application/xml")

    # GPT-Aufruf (später ersetzen durch echte GPT-Intenterkennung)
    gpt_output = {"response": "Grüß dich, wie darf ich dich nennen?"}
    gpt_text = gpt_output.get("response", "Des hob i jetzt leider ned ganz verstandn.")

    # ElevenLabs erzeugen
    tts_twiml = create_elevenlabs_response(gpt_text)
    r.append(VoiceResponse().from_xml(f"<Response>{tts_twiml}</Response>"))

    return Response(content=str(r), media_type="application/xml")
