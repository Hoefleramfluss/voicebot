from fastapi import Request, APIRouter
from fastapi.responses import Response
from src.modules.elevenlabs import create_elevenlabs_response

router = APIRouter()

@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    # Hier könntest du SpeechResult auswerten…
    # Dummy-Antwort
    gpt_text = "Grüß dich, wie darf ich dich nennen?"

    # Erzeuge TTS und baue TwiML
    tts_twiml = create_elevenlabs_response(gpt_text, request)
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  {tts_twiml}
</Response>"""
    return Response(content=twiml, media_type="application/xml")
