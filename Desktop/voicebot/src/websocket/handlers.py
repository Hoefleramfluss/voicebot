from typing import Dict
from fastapi import WebSocket

# Hält aktive Sessions: streamSid -> WebSocket
active_sessions: Dict[str, WebSocket] = {}

def register_session(session_id: str, websocket: WebSocket):
    active_sessions[session_id] = websocket

def unregister_session(session_id: str):
    if session_id in active_sessions:
        del active_sessions[session_id]

def get_session_ws(session_id: str):
    return active_sessions.get(session_id)
