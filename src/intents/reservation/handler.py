# src/intents/reservation/handler.py

from src.intents.reservation.parse import parse_reservation_text
from src.resmio.resmio_client import ResMioClient
from src.websocket.session_context import session_context

from src.intents.upsell import upsell_recommendation
from src.intents.media import send_whatsapp, send_email
from src.intents.telegram_alerts import send_telegram_alert
from src.intents.faq.sonntag import (
    is_sunday_reservation,
    SONNTAGS_HINWEIS,
)
from src.intents.multilang import detect_language, translate


def handle_reservation(text, context):
    session_id = context.get("session_id") if isinstance(context, dict) else None
    parsed = parse_reservation_text(text)
    previous = session_context.get(session_id, "reservation") if session_id else {}
    # Vorherige Slots übernehmen
    for k, v in (previous or {}).items():
        if not parsed.get(k) and v:
            parsed[k] = v
    if session_id:
        session_context.set(session_id, "reservation", parsed)
    # Pflichtslots prüfen
    missing = []
    if not parsed.get("persons"):
        missing.append("Für wie viele Personen darf ich reservieren?")
    if not parsed.get("date"):
        missing.append("An welchem Tag möchtest du kommen?")
    if not parsed.get("time"):
        missing.append("Um wieviel Uhr soll ich reservieren?")
    if missing:
        response_text = " ".join(missing) + " " + upsell_recommendation() + " Kann ich sonst noch etwas für dich tun?"
        return {
            "text": response_text,
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": True
        }
    # Sonntagslogik
    if parsed.get("date") and is_sunday_reservation(parsed["date"]):
        send_telegram_alert(f"Sonntagsreservierung: {parsed}")
        faqs = ", ".join(get_sonntags_faqs())
        video = get_sonntags_video()
        response_text = (
            f"{SONNTAGS_HINWEIS}\nFAQs: {faqs}\nVideo: {video} "
            + upsell_recommendation() + " Kann ich sonst noch etwas für dich tun?"
        )
        return {
            "text": response_text,
            "intent": "reservierung",
            "sonntag": True,
            "parsed": parsed
        }
    # Optionale End-Slots
    if not any([
        parsed.get("occasion"),
        parsed.get("special_request"),
        parsed.get("children"),
        parsed.get("terrace")
    ]):
        return {
            "text": (
                "Habt ihr was zu feiern? Oder hat wer von euch eine Allergie? "
                "Oder sonst noch Wünsche? Wir sorgen für eine schöne Zeit bei uns. "
                + upsell_recommendation()
                + " Kann ich sonst noch etwas für dich tun?"
            ),
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": "final_optional"
        }
    # Alles beisammen: Bestätigung fragen
    if session_id:
        session_context.set(session_id, "reservation_pending", parsed)
    return {
        "text": "Soll ich jetzt verbindlich reservieren? " + upsell_recommendation() + " Kann ich sonst noch etwas für dich tun?",
        "intent": "reservierung",
        "parsed": parsed,
        "confirmation": True
    }

def confirm_reservation(session_id, text=None):
    parsed = session_context.get(session_id, "reservation_pending")
    # Korrekturwunsch
    if text:
        lower = text.lower()
        for feld, frage in [
            ("date", "Welches Datum soll ich stattdessen eintragen?"),
            ("time", "Um wieviel Uhr möchtest du reservieren?"),
            ("date", "An welchem Tag möchtest du reservieren?")
        ]:
            if any(kw in lower for kw in ["datum", "uhrzeit", "tag", "falsch"]):
                return {
                    "text": frage,
                    "intent": "reservierung",
                    "correction": feld,
                    "parsed": parsed
                }
    session_context.set(session_id, "reservation_pending", None)
    api_result = ResMioClient().create_reservation(parsed)
    return {
        "text": (
            "Reservierung wurde weitergeleitet! Wir freuen uns auf euch. "
            "Möchtest du eine Bestätigung per WhatsApp oder E‑Mail bekommen? "
            "Sag mir einfach deine Mailadresse oder Handynummer."
        ),
        "intent": "reservierung",
        "parsed": parsed,
        "api_result": api_result,
        "needs_contact": True,
        "flow_end": True
    }
