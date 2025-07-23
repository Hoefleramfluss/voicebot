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
    # --- Kontext & Session ---
    session_id = context.get("session_id") if isinstance(context, dict) else None
    user_name = context.get("name") if context else None
    if not user_name:
        user_name = "Gast"
    # Immer: Begrüßung
    if not session_context.get(session_id, "reservation_started"):
        session_context.set(session_id, "reservation_started", True)
        return {
            "text": f"Na sehr gerne {user_name}. Für wann darf ich reservieren?",
            "intent": "reservierung",
            "parsed": {},
            "slot_filling": True
        }

    # --- Always-On-Intentwechsel ---
    # (Hier nur symbolisch, da echter Intentwechsel im Router; kann aber via Kontextflag und session_context.get/set gesteuert werden)
    if context.get("new_intent") and context["new_intent"] != "reservierung":
        last_sentence = session_context.get(session_id, "last_sentence") or ""
        schmaeh = "Nicht so hastig, lass mich ausreden hihi."
        interruption = f"{last_sentence} {schmaeh}"
        session_context.set(session_id, "pending_intent", context["new_intent"])
        return {
            "text": interruption,
            "intent": context["new_intent"],
            "parsed": {},
            "slot_filling": False
        }

    # --- Parsing & Slot-Merging ---
    parsed = parse_reservation_text(text)
    previous = session_context.get(session_id, "reservation") if session_id else {}
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
    # Flexible Datumserkennung (z.B. siebter achter, kommenden Samstag, etc.)
    # (parse_reservation_text muss das liefern)
    # Gruppengröße > 10
    needs_confirmation = False
    if parsed.get("persons") and parsed["persons"] > 10:
        needs_confirmation = True
    # Wetterabfrage
    weather_info = None
    mood = None
    if parsed.get("date") and parsed.get("time") and (parsed.get("terrace") or "terrasse" in text.lower() or "wetter" in text.lower()):
        from src.intents.weather import OpenWeatherClient
        weather_info = OpenWeatherClient().get_forecast(parsed["date"], parsed["time"])
        # Stimmungserkennung (Dummy: falls negatives Wort in text)
        negative_words = ["schlecht", "regen", "kalt", "unfreundlich", "nervig"]
        if any(w in text.lower() for w in negative_words):
            mood = "negativ"
    # Upselling bei schlechter Stimmung oder immer nach Wetter
    upsell = upsell_recommendation() if (mood == "negativ" or weather_info) else ""
    # Pflichtslot-Fragen
    if missing:
        response_text = " ".join(missing) + (" " + upsell if upsell else "") + " Kann ich sonst noch etwas für dich tun?"
        return {
            "text": response_text,
            "intent": "reservierung",
            "parsed": parsed,
            "slot_filling": True,
            "weather_info": weather_info,
            "mood": mood
        }
    # Gruppengröße > 10: Zusatzhinweis
    if needs_confirmation:
        return {
            "text": "Bei mehr als zehn Gästen kann es sein, dass wir eine Anzahlung benötigen. Ich leite alles sofort weiter und es wird sich gleich wer bei dir melden. Passt das?",
            "intent": "reservierung",
            "parsed": parsed,
            "needs_confirmation": True
        }
    # Sonntagslogik
    if parsed.get("date") and is_sunday_reservation(parsed["date"]):
        send_telegram_alert(f"Sonntagsreservierung: {parsed}")
        from src.intents.faq.sonntag import get_sonntags_faqs, get_sonntags_video
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
    # Optionale End-Slots (Kommentar-Ausnahme)
    if not any([
        parsed.get("occasion"),
        parsed.get("special_request"),
        parsed.get("children"),
        parsed.get("terrace")
    ]):
        # Negativ-Erkennung
        negative = ["nein", "nö", "nichts", "ganz normal", "passt", "kein", "keine"]
        if any(w in text.lower() for w in negative):
            # Felder leer lassen, weiter
            pass
        else:
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
    send_telegram_alert(f"Neue Reservierung: {parsed}")
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
