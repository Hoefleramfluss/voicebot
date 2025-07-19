"""
Multi-Language/Übersetzung: Automatische Spracherkennung und Übersetzung für internationale Gäste.
"""
import requests
import os

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_URL = "https://api-free.deepl.com/v2/translate"

SUPPORTED_LANGS = ["DE", "EN", "HU", "CS", "IT"]

# Sprache anhand Vorwahl oder Text erkennen (Dummy)
def detect_language(phone_number=None, text=None):
    if phone_number:
        if phone_number.startswith("+36"):
            return "HU"
        if phone_number.startswith("+420"):
            return "CS"
        if phone_number.startswith("+39"):
            return "IT"
    # Fallback: Textanalyse (Dummy)
    return "DE"

# Übersetzung via DeepL
def translate(text, target_lang):
    if not DEEPL_API_KEY:
        return text
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    }
    try:
        resp = requests.post(DEEPL_URL, data=data)
        result = resp.json()
        return result["translations"][0]["text"]
    except Exception:
        return text
