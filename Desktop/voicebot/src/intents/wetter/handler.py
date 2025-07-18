import requests
import os
import random
from datetime import datetime
from openai import OpenAI

# OpenWeatherMap API-Key aus Umgebungsvariable
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GPT-Client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Helper: Hole Wetterdaten für ein Datum (heute oder in Zukunft)
def get_weather_forecast(date=None, city="Wien"):
    if not OPENWEATHER_API_KEY:
        return None
    # Aktuelles Wetter oder Forecast (max 5 Tage per API)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=de"
    try:
        resp = requests.get(url)
        data = resp.json()
        if "list" not in data:
            return None
        # Datum parsen
        target = datetime.now().date() if not date else datetime.fromisoformat(date).date()
        best = None
        for entry in data["list"]:
            dt = datetime.fromtimestamp(entry["dt"]).date()
            if dt == target:
                best = entry
                break
        return best
    except Exception:
        return None

# GPT-generierte Wetterantwort

def gpt_weather_response(weather, user_text, date=None):
    temp = weather["main"]["temp"] if weather else "unbekannt"
    desc = weather["weather"][0]["description"] if weather else "unbekannt"
    base = f"Das Wetter am gewünschten Tag: {desc}, etwa {temp} Grad."
    # Prompt für GPT
    prompt = (
        f"Formuliere eine charmante, kreative Antwort für einen Gast, der nach dem Wetter fragt. "
        f"Füge Kontext hinzu (z.B. schlage bei Hitze einen Schattenplatz vor, bei Regen einen Platz drinnen). "
        f"Wetterbeschreibung: {desc}. Temperatur: {temp} Grad. Datum: {date or 'heute'}. "
        f"Ursprüngliche Frage: '{user_text}'. Antworte im Stil eines Wiener Gastwirts, variiere die Formulierung jedes Mal."
    )
    if client:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception:
            pass
    # Fallback: Zufällige Antwort
    fallback = [
        f"Zu deinem gewünschten Tag soll es {temp} Grad und {desc} geben – soll ich dir einen Platz draußen sichern?",
        f"Das Wetter schaut nach '{desc}' und {temp} Grad aus. Lieber Schattenplatz oder doch drinnen?",
        f"Es wird voraussichtlich {desc} mit {temp} Grad – sag Bescheid, ob du draußen sitzen magst!"
    ]
    return random.choice(fallback)

def handle_wetter(text, context=None):
    # Datum extrahieren (aus Kontext oder Text)
    date = None
    if context and isinstance(context, dict):
        date = context.get("date")
    # Suche nach explizitem Datum im Text (z.B. "am 19.", "am Samstag") ggf. erweitern
    # ... (kann mit parse_reservation_text kombiniert werden)
    weather = get_weather_forecast(date)
    antwort = gpt_weather_response(weather, text, date)
    return {
        "response": antwort,
        "intent": "wetter",
        "flow_end": False
    }
