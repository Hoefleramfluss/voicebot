import re
from src.websocket.session_context import session_context

def ask_name(session_id=None):
    return {
        "response": "Wie darf ich dich ansprechen?",
        "intent": "name",
        "ask_name": True
    }

def handle_name(text, session_id=None):
    # Einfache Namenerkennung ("Ich heiße ...", "Mein Name ist ...", "Chris")
    match = re.search(r"(?:ich hei[ßs]e|mein name ist)\s+([A-Za-zÄÖÜäöüß]+)", text, re.IGNORECASE)
    name = None
    if match:
        name = match.group(1)
    elif len(text.split()) == 1 and text.istitle():
        name = text.strip()
    if name and session_id:
        session_context.set(session_id, "name", name)
        return {
            "response": f"Super, {name}! Dann lass uns loslegen. Für wie viele Personen darf ich reservieren?",
            "intent": "name",
            "name": name
        }
    # Ablehnung erkennen
    if any(word in text.lower() for word in ["wieso", "warum", "nein", "sicha ned", "mag nicht", "brauchst nicht"]):
        return {
            "response": "Kein Problem! Es ist nur für die Kommunikation angenehmer, aber wir können auch so weitermachen.",
            "intent": "name",
            "name": None
        }
    return {
        "response": "Ich habe deinen Namen leider nicht verstanden – magst du ihn nochmal wiederholen?",
        "intent": "name",
        "ask_name": True
    }
