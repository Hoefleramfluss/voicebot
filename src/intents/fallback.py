import random
import os
from openai import OpenAI

FALLBACKS = [
    "Entschuldige, da habe ich gerade was nicht ganz geschnallt – darf ich kurz nachhaken, oder soll ich dir einfach unsere Spezialitäten nennen?",
    "Ups, das war jetzt ein bisschen zu schnell für mich – darf ich nochmal nachfragen, oder willst du lieber ein paar Empfehlungen hören?",
    "Das habe ich leider nicht ganz verstanden – möchtest du, dass ich dir unsere Highlights vorstelle?",
    "Ich bin kurz ins Grübeln gekommen – magst du mir nochmal auf die Sprünge helfen oder lieber einen Schmäh hören?",
    "Das war jetzt ein echter Zungenbrecher! Willst du einen Witz hören, solange ich nachdenke?",
    "Ich hab’s nicht ganz erwischt – aber ich kann dich gern überraschen, wenn du magst!",
    "Da bin ich jetzt überfragt – aber ich kann dir einen Tipp geben: Probier unser Frühstücksbuffet!"
]

# GPT-gestützter Fallback
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def creative_fallback(context=None, user_text=None):
    prompt = (
        "Du bist ein charmanter, humorvoller, kreativer Gastronomie-Bot mit Wiener Schmäh. "
        "Der User hat etwas gesagt, das du nicht verstehst oder das keinen klaren Intent hat. "
        "Antworte immer kreativ, freundlich, abwechslungsreich, gern mit Humor oder einem Insider. "
        "Beziehe dich auf das, was der User zuletzt gesagt hat, und biete immer eine Anschlussmöglichkeit an (z.B. 'Magst noch was wissen?'). "
        f"Letzte Eingabe: '{user_text or ''}'. Kontext: {context or ''}"
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
    return random.choice(FALLBACKS)
