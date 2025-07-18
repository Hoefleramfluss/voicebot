from src.utils.mailgun_client import send_email

def handle_faq(text, context=None):
    # Beispiel: Wenn nach Speisekarte gefragt wird
    if "speisekarte" in text.lower() or "frühstückskarte" in text.lower() or "hauptkarte" in text.lower():
        antwort = "Möchtest du die Karte per WhatsApp oder E-Mail bekommen? Sag mir einfach deine Mailadresse oder Handynummer."
        return {
            "response": antwort,
            "intent": "faq",
            "needs_contact": True,
            "flow_end": False
        }
    return {
        "response": "Hier sind unsere Öffnungszeiten: Mo-So 11-23 Uhr. Für mehr Details einfach fragen! Kann ich sonst noch etwas für dich tun?",
        "intent": "faq",
        "flow_end": True
    }
