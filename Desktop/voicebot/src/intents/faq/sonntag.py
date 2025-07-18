"""
Sonntags-/Speziallogik: Erkennt Sonntagsreservierungen und informiert über Frühstücksbuffet, FAQ und Video-Angebot.
"""
import datetime

def is_sunday_reservation(date_str):
    # Erwartet ISO-Format YYYY-MM-DD
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return dt.weekday() == 6

SONNTAGS_HINWEIS = "Am Sonntag gibt's bei uns von 8 bis 11 Uhr nur Frühstücksbuffet. Möchtest du mehr Infos oder ein Video sehen?"

SONNTAGS_FAQS = [
    "Was kostet das Frühstücksbuffet?", "Gibt's vegane Optionen?", "Braucht man Reservierung?", "Kann ich spontan vorbeikommen?"
]

def get_sonntags_faqs():
    return SONNTAGS_FAQS

# Video-Link oder Datei für WhatsApp anbieten
def get_sonntags_video():
    return "https://www.hoefleramfluss.at/fruehstuecksbuffet-video"
