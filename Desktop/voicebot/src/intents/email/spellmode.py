"""
SpellMode: Erkennung und Zusammenfassung von buchstabierten E-Mail-Adressen.
"""
import re

class SpellMode:
    # Erlaubt Buchstabieralphabet und gängige Namen
    LETTERS = set("abcdefghijklmnopqrstuvwxyzäöüß")
    SPECIALS = {"at": "@", "punkt": ".", "dot": ".", "minus": "-", "strich": "-", "unterstrich": "_"}

    def __init__(self):
        self.buffer = []

    def add(self, word):
        word = word.lower()
        if word in self.SPECIALS:
            self.buffer.append(self.SPECIALS[word])
        elif len(word) == 1 and word in self.LETTERS:
            self.buffer.append(word)
        elif re.match(r"^[a-zäöüß0-9]$", word):
            self.buffer.append(word)
        # Sonst ignorieren oder erweitern

    def get_email(self):
        joined = "".join(self.buffer)
        if "@" in joined and "." in joined:
            return joined
        return None

    def reset(self):
        self.buffer = []
