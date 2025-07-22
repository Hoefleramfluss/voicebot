from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
from config.config import Config
from src.utils.logger import setup_logger
from src.websocket.server import router as ws_router
from src.telephony.webhook import router as twilio_router
from src.intents.intent_router import IntentRouter
from src.modules.elevenlabs import create_elevenlabs_response
from loguru import logger
from pathlib import Path

# Projekt-Root (zwei Ebenen über src/app.py → /app)
BASE_DIR = Path(__file__).resolve().parents[2]

app = FastAPI(title="VoiceBot")

# Statische Files für ElevenLabs-Audio (absoluter Pfad zum /static-Verzeichnis)
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
setup_logger(Config.LOGGING_TARGET)

# Routen
app.include_router(ws_router)
app.include_router(twilio_router)

@app.get("/")
def root():
    return {"status": "VoiceBot API running"}

@app.post("/voice")
async def voice_webhook():
    response = VoiceResponse()
    gather = Gather(
        input='speech',
        action='/gather',
        method='POST',
        language='de-DE',
        speechModel='phone_call',
        speechTimeout='auto',
        timeout=10,
        actionOnEmptyResult=True,
        profanityFilter=False,
        hints='Hallo, Hilfe, Information, Termin, Bestellung, Support'
    )
    gather.say('Hallo! Wie kann ich dir helfen? Sprich einfach drauf los.')
    response.append(gather)
    response.say('Entschuldigung, i hob di ned verstandn. Auf Wiederschaun.')
    response.hangup()
    return Response(content=str(response), media_type="application/xml")

@app.post("/gather")
async def gather_callback(request: Request):
    form_data = await request.form()
    speech_result = form_data.get('SpeechResult', '').strip()
    confidence = float(form_data.get('Confidence', '0.0'))
    call_sid = form_data.get('CallSid', '')

    logger.info(f"Gather-Callback: CallSid={call_sid}, SpeechResult='{speech_result}', Confidence={confidence}")

    if speech_result:
        intent_router = IntentRouter()
        intent_result = intent_router.handle(speech_result)
        logger.info(f"Intent-Ergebnis: {intent_result}")

        tts_text = intent_result.get("text", "Entschuldigung, das habe ich nicht ganz verstandn.")
        # request mitschicken für URL-Aufbau
        tts_twiml = create_elevenlabs_response(tts_text, request)
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  {tts_twiml}
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    else:
        logger.warning(f"Gather-Callback: Kein SpeechResult erhalten. Form-Data: {dict(form_data)}")
        response = VoiceResponse()
        gather = Gather(
            input='speech',
            action='/gather',
            method='POST',
            language='de-DE',
            speechModel='phone_call',
            speechTimeout='auto',
            timeout=8,
            actionOnEmptyResult=True,
            profanityFilter=False,
            hints='Hallo, Hilfe, Information, Termin, Bestellung, Support'
        )
        gather.say('Wie kann ich dir helfen? Sprich bitte deutlich.')
        response.append(gather)
        response.say('Auf Wiederschaun.')
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
