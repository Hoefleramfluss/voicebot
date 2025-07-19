"""
Handover/Aufnahme: Startet Aufnahme für Chef- oder Mitarbeiter-Intent, speichert Audiodatei und Kontext.
"""
import os
from datetime import datetime

class HandoverRecorder:
    def __init__(self, base_dir="/tmp/voicebot_recordings"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_recording(self, session_id, audio_bytes, context=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"handover_{session_id}_{timestamp}.wav"
        path = os.path.join(self.base_dir, filename)
        with open(path, "wb") as f:
            f.write(audio_bytes)
        # Kontextdatei speichern
        if context:
            with open(path + ".meta", "w") as f:
                f.write(str(context))
        return path
