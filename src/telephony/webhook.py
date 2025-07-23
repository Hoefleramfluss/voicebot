from fastapi import Request, APIRouter
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from src.modules.elevenlabs import create_elevenlabs_response
import logging

router = APIRouter()

@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    # Dummy-Antwort für Twilio Call
    gpt_text = "Grüß dich, wie darf ich dich nennen?"
    tts_twiml = create_elevenlabs_response(gpt_text)
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  {tts_twiml}
</Response>"""
    return Response(content=twiml, media_type="application/xml")

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
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  {tts_twiml}
</Response>"""
    return Response(content=twiml, media_type="application/xml")
