from fastapi import FastAPI
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

from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Say, Pause

@app.post("/voice")
async def voice_webhook():
    response = VoiceResponse()
    start = Start()
    start.stream(url='wss://voicebot1-515ea4753341.herokuapp.com/ws/voice')
    response.append(start)
    response.say('Sie sind verbunden. Sprechen Sie jetzt.')
    response.pause(length=30)
    return Response(content=str(response), media_type="application/xml")
