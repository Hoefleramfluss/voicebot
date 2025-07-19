from src.telegram.notifier import notifier

def handle_chef(text, context=None):
    # Extrahiere Anliegen (Platzhalter, später NLP/Slot-Filling)
    name = None
    concern = None
    if context and isinstance(context, dict):
        name = context.get("name")
        concern = context.get("concern")
    details = f"Name: {name or '-'}\nAnliegen: {concern or '-'}\nText: {text}"
    notifier.send_team_alert("Chef/Lieferanten-Anfrage", details)
    return {
        "response": "Ich leite das direkt an den Chef weiter. Du bekommst spätestens am nächsten Werktag eine Rückmeldung.",
        "intent": "chef",
        "flow_end": True
    }
