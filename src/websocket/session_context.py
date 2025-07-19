from typing import Dict

class SessionContextManager:
    def __init__(self):
        self.contexts: Dict[str, dict] = {}

    def set(self, session_id: str, key: str, value):
        if session_id not in self.contexts:
            self.contexts[session_id] = {}
        self.contexts[session_id][key] = value

    def get(self, session_id: str, key: str, default=None):
        return self.contexts.get(session_id, {}).get(key, default)

    def clear(self, session_id: str):
        if session_id in self.contexts:
            del self.contexts[session_id]

    # Erweiterung: parallele Intents und unterbrochene Antworten
    def set_pending_intent(self, session_id: str, intent: str, last_response: str = None):
        if session_id not in self.contexts:
            self.contexts[session_id] = {}
        self.contexts[session_id]["pending_intent"] = intent
        if last_response:
            self.contexts[session_id]["last_response"] = last_response

    def get_pending_intent(self, session_id: str):
        return self.contexts.get(session_id, {}).get("pending_intent")

    def clear_pending_intent(self, session_id: str):
        if session_id in self.contexts and "pending_intent" in self.contexts[session_id]:
            del self.contexts[session_id]["pending_intent"]
        if session_id in self.contexts and "last_response" in self.contexts[session_id]:
            del self.contexts[session_id]["last_response"]

    def get_last_response(self, session_id: str):
        return self.contexts.get(session_id, {}).get("last_response")

# Singleton für globale Nutzung
session_context = SessionContextManager()
