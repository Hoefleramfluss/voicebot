# src/app.py

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
# <<< richtiges Paket
from src.config.config import Config
from src.utils.logger import setup_logger
from src.websocket.server import router as ws_router
from src.telephony.webhook import router as twilio_router
from src.intents.intent_router import IntentRouter
from src.modules.elevenlabs import create_elevenlabs_response
from loguru import logger
from pathlib import Path
import os

# Zwei Ebenen über src/app.py → zeigt auf /app
BASE_DIR = Path(__file__).resolve().parents[2]

app = FastAPI(title="VoiceBot")

# Schreibe statische Dateien nach BASE_DIR/static (wie ursprünglich)
STATIC_DIR = BASE_DIR / "static"
TTS_DIR = STATIC_DIR / "tts"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TTS_DIR.mkdir(parents=True, exist_ok=True)

# Statische Dateien aus BASE_DIR/static
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_logger(Config.LOGGING_TARGET)
app.include_router(ws_router)
app.include_router(twilio_router)

@app.get("/")
def root():
    return {"status": "VoiceBot API running"}

@app.get("/static-test")
def static_test():
    import os
    tts_dir = "/tmp/static/tts"
    if not os.path.exists(tts_dir):
        return {"tts_files": [], "msg": "Verzeichnis nicht vorhanden"}
    files = [f for f in os.listdir(tts_dir) if f.endswith('.mp3')]
    urls = [f"/static/tts/{f}" for f in files]
    return {"tts_files": files, "urls": urls}

@app.post("/voice")
async def voice_webhook():
    # Begrüßung und Prompt via ElevenLabs TTS
    greet_text = "Hallo! Wie kann ich dir helfen? Sprich einfach drauf los."
    tts_greet = create_elevenlabs_response(greet_text)
    fallback_text = "Entschuldigung, i hob di ned verstandn. Auf Wiederschaun."
    tts_fallback = create_elevenlabs_response(fallback_text)
    twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
  {tts_greet}
  <Gather input='speech' action='/gather' method='POST' language='de-DE' speechModel='phone_call' speechTimeout='auto' timeout='10' actionOnEmptyResult='true' profanityFilter='false' hints='Hallo, Hilfe, Information, Termin, Bestellung, Support'>
  </Gather>
  {tts_fallback}
  <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@app.post("/gather")
async def gather_callback(request: Request):
    form_data = await request.form()
    speech_result = form_data.get('SpeechResult', '').strip()
    confidence = float(form_data.get('Confidence', '0.0'))
    call_sid = form_data.get('CallSid', '')
    logger.info(f"Gather-Callback: CallSid={call_sid}, SpeechResult='{speech_result}', Confidence={confidence}")

    if speech_result:
        intent_result = IntentRouter().handle(speech_result)
        tts_text = intent_result.get("text", "Entschuldigung, das habe ich nicht ganz verstandn.")
        tts_twiml = create_elevenlabs_response(tts_text, request)
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  {tts_twiml}
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    else:
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
