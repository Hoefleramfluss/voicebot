from src.telegram.notifier import notifier

def handle_event(text, context=None):
    # Extrahiere Eventdaten (Platzhalter, später NLP/Slot-Filling)
    name = None
    persons = None
    date = None
    wishes = None
    if context and isinstance(context, dict):
        name = context.get("name")
        persons = context.get("persons")
        date = context.get("date")
        wishes = context.get("wishes")
    details = f"Name: {name or '-'}\nPersonen: {persons or '-'}\nDatum: {date or '-'}\nWünsche: {wishes or '-'}\nText: {text}"
    notifier.send_team_alert("Eventanfrage (Feier)", details)
    return {
        "response": "Danke für deine Anfrage! Ich habe alles notiert und unser Team meldet sich verlässlich bei dir.",
        "intent": "event",
        "flow_end": True
    }
