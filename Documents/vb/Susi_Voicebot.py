from flask import Flask, request, jsonify
import openai
import os
import re
from datetime import datetime
import dateparser
from twilio.rest import Client

app = Flask(__name__)

# OpenAI API-Key aus Umgebungsvariable laden
openai.api_key = os.getenv("OPENAI_API_KEY")

# Twilio-Config aus Umgebungsvariablen (setzen via heroku config:set TWILIO_...)
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Konstanten
SUSI_NAME = "Jessica"
RESTAURANT_NAME = "Höfler am Fluss"
FRUEHSTUECKS_LINK = "https://drive.google.com/file/d/1-FwErcbjAHZdDu7fa5B1oKtiHNlQELZv/view?usp=sharing"
SPEISEKARTE_LINK = "https://static1.squarespace.com/static/66969736b6669c5579542828/t/686580f466f6673ea1f641fb/1751482637733/PDF.pdf"
GUTSCHEIN_EMAIL = "hoefler@amfluss.info"

# Zustands-Speicher (Einfachheitshalber global, für mehrere Nutzer DB empfohlen)
conversations = {}

def format_datetime(dt):
    return dt.strftime("am %A, den %d. %B um %H Uhr")

def intent_erkennung(text):
    text = text.lower()
    if any(w in text for w in ["reservier", "tisch", "platz", "buchung", "reserve"]):
        return "reservierung"
    if any(w in text for w in ["job", "stellenangebot", "arbeiten", "jobanfrage", "bewerbung"]):
        return "job"
    if any(w in text for w in ["gutschein", "voucher", "geschenkschein"]):
        return "gutschein"
    if any(w in text for w in ["stornier", "absag", "cancel"]):
        return "storno"
    if any(w in text for w in ["speisekarte", "karte", "menu", "frühstück"]):
        return "speisekarte"
    if any(w in text for w in ["feedback", "meinung", "bewertung", "beschwerde"]):
        return "feedback"
    return "unbekannt"

def send_sms(to_number, message):
    if not twilio_account_sid or not twilio_auth_token or not twilio_phone_number:
        print("Twilio Credentials fehlen, SMS wird nicht gesendet.")
        return False
    try:
        twilio_client.messages.create(
            to=to_number,
            from_=twilio_phone_number,
            body=message
        )
        print(f"SMS an {to_number} gesendet.")
        return True
    except Exception as e:
        print(f"Fehler beim SMS-Versand: {e}")
        return False

@app.route("/voice", methods=["POST"])
def voice_webhook():
    caller = request.form.get("From", "")
    speech = request.form.get("SpeechResult", "") or request.form.get("TranscriptionText", "") or ""
    user_id = caller  # Vereinfacht: Nutzer-ID per Telefonnummer

    if user_id not in conversations:
        conversations[user_id] = {
            "step": "begrüßung",
            "name": None,
            "intent": None,
            "reservierung": {},
            "jobtext": None,
            "storno_ref": None
        }
    conv = conversations[user_id]
    antwort = ""

    if conv["step"] == "begrüßung":
        antwort = f"Hallo und Grüß Dich beim {RESTAURANT_NAME}. I bin die {SUSI_NAME}. Magst du mir vielleicht deinen Vornamen verraten?"
        conv["step"] = "name_erfassung"

    elif conv["step"] == "name_erfassung":
        name = speech.strip().split()[0].capitalize() if speech.strip() else "Gast"
        conv["name"] = name
        antwort = f"Servus {name}. Schön, dass du anrufst. Was kann ich für dich tun?"
        conv["step"] = "intent_erkennung"

    elif conv["step"] == "intent_erkennung":
        intent = intent_erkennung(speech)
        conv["intent"] = intent
        if intent == "reservierung":
            antwort = f"Liebend gerne, {conv['name']}. Für wann und wie viele Personen darf ich euch eintragen?"
            conv["step"] = "reservierung_datum_personen"
        elif intent == "job":
            antwort = f"Hey cool, dass du dich interessierst in unser Team zu kommen. Welche Stelle würde dich denn interessieren?"
            conv["step"] = "job_erfassung"
        elif intent == "gutschein":
            antwort = f"Wir bieten Gutscheine an, die du direkt bei uns im Restaurant oder online einlösen kannst. Möchtest du, dass ich einen Gutschein zur Abholung für dich vorbereite? Dann brauch ich noch deinen Namen, Datum und Uhrzeit."
            conv["step"] = "gutschein_erfassung"
        elif intent == "storno":
            antwort = "Kannst du mir bitte deine Reservierungsnummer sagen?"
            conv["step"] = "storno_nummer"
        elif intent == "speisekarte":
            antwort = f"Unsere Speisekarte findest du hier: {SPEISEKARTE_LINK}. Soll ich dir den Link per SMS senden?"
            conv["step"] = "speisekarte_sms"
        else:
            antwort = "Das hab ich leider nicht verstanden, magst du es nochmal anders versuchen? Oder möchtest du eine Tischreservierung, einen Gutschein oder etwas anderes?"
            conv["step"] = "intent_erkennung"

    elif conv["step"] == "reservierung_datum_personen":
        dt, personen = None, None
        date_match = dateparser.parse(speech, settings={"PREFER_DATES_FROM": "future"})
        if date_match:
            dt = date_match
        p_match = re.findall(r"\b\d{1,2}\b", speech)
        if p_match:
            personen = int(p_match[0])
        conv["reservierung"]["datum"] = dt
        conv["reservierung"]["personen"] = personen
        if dt and personen:
            dt_str = format_datetime(dt)
            antwort = f"Am {dt_str} für {personen} Personen, stimmt's? Gibt’s einen besonderen Anlass, Allergien oder Wünsche, damit alles perfekt für euch ist?"
            conv["step"] = "reservierung_kommentar"
        else:
            antwort = f"I hob leider noch ned alle Daten. Für wann und wie viele Personen soll die Reservierung sein?"

    elif conv["step"] == "reservierung_kommentar":
        comment = speech.strip()
        conv["reservierung"]["kommentar"] = comment
        dt = conv["reservierung"].get("datum")
        personen = conv["reservierung"].get("personen")
        dt_str = format_datetime(dt) if dt else "dem gewünschten Datum"
        antwort = f"Super, {conv['name']}, ich hab euch für {dt_str} für {personen} Personen eingetragen. Ich freu mich schon auf euren Besuch! Falls du noch was brauchst, sag einfach Bescheid."
        conv["step"] = "abschluss"

    elif conv["step"] == "job_erfassung":
        jobtext = speech.strip()
        conv["jobtext"] = jobtext
        antwort = f"Vielen Dank, {conv['name']}! Ich leite deine Bewerbung für die Stelle '{jobtext}' weiter. Wir melden uns bald bei dir!"
        # TODO: E-Mail versenden mit den Jobdaten an hoefler@amfluss.info
        conv["step"] = "abschluss"

    elif conv["step"] == "gutschein_erfassung":
        antwort = f"Alles klar, {conv['name']}. Wir bereiten deinen Gutschein zur Abholung vor. Danke für deinen Einkauf!"
        # TODO: E-Mail und Telefonanruf ans Restaurant mit Gutscheininfo
        conv["step"] = "abschluss"

    elif conv["step"] == "storno_nummer":
        ref = speech.strip().replace("#", "").upper()
        conv["storno_ref"] = ref
        antwort = f"Möchtest du wirklich die Reservierung mit der Nummer {ref} stornieren?"
        conv["step"] = "storno_bestaetigung"

    elif conv["step"] == "storno_bestaetigung":
        if any(w in speech.lower() for w in ["ja", "stornier", "bestätig", "okay", "ok", "yes"]):
            antwort = f"Okay, ich storniere das für dich. Danke für deine Rückmeldung, {conv['name']}!"
            # TODO: Storno an Resmio API senden
            conv["step"] = "abschluss"
        else:
            antwort = "Alles klar, die Reservierung bleibt bestehen. Wenn du noch was brauchst, sag einfach Bescheid."
            conv["step"] = "abschluss"

    elif conv["step"] == "speisekarte_sms":
        if any(w in speech.lower() for w in ["ja", "bitte", "gern", "gerne", "schick", "sms"]):
            if send_sms(caller, f"Hier der Link zur Speisekarte: {SPEISEKARTE_LINK}"):
                antwort = "Link zur Speisekarte wurde dir per SMS gesendet."
            else:
                antwort = "Leider konnte ich die SMS nicht senden."
        else:
            antwort = "Okay, wenn du den Link doch möchtest, sag einfach Bescheid."
        conv["step"] = "abschluss"

    elif conv["step"] == "abschluss":
        antwort = "Kann ich sonst noch was für dich tun?"
        conv["step"] = "intent_erkennung"

    else:
        antwort = "Tut mir leid, ich bin grad etwas überfordert. Versuch’s bitte nochmal!"
        conv["step"] = "begrüßung"
        conv["name"] = None
        conv["intent"] = None
        conv["reservierung"] = {}
        conv["jobtext"] = None
        conv["storno_ref"] = None

    return jsonify({"response": antwort})

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
