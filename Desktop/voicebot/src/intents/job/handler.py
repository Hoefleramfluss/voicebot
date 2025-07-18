from src.telegram.notifier import notifier

def handle_job(text, context=None):
    # Einfache Extraktion der Daten (Platzhalter, später NLP/Slot-Filling)
    name = None
    phone = None
    stelle = None
    extra = None
    if context and isinstance(context, dict):
        name = context.get("name")
        phone = context.get("phone")
        stelle = context.get("stelle")
        extra = context.get("extra")
    # Telegram-Nachricht an Team
    details = f"Name: {name or '-'}\nTelefon: {phone or '-'}\nStelle: {stelle or '-'}\nBemerkung: {extra or '-'}\nText: {text}"
    notifier.send_team_alert("Jobanfrage", details)
    return {
        "response": "Danke für dein Interesse! Ich habe deine Anfrage direkt an das Team weitergeleitet. Wir melden uns so rasch wie möglich.",
        "intent": "job",
        "flow_end": True
    }
