from src.telegram.notifier import notifier

def handle_catering(text, context=None):
    # Extrahiere Cateringdaten (Platzhalter, später NLP/Slot-Filling)
    name = None
    persons = None
    wishes = None
    if context and isinstance(context, dict):
        name = context.get("name")
        persons = context.get("persons")
        wishes = context.get("wishes")
    details = f"Name: {name or '-'}\nPersonen: {persons or '-'}\nWünsche: {wishes or '-'}\nText: {text}"
    notifier.send_team_alert("Catering-Anfrage", details)
    return {
        "response": "Danke für deine Catering-Anfrage! Ich habe alles notiert und unser Team meldet sich schnellstmöglich bei dir.",
        "intent": "catering",
        "flow_end": True
    }
