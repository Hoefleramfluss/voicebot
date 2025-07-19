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
        notifier.send(f"Call beendet: session_id={session_id}, client={websocket.client}")
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR in ws/voice: {e!r}", exc_info=True)
        if session_id:
            unregister_session(session_id)
        notifier.send(f"Fehler in Call: session_id={session_id}, client={websocket.client}, error={e}")
        await websocket.close()


# --- Debug-WebSocket-Handler für Rohdaten ---
@router.websocket("/ws/debug")
async def debug_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"[DEBUG] Client connected: {websocket.client}")
    try:
        while True:
            msg = await websocket.receive()
            if msg["type"] == "websocket.receive":
                if "bytes" in msg and msg["bytes"] is not None:
                    logger.info(f"[DEBUG] Received BYTES: len={len(msg['bytes'])}")
                if "text" in msg and msg["text"] is not None:
                    logger.info(f"[DEBUG] Received TEXT: {msg['text']}")
    except Exception as e:
        logger.warning(f"[DEBUG] Exception: {e!r}")
    finally:
        logger.info(f"[DEBUG] Client disconnected: {websocket.client}")

# --- Test-WebSocket-Handler für Echo- und Dauerverbindung ---
@router.websocket("/ws/test")
async def test_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"[TEST] Client connected: {websocket.client}")
    try:
        while True:
            msg = await websocket.receive_text()
            logger.info(f"[TEST] Received: {msg}")
            await websocket.send_text(f"Echo: {msg}")
    except WebSocketDisconnect:
        logger.info(f"[TEST] Client disconnected: {websocket.client}")
