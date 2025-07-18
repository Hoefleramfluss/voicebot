"""
Upsell- und Wetter-Empfehlungsmodul: Gibt Empfehlungen je nach Wetter, Tageszeit, Temperatur, Anlass.
"""
import datetime
import random

def get_time_of_day():
    now = datetime.datetime.now()
    if 5 <= now.hour < 11:
        return "frühstück"
    elif 11 <= now.hour < 15:
        return "mittag"
    elif 15 <= now.hour < 18:
        return "nachmittag"
    elif 18 <= now.hour < 23:
        return "abend"
    else:
        return "nacht"

UPSELLS = {
    "frühstück": ["Probier unser Frühstücksbuffet!"],
    "mittag": ["Heute gibt's unser Mittagsmenü!"],
    "nachmittag": ["Wie wär's mit einem hausgemachten Eiskaffee?"],
    "abend": ["Ein Glas Wein zum Ausklang?"],
    "nacht": ["Für Nachtschwärmer gibt's bei uns auch was!"]
}

def upsell_recommendation(weather=None):
    tod = get_time_of_day()
    recs = UPSELLS.get(tod, [])
    if weather and weather.get("main") == "Clear" and tod == "nachmittag":
        recs.append("Bei Sonnenschein empfehle ich heute unseren Eiskaffee!")
    if recs:
        return random.choice(recs)
    return "Lass dich überraschen – wir haben immer was Besonderes!"
