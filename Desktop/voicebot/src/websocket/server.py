from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()

from src.speech_to_text.transcribe import transcribe_audio
from src.websocket.handlers import register_session, unregister_session
from src.telegram.notifier import notifier

@router.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    session_id = websocket.query_params.get("session")
    await websocket.accept()
    logger.info(f"Client connected: {websocket.client}, session_id={session_id}")
    if session_id:
        register_session(session_id, websocket)
    try:
        await transcribe_audio(websocket)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}, session_id={session_id}")
        if session_id:
            unregister_session(session_id)
        # Telegram Call-Report
        notifier.send(f"Call beendet: session_id={session_id}, client={websocket.client}")
