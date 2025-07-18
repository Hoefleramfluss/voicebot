import os
import logging
from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import openai
import dateparser
import re

# --- Konfiguration ---

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

openai.api_key = OPENAI_API_KEY
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- Helferfunktionen ---

def openai_chat(messages, model="gpt-4o", temperature=0.7):
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()

def clean_ref_num(ref):
    return re.sub(r"[^a-zA-Z0-9]", "", ref).upper()

def parse_datetime(text):
    dt = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
    return dt

def send_sms(to, body):
    message = twilio_client.messages.create(
        body=body,
        from_=TWILIO_PHONE_NUMBER,
        to=to
    )
    logging.info(f"SMS sent to {to}, SID: {message.sid}")
    return message.sid

# --- Systemprompt für Jessica ---

SYSTEM_PROMPT = """
Du bist Jessica, die charmante, sympathische Telefonassistentin vom Restaurant "Höfler am Fluss" in Bad Erlach.
Du bist herzlich, locker, mit leicht niederösterreichischem Schmäh und behandelst Gäste immer persönlich und freundlich.
Du erkennst automatisch Intentionen wie Reservierung, Stornierung, Gutscheinverkauf, Jobanfragen, Feedback und leitest die Gespräche natürlich.
Bei Reservierungen fragst du nach Datum, Uhrzeit, Personenanzahl, Anlass und Allergien. Du bestätigst freundlich die Angaben.
Bei Stornierungen fragst du nach der Reservierungsnummer und bestätigst vor Ausführung.
Du duzt immer nach der Begrüßung und sprichst den Gast mit Vornamen an.
Sei charmant, hilfsbereit und nie roboterhaft.
"""

# --- Session-Status (in Memory für Demo) ---

sessions = {}

# --- Hauptroute für Twilio Voice ---

@app.route("/voice", methods=["POST"])
def voice():
    call_sid = request.values.get("CallSid")
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "").strip()
    digits = request.values.get("Digits", "").strip()

    logging.info(f"Anruf von {from_number} SID: {call_sid}, SpeechResult: '{speech_result}', Digits: '{digits}'")

    # Session anlegen / laden
    session = sessions.setdefault(call_sid, {
        "stage": "greet",
        "name": None,
        "intent": None,
        "reservation": {},
        "job": None,
        "awaiting_confirmation": False,
    })

    resp = VoiceResponse()

    # --- Dialogsteuerung ---

    if session["stage"] == "greet":
        # Begrüßung
        gather = Gather(input="speech", timeout=5, hints="Name, Vorname", action="/process_name", method="POST")
        gather.say("Hallo und Grüß di beim Höfler am Fluss. Ich bin die Jessica. Magst du mir vielleicht deinen Vornamen verraten?", language="de-AT")
        resp.append(gather)
        resp.redirect("/voice")  # Falls kein Input
        session["stage"] = "waiting_name"
        return Response(str(resp), mimetype="application/xml")

    if session["stage"] == "waiting_name":
        # Falls kein Name (ohne SpeechResult), nochmal fragen
        gather = Gather(input="speech", timeout=5, hints="Name, Vorname", action="/process_name", method="POST")
        gather.say("I hab dich leider nicht verstanden. Magst bitte deinen Vornamen sagen?", language="de-AT")
        resp.append(gather)
        resp.redirect("/voice")
        return Response(str(resp), mimetype="application/xml")

    # Fallback - sicherheitshalber
    resp.say("Entschuldigung, es ist ein Fehler aufgetreten. Bitte ruf später wieder an.", language="de-AT")
    resp.hangup()
    return Response(str(resp), mimetype="application/xml")


@app.route("/process_name", methods=["POST"])
def process_name():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.setdefault(call_sid, {"stage": None})

    if not speech_result:
        resp = VoiceResponse()
        gather = Gather(input="speech", timeout=5, hints="Name, Vorname", action="/process_name", method="POST")
        gather.say("Ich hab dich leider nicht verstanden. Wie heißt du?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    name = speech_result.split()[0].capitalize()
    session["name"] = name
    session["stage"] = "intent_query"

    resp = VoiceResponse()
    gather = Gather(input="speech", timeout=5, hints="Reservierung, Tisch, Gutschein, Job, Storno, Speisekarte", action="/process_intent", method="POST")
    gather.say(f"Servus {name}. Schön, dass du anrufst. Was kann ich für dich tun?", language="de-AT")
    resp.append(gather)
    resp.redirect("/voice")
    return Response(str(resp), mimetype="application/xml")


@app.route("/process_intent", methods=["POST"])
def process_intent():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").lower()
    session = sessions.setdefault(call_sid, {"stage": None})

    name = session.get("name", "Gast")

    resp = VoiceResponse()

    # Intenterkennung simpel per Schlüsselwörter
    if any(word in speech_result for word in ["reservier", "tisch", "platz"]):
        session["intent"] = "reservation"
        session["stage"] = "ask_reservation_date"
        gather = Gather(input="speech", timeout=5, action="/handle_reservation_date", method="POST")
        gather.say(f"Liebend gerne, {name}. Für wann darf ich euch eintragen? Datum und Uhrzeit bitte.", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    if any(word in speech_result for word in ["stornier", "absag"]):
        session["intent"] = "cancellation"
        session["stage"] = "ask_reservation_ref"
        gather = Gather(input="speech", timeout=5, action="/handle_cancellation_ref", method="POST")
        gather.say(f"Kannst du mir bitte deine Reservierungsnummer sagen?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    if any(word in speech_result for word in ["gutschein"]):
        session["intent"] = "voucher"
        session["stage"] = "ask_voucher_name"
        gather = Gather(input="speech", timeout=5, action="/handle_voucher_name", method="POST")
        gather.say(f"Sehr gern, {name}. Für wen darf ich den Gutschein vorbereiten?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    if any(word in speech_result for word in ["job", "stellenangebot", "arbeitsplatz"]):
        session["intent"] = "job"
        session["stage"] = "ask_job_position"
        gather = Gather(input="speech", timeout=5, action="/handle_job_position", method="POST")
        gather.say(f"Hey cool, dass du dich für einen Job bei uns interessierst! Welche Stelle würd dich denn interessieren?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    # Standardantwort bei Unklarheit
    gather = Gather(input="speech", timeout=5, hints="Reservierung, Gutschein, Job, Stornierung, Speisekarte", action="/process_intent", method="POST")
    gather.say("Das hab ich leider nicht verstanden. Magst du es bitte nochmal sagen?", language="de-AT")
    resp.append(gather)
    resp.redirect("/voice")
    return Response(str(resp), mimetype="application/xml")

# --- Reservierungsfluss ---

@app.route("/handle_reservation_date", methods=["POST"])
def handle_reservation_date():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    dt = parse_datetime(speech_result)
    resp = VoiceResponse()

    if not dt:
        gather = Gather(input="speech", timeout=5, action="/handle_reservation_date", method="POST")
        gather.say("Das Datum oder die Uhrzeit hab ich nicht verstanden. Magst du es nochmal sagen?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    # Prüfen auf Ruhetage (Di, Mi)
    if dt.weekday() in [1, 2]:
        gather = Gather(input="speech", timeout=5, action="/handle_reservation_date", method="POST")
        gather.say("Am Dienstag und Mittwoch haben wir Ruhetag. Kannst du einen anderen Tag nennen?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    session["reservation"]["datetime"] = dt.isoformat()
    session["stage"] = "ask_reservation_people"

    gather = Gather(input="speech", timeout=5, action="/handle_reservation_people", method="POST")
    gather.say(f"Am {dt.strftime('%A, %d. %B')} um {dt.strftime('%H Uhr')}. Für wie viele Personen darf ich reservieren?", language="de-AT")
    resp.append(gather)
    return Response(str(resp), mimetype="application/xml")


@app.route("/handle_reservation_people", methods=["POST"])
def handle_reservation_people():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    # Einfach nur Zahl aus der Antwort extrahieren
    num_match = re.search(r"\d+", speech_result)
    resp = VoiceResponse()

    if not num_match:
        gather = Gather(input="speech", timeout=5, action="/handle_reservation_people", method="POST")
        gather.say("Wie viele Personen werden es denn ungefähr?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    num = int(num_match.group())
    if num > 9:
        gather = Gather(input="speech", timeout=5, action="/handle_reservation_people", method="POST")
        gather.say("Für Gruppen ab 10 Personen ruf uns bitte direkt an, da wir das speziell vorbereiten.", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    session["reservation"]["people"] = num
    session["stage"] = "ask_reservation_comment"

    gather = Gather(input="speech", timeout=5, action="/handle_reservation_comment", method="POST")
    gather.say("Gibt’s einen besonderen Anlass, Allergien oder Wünsche, damit alles perfekt für euch ist?", language="de-AT")
    resp.append(gather)
    return Response(str(resp), mimetype="application/xml")


@app.route("/handle_reservation_comment", methods=["POST"])
def handle_reservation_comment():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    session["reservation"]["comment"] = speech_result
    session["stage"] = "confirm_reservation"

    dt_iso = session["reservation"].get("datetime", "")
    dt_human = ""
    if dt_iso:
        import datetime
        dt_human = datetime.datetime.fromisoformat(dt_iso).strftime("%A, %d. %B um %H Uhr")

    resp = VoiceResponse()
    gather = Gather(input="speech", timeout=5, action="/handle_reservation_confirm", method="POST")
    gather.say(f"Super {name}, ich hab euch für den {dt_human} für {session['reservation']['people']} Personen eingetragen. Stimmt das so?", language="de-AT")
    resp.append(gather)
    return Response(str(resp), mimetype="application/xml")


@app.route("/handle_reservation_confirm", methods=["POST"])
def handle_reservation_confirm():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").lower()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    resp = VoiceResponse()

    if any(word in speech_result for word in ["ja", "stimmt", "genau", "richtig", "passt"]):
        # TODO: hier API-Call zu Resmio mit session["reservation"] einbauen
        resp.say(f"Super, {name}! Ich freue mich schon auf euren Besuch beim Höfler am Fluss.", language="de-AT")
        session["stage"] = "done"
        # Hier auch SMS oder Mail optional versenden
        resp.hangup()
        return Response(str(resp), mimetype="application/xml")

    else:
        session["stage"] = "ask_reservation_date"
        gather = Gather(input="speech", timeout=5, action="/handle_reservation_date", method="POST")
        gather.say("Okay, dann sag mir bitte nochmal Datum und Uhrzeit.", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")


# --- Stornierungsfluss ---

@app.route("/handle_cancellation_ref", methods=["POST"])
def handle_cancellation_ref():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    ref_num = clean_ref_num(speech_result)
    session["cancellation_ref"] = ref_num
    session["stage"] = "confirm_cancellation"

    resp = VoiceResponse()
    gather = Gather(input="speech", timeout=5, action="/handle_cancellation_confirm", method="POST")
    gather.say(f"Möchtest du wirklich die Reservierung mit der Nummer {ref_num} stornieren?", language="de-AT")
    resp.append(gather)
    return Response(str(resp), mimetype="application/xml")


@app.route("/handle_cancellation_confirm", methods=["POST"])
def handle_cancellation_confirm():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").lower()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    resp = VoiceResponse()

    if any(word in speech_result for word in ["ja", "stimmt", "genau", "richtig", "passt"]):
        # Hier Resmio API Cancel einbauen mit session["cancellation_ref"]
        # Beispiel: cancel_reservation(session["cancellation_ref"])

        # Antwort an Anrufer:
        resp.say(f"Okay, ich storniere die Reservierung {session['cancellation_ref']} für dich. Danke, {name}!", language="de-AT")
        session["stage"] = "done"
        resp.hangup()
        return Response(str(resp), mimetype="application/xml")

    else:
        resp.say("Okay, die Reservierung bleibt bestehen. Wenn du noch etwas brauchst, einfach melden!", language="de-AT")
        session["stage"] = "done"
        resp.hangup()
        return Response(str(resp), mimetype="application/xml")

# --- Gutscheinfluss ---

@app.route("/handle_voucher_name", methods=["POST"])
def handle_voucher_name():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    session["voucher_name"] = speech_result
    session["stage"] = "ask_voucher_date"

    resp = VoiceResponse()
    gather = Gather(input="speech", timeout=5, action="/handle_voucher_date", method="POST")
    gather.say(f"Für wann darf ich den Gutschein vorbereiten?", language="de-AT")
    resp.append(gather)
    return Response(str(resp), mimetype="application/xml")

@app.route("/handle_voucher_date", methods=["POST"])
def handle_voucher_date():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    dt = parse_datetime(speech_result)
    resp = VoiceResponse()

    if not dt:
        gather = Gather(input="speech", timeout=5, action="/handle_voucher_date", method="POST")
        gather.say("Das Datum hab ich nicht verstanden. Magst du es nochmal sagen?", language="de-AT")
        resp.append(gather)
        return Response(str(resp), mimetype="application/xml")

    session["voucher_date"] = dt.isoformat()
    session["stage"] = "ask_voucher_time"

    gather = Gather(input="speech", timeout=5, action="/handle_voucher_time", method="POST")
    gather.say(f"Um wieviel Uhr darf der Gutschein abgeholt werden?", language="de-AT")
    resp.append(gather)
    return Response(str(resp), mimetype="application/xml")

@app.route("/handle_voucher_time", methods=["POST"])
def handle_voucher_time():
    call_sid = request.values.get("CallSid")
    speech_result = request.values.get("SpeechResult", "").strip()
    session = sessions.get(call_sid, {})
    name = session.get("name", "Gast")

    session["voucher_time"] = speech_result
    session["stage"] = "confirm_voucher"

    dt_human = ""
    if "voucher_date"
