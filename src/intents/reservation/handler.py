from src.intents.reservation.parse import parse_reservation_text
from src.resmio.resmio_client import ResMioClient
from src.websocket.session_context import session_context

from src.intents.upsell import upsell_recommendation
from src.intents.media import send_whatsapp, send_email
from src.intents.telegram_alerts import send_telegram_alert
from src.intents.faq.sonntag import is_sunday_reservation, SONNTAGS_HINWEIS, get_sonntags_faqs, get_sonntags_video
from src.intents.multilang import detect_language, translate


from src.utils.elevenlabs import create_elevenlabs_response

def handle_reservation(text, context=None):
    session_id = None
    if context and isinstance(context, dict):
        session_id = context.get("session_id")
    previous = session_context.get(session_id, "reservation") if session_id else None
    parsed = parse_reservation_text(text)
    if previous:
        for k, v in previous.items():
            if not parsed.get(k) and v:
                parsed[k] = v
    if session_id:
        session_context.set(session_id, "reservation", parsed)
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
        response = " ".join(missing) + " " + upsell + " " + abschluss
        return {
            "response": create_elevenlabs_response(response),
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": True
        }
    # Sonntagslogik
    if parsed.get("date") and is_sunday_reservation(parsed["date"]):
        sonntag_msg = SONNTAGS_HINWEIS
        sonntag_faqs = ", ".join(get_sonntags_faqs())
        sonntag_video = get_sonntags_video()
        response = f"{sonntag_msg}\nFAQs: {sonntag_faqs}\nVideo: {sonntag_video}"
        abschluss = "Kann ich sonst noch etwas für dich tun?"
        response += f"\n{upsell_recommendation()}\n{abschluss}"
        send_telegram_alert(f"Sonntagsreservierung: {parsed}")
        return {"response": create_elevenlabs_response(response), "intent": "reservierung", "sonntag": True, "parsed": parsed}
    # Abschlussfrage zu Anlass, Allergien, Sonderwünschen
    if not parsed.get("occasion") and not parsed.get("special_request") and not parsed.get("children") and not parsed.get("terrace"):
        upsell = upsell_recommendation()
        abschluss = "Kann ich sonst noch etwas für dich tun?"
        response = "Habt ihr was zu feiern? Oder hat wer von euch eine Allergie? Oder sonst noch Wünsche? Wir sorgen für eine schöne Zeit bei uns." + " " + upsell + " " + abschluss
        return {
            "response": create_elevenlabs_response(response),
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": "final_optional"
        }
    # Alles da: Bestätigungsabfrage vor finaler Reservierung
    if session_id:
        session_context.set(session_id, "reservation_pending", parsed)
    abschluss = "Kann ich sonst noch etwas für dich tun?"
    response = "Soll ich jetzt verbindlich reservieren? " + upsell_recommendation() + " " + abschluss
    return {
        "response": response,
        "intent": "reservierung",
        "parsed": parsed,
        "confirmation": True
    }

# Handler für Bestätigung (separat aufrufbar)
def confirm_reservation(session_id, text=None):
    from src.intents.upsell import upsell_recommendation
    from src.intents.media import send_whatsapp, send_email
    from src.intents.telegram_alerts import send_telegram_alert
    from src.websocket.session_context import session_context
    parsed = session_context.get(session_id, "reservation_pending")
    if not parsed:
        return {"response": "Keine Reservierung zum Bestätigen gefunden.", "intent": "reservierung"}
    # Korrekturwunsch erkennen
    if text:
        corrections = [
            ("datum", "Welches Datum soll ich stattdessen eintragen?"),
            ("uhrzeit", "Welche Uhrzeit möchtest du ändern?"),
            ("zeit", "Welche Uhrzeit möchtest du ändern?"),
            ("tag", "Welcher Tag ist richtig?"),
            ("falsch", "Was soll ich für dich korrigieren?")
        ]
        for word, question in corrections:
            if word in text.lower():
                return {"response": question, "intent": "reservierung", "correction": word, "parsed": parsed}
    session_context.set(session_id, "reservation_pending", None)
    resmio = ResMioClient()
    api_result = resmio.create_reservation(parsed)
    kontaktfrage = "Möchtest du eine Bestätigung per WhatsApp oder E-Mail bekommen? Sag mir einfach deine Mailadresse oder Handynummer."
    return {
        "response": f"Reservierung wurde weitergeleitet! Wir freuen uns auf euch. {kontaktfrage}",
        "intent": "reservierung",
        "parsed": parsed,
        "api_result": api_result,
        "needs_contact": True,
        "flow_end": True
    }
