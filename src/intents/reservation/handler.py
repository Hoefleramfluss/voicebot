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
    get_sonntags_faqs,
    get_sonntags_video,
)
from src.intents.multilang import detect_language, translate


def handle_reservation(text, context=None):
    session_id = context.get("session_id") if isinstance(context, dict) else None
    previous = session_context.get(session_id, "reservation") if session_id else {}
    parsed = parse_reservation_text(text)

    # Vorherige Slots übernehmen
    for k, v in (previous or {}).items():
        if not parsed.get(k) and v:
            parsed[k] = v
    if session_id:
        session_context.set(session_id, "reservation", parsed)

    # Fehlende Slots abfragen
    missing = []
    if not parsed.get("persons"):
        missing.append("Für wie viele Personen darf ich reservieren?")
    if not parsed.get("date"):
        missing.append("Für welches Datum möchtest du reservieren?")
    if not parsed.get("time"):
        missing.append("Um wieviel Uhr darf ich reservieren?")

    if missing:
        upsell = upsell_recommendation()
        abschluss = "Kann ich sonst noch etwas für dich tun?"
        response_text = " ".join(missing) + " " + upsell + " " + abschluss
        return {
            "text": response_text,
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": True,
        }

    # Sonntags-Logik
    if parsed.get("date") and is_sunday_reservation(parsed["date"]):
        sonntag_msg = SONNTAGS_HINWEIS
        sonntag_faqs = ", ".join(get_sonntags_faqs())
        sonntag_video = get_sonntags_video()
        upsell = upsell_recommendation()
        abschluss = "Kann ich sonst noch etwas für dich tun?"
        response_text = (
            f"{sonntag_msg}\nFAQs: {sonntag_faqs}\nVideo: {sonntag_video}\n"
            f"{upsell}\n{abschluss}"
        )
        send_telegram_alert(f"Sonntagsreservierung: {parsed}")
        return {
            "text": response_text,
            "intent": "reservierung",
            "sonntag": True,
            "parsed": parsed,
        }

    # Finale Slot‑Füllung: Anlass, Allergien, Sonderwünsche
    if (
        not parsed.get("occasion")
        and not parsed.get("special_request")
        and not parsed.get("children")
        and not parsed.get("terrace")
    ):
        upsell = upsell_recommendation()
        abschluss = "Kann ich sonst noch etwas für dich tun?"
        response_text = (
            "Habt ihr was zu feiern? Oder hat wer von euch eine Allergie? "
            "Oder sonst noch Wünsche? Wir sorgen für eine schöne Zeit bei uns. "
            + upsell
            + " "
            + abschluss
        )
        return {
            "text": response_text,
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": "final_optional",
        }

    # Alles beisammen: Bestätigung fragen
    if session_id:
        session_context.set(session_id, "reservation_pending", parsed)
    upsell = upsell_recommendation()
    abschluss = "Kann ich sonst noch etwas für dich tun?"
    response_text = "Soll ich jetzt verbindlich reservieren? " + upsell + " " + abschluss
    return {
        "text": response_text,
        "intent": "reservierung",
        "parsed": parsed,
        "confirmation": True,
    }


def confirm_reservation(session_id, text=None):
    from src.intents.upsell import upsell_recommendation
    from src.intents.media import send_whatsapp, send_email
    from src.intents.telegram_alerts import send_telegram_alert
    from src.websocket.session_context import session_context

    parsed = session_context.get(session_id, "reservation_pending")
    if not parsed:
        return {"text": "Keine Reservierung zum Bestätigen gefunden.", "intent": "reservierung"}

    # Korrekturwunsch erkennen
    if text:
        corrections = [
            ("datum", "Welches Datum soll ich stattdessen eintragen?"),
            ("uhrzeit", "Welche Uhrzeit möchtest du ändern?"),
            ("zeit", "Welche Uhrzeit möchtest du ändern?"),
            ("tag", "Welcher Tag ist richtig?"),
            ("falsch", "Was soll ich für dich korrigieren?"),
        ]
        for word, question in corrections:
            if word in text.lower():
                return {
                    "text": question,
                    "intent": "reservierung",
                    "correction": word,
                    "parsed": parsed,
                }

    session_context.set(session_id, "reservation_pending", None)
    resmio = ResMioClient()
    api_result = resmio.create_reservation(parsed)
    kontaktfrage = (
        "Möchtest du eine Bestätigung per WhatsApp oder E-Mail bekommen? "
        "Sag mir einfach deine Mailadresse oder Handynummer."
    )
    return {
        "text": f"Reservierung wurde weitergeleitet! Wir freuen uns auf euch. {kontaktfrage}",
        "intent": "reservierung",
        "parsed": parsed,
        "api_result": api_result,
        "needs_contact": True,
        "flow_end": True,
    }
