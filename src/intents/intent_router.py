from src.intents.keyword_router import KeywordRouter
from src.intents.reservation.handler import handle_reservation, confirm_reservation
from src.intents.faq.handler import handle_faq
from src.intents.smalltalk.handler import handle_smalltalk
from src.intents.fallback import creative_fallback
from src.websocket.session_context import session_context
from src.intents.name.handler import ask_name, handle_name
from src.intents.job.handler import handle_job
from src.intents.event.handler import handle_event
from src.intents.catering.handler import handle_catering
from src.intents.chef.handler import handle_chef
from src.intents.wetter.handler import handle_wetter

# NEU: Erweiterte Module
from src.intents.reminder import ReminderManager
from src.intents.analytics.metrics import AnalyticsManager
from src.intents.upsell import upsell_recommendation
from src.intents.telegram_alerts import send_telegram_alert
from src.intents.email.spellmode import SpellMode
from src.intents.media import send_whatsapp, send_email
from src.intents.multilang import detect_language, translate
from src.intents.handovers.recorder import HandoverRecorder
from src.intents.faq.sonntag import is_sunday_reservation, SONNTAGS_HINWEIS, get_sonntags_faqs, get_sonntags_video

class IntentRouter:
    def __init__(self):
        self.keyword_router = KeywordRouter()
        # NEU: Initialisierung der erweiterten Module
        self.analytics = AnalyticsManager()
        self.reminder = ReminderManager()
        self.spellmode = SpellMode()
        self.handover_recorder = HandoverRecorder()

    def handle(self, text, context=None):
        # Session-Kontext: session_id aus context
        session_id = None
        if context and isinstance(context, dict):
            session_id = context.get("session_id")
        last_intent = session_context.get(session_id, "last_intent") if session_id else None
        name = session_context.get(session_id, "name") if session_id else None

        # Analytics: Logge jeden Call und Intent
        self.analytics.log_call()

        # Einstieg: Wenn kein Name im Kontext, aber pending_intent==reservierung, dann Namenerkennung und zurück in Reservierungsflow
        pending_intent = session_context.get(session_id, "pending_intent") if session_id else None
        if not name and pending_intent == "reservierung":
            from src.intents.name.handler import handle_name
            name_result = handle_name(text, session_id)
            if name_result.get("name"):
                # Name erkannt, zurück in Reservierungsflow
                session_context.set(session_id, "pending_intent", None)
                from src.intents.reservation.handler import handle_reservation
                context = dict(context) if context else {}
                context["name"] = name_result["name"]
                context["session_id"] = session_id
                return handle_reservation("", context)
            else:
                return name_result

        # Einstieg: Wenn kein Name im Kontext, frage nach Name
        if not name:
            if last_intent == "name":
                return handle_name(text, session_id)
            session_context.set(session_id, "last_intent", "name")
            return ask_name(session_id)

        intent = self.keyword_router.route(text)
        if intent:
            self.analytics.log_intent(intent)

        # Reminder: Offene Flows merken
        if session_id and last_intent and intent and intent != last_intent:
            self.reminder.set_reminder(session_id, last_intent)

        # Multi-Language: Sprache erkennen
        lang = detect_language(context.get("phone") if context else None, text)

        # --- Sonntagslogik bei Reservierung ---
        if intent == "reservierung" and context and context.get("date"):
            from src.intents.faq.sonntag import is_sunday_reservation, SONNTAGS_HINWEIS, get_sonntags_faqs, get_sonntags_video
            if is_sunday_reservation(context["date"]):
                sonntag_msg = SONNTAGS_HINWEIS
                sonntag_faqs = ", ".join(get_sonntags_faqs())
                sonntag_video = get_sonntags_video()
                response = f"{sonntag_msg}\nFAQs: {sonntag_faqs}\nVideo: {sonntag_video}"
                if name:
                    response = response.replace("{{name}}", name)
                # Übersetzen falls nötig
                if lang != "DE":
                    response = translate(response, lang)
                # Abschlussfrage
                response += f"\nKann ich sonst noch etwas für dich tun{f', {name}' if name else ''}?"
                return {"response": response, "intent": "reservierung", "sonntag": True}

        # Nach jedem Flow: Upsell-Empfehlung
        upsell = upsell_recommendation()
        # Abschlussfrage
        abschluss = f"Kann ich sonst noch etwas für dich tun{f', {name}' if name else ''}?"

        # --- NEU: Sofortige Intent-Wechsel und sanfte Flow-Unterbrechung ---
        if session_id and last_intent and intent and intent != last_intent and last_intent not in (None, "name"):
            # Merke neuen Intent
            session_context.set_pending_intent(session_id, intent)
            # Letzte Antwort merken (optional, falls Handler sie bereitstellt)
            last_response = session_context.get_last_response(session_id)
            # GPT-Schmäh für Unterbrechung generieren
            from src.intents.fallback import creative_fallback
            interruption_prompt = (
                f"Ein Gast unterbricht mitten im Flow mit einem neuen Wunsch/Intent. "
                f"Formuliere eine charmante, humorvolle Unterbrechung im Stil eines Wiener Gastwirts. "
                f"Beende den letzten Satz oder Gedanken möglichst schnörkellos. "
                f"Füge eine kurze Überleitung wie 'Nicht so hastig, lass mich ausreden hihi.' hinzu. "
                f"Personalisiere mit Vornamen, falls vorhanden. Letzte Antwort: '{last_response or ''}'. Vorname: '{name or ''}'."
            )
            interruption = creative_fallback(context=interruption_prompt, user_text=text)
            # Letzten Satz abschließen, dann Intent-Wechsel signalisieren
            response = interruption
            # Optional: letzte Antwort (z.B. "...Also, für 19.6. einen Tisch für fünf. Passt das?") anhängen
            if last_response:
                response += f" {last_response.strip()}"
            # Nach Unterbrechung direkt zum neuen Intent springen
            # Handler für neuen Intent aufrufen
            session_context.set(session_id, "last_intent", intent)
            session_context.clear_pending_intent(session_id)
            def ensure_text_key(result):
                if isinstance(result, dict):
                    if "text" not in result:
                        if "response" in result:
                            result["text"] = result["response"]
                        else:
                            result["text"] = "Entschuldigung, das habe ich nicht ganz verstanden."
                return result

            if intent == "reservierung":
                result = handle_reservation(text, context)
            elif intent == "faq":
                result = handle_faq(text, context)
            elif intent == "smalltalk":
                result = handle_smalltalk(text, context)
            elif intent == "job":
                result = handle_job(text, context)
            elif intent == "event":
                result = handle_event(text, context)
            elif intent == "catering":
                result = handle_catering(text, context)
            elif intent == "chef":
                result = handle_chef(text, context)
            elif intent == "feedback":
                result = {"response": "Danke für dein Feedback! Wir nehmen das sehr ernst und leiten es intern weiter.", "intent": "feedback", "flow_end": True}
            elif intent == "wetter":
                result = handle_wetter(text, context)
            else:
                result = {"response": f"Intent erkannt: {intent}", "intent": intent}
            # Personalisierung: Name in die neue Antwort einbauen, falls vorhanden
            if name and "response" in result:
                result["response"] = result["response"].replace("{{name}}", name)
            result = ensure_text_key(result)
            return {"response": response, "interrupted": True, "interrupted_intent": last_intent, **result}

        # Bestätigungsantworten für Reservierung erkennen
        if session_id and session_context.get(session_id, "reservation_pending"):
            confirmation_words = ["ja", "bitte reservieren", "bestätigen", "reservieren", "mach das", "okay", "ok", "passt"]
            if any(word in text.lower() for word in confirmation_words):
                return confirm_reservation(session_id)
        # Reminder-Logik: Flow-Wechsel erkennen
        if last_intent == "reservierung" and intent in ("faq", "smalltalk"):
            session_context.set(session_id, "last_intent", intent)
            return {
                "response": f"Klar! Ich beantworte gerne deine Frage. Danach können wir mit der Reservierung weitermachen, wenn du möchtest{f', {name}' if name else ''}.",
                "intent": intent,
                "reminder": "Du warst mitten in einer Reservierung. Zurück zum Buchungsvorgang?"
            }

        # Normaler Routing-Flow
        if intent == "reservierung":
            session_context.set(session_id, "last_intent", "reservierung")
            return handle_reservation(text, context)
        if intent == "faq":
            session_context.set(session_id, "last_intent", "faq")
            return handle_faq(text, context)
        if intent == "smalltalk":
            session_context.set(session_id, "last_intent", "smalltalk")
            return handle_smalltalk(text, context)
        if intent == "job":
            session_context.set(session_id, "last_intent", "job")
            return handle_job(text, context)
        if intent == "event":
            session_context.set(session_id, "last_intent", "event")
            return handle_event(text, context)
        if intent == "catering":
            session_context.set(session_id, "last_intent", "catering")
            return handle_catering(text, context)
        if intent == "chef":
            session_context.set(session_id, "last_intent", "chef")
            return handle_chef(text, context)
        if intent == "feedback":
            session_context.set(session_id, "last_intent", "feedback")
            # Feedback-Handler folgt, z.B. handle_feedback(text, context)
            return {"response": "Danke für dein Feedback! Wir nehmen das sehr ernst und leiten es intern weiter.", "intent": "feedback", "flow_end": True}
        if intent == "wetter":
            session_context.set(session_id, "last_intent", "wetter")
            return handle_wetter(text, context)
        if intent:
            session_context.set(session_id, "last_intent", intent)
            return {"response": f"Intent erkannt: {intent}", "intent": intent}
        # Fallback: GPT Wow-Antwort mit Kontext und Nutzereingabe
        return {"response": creative_fallback(context=context, user_text=text), "intent": None}
