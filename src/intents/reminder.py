"""
Reminder- und Flow-Logik: Merkt offene Anliegen, bietet Rückkehr an.
"""
class ReminderManager:
    def __init__(self):
        self.open_flows = {}

    def set_reminder(self, session_id, flow):
        self.open_flows[session_id] = flow

    def get_reminder(self, session_id):
        return self.open_flows.get(session_id)

    def clear_reminder(self, session_id):
        if session_id in self.open_flows:
            del self.open_flows[session_id]
