from fastapi import FastAPI, Request
from starlette.websockets import WebSocket
from starlette.middleware.cors import CORSMiddleware
from config.config import Config
from src.utils.logger import setup_logger
from src.websocket.server import router as ws_router
from src.telephony.webhook import router as twilio_router

app = FastAPI(title="VoiceBot")

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

from fastapi.responses import Response

from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Hangup

@app.post("/voice")
async def voice_webhook():
    response = VoiceResponse()
    
    # Gather für Speech-to-Text mit optimalen Einstellungen
    gather = Gather(
        input='speech',  # Nur Speech, kein DTMF
        action='/gather',  # Callback-URL für Ergebnis
        method='POST',
        language='de-DE',  # Deutsche Sprache
        speechModel='phone_call',  # Optimiert für Telefonate
        speechTimeout='auto',  # Automatische Pause-Erkennung
        timeout=10,  # 10 Sekunden warten auf Input
        actionOnEmptyResult=True,  # Auch bei leerem Ergebnis Callback
        profanityFilter=False,  # Keine Zensur
        hints='Hallo, Hilfe, Information, Termin, Bestellung, Support'  # Erkennungs-Hints
    )
    
    gather.say('Hallo! Wie kann ich Ihnen helfen? Sprechen Sie jetzt.')
    response.append(gather)
    
    # Fallback falls kein Input
    response.say('Entschuldigung, ich habe Sie nicht verstanden. Auf Wiederhören.')
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")

@app.post("/gather")
async def gather_callback(request: Request):
    """Verarbeitet Speech-to-Text-Ergebnisse von Twilio Gather"""
    from src.intents.intent_router import IntentRouter
    from loguru import logger
    
    # Form-Daten von Twilio parsen
    form_data = await request.form()
    
    # Speech-to-Text-Ergebnis extrahieren
    speech_result = form_data.get('SpeechResult', '').strip()
    confidence = form_data.get('Confidence', '0.0')
    call_sid = form_data.get('CallSid', '')
    
    logger.info(f"Gather-Callback: CallSid={call_sid}, SpeechResult='{speech_result}', Confidence={confidence}")
    
    response = VoiceResponse()
    
    if speech_result:
        # Intent-Router für Spracherkennung
        intent_router = IntentRouter()
        intent_result = intent_router.handle(speech_result)
        
        logger.info(f"Intent-Ergebnis: {intent_result}")
        
        # Antwort basierend auf Intent
        if intent_result.get('type') == 'response':
            response.say(intent_result.get('text', 'Entschuldigung, das habe ich nicht verstanden.'))
        else:
            response.say(f"Sie haben gesagt: {speech_result}. Vielen Dank für Ihren Anruf.")
        
        # Weitere Eingabe möglich machen
        gather_again = Gather(
            input='speech',
            action='/gather',
            method='POST',
            language='de-DE',
            speechModel='phone_call',
            speechTimeout='auto',
            timeout=8,
            actionOnEmptyResult=True,
            profanityFilter=False,
            hints='Ja, Nein, Danke, Tschüss, Wiederholen, Hilfe'
        )
        gather_again.say('Möchten Sie noch etwas anderes wissen?')
        response.append(gather_again)
        
        # Fallback
        response.say('Vielen Dank für Ihren Anruf. Auf Wiederhören.')
        response.hangup()
    else:
        # Kein Speech-Ergebnis
        logger.warning(f"Gather-Callback: Kein SpeechResult erhalten. Form-Data: {dict(form_data)}")
        response.say('Entschuldigung, ich habe Sie nicht verstanden. Versuchen Sie es bitte noch einmal.')
        
        # Nochmal versuchen
        gather_retry = Gather(
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
        gather_retry.say('Wie kann ich Ihnen helfen? Sprechen Sie deutlich.')
        response.append(gather_retry)
        
        # Finale Fallback
        response.say('Auf Wiederhören.')
        response.hangup()
    
    return Response(content=str(response), media_type="application/xml")
