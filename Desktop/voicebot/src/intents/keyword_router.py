from src.intents.keywords_de import KEYWORDS

class KeywordRouter:
    def __init__(self):
        self.keywords = KEYWORDS

    def route(self, text: str):
        text_lower = text.lower()
        for intent, words in self.keywords.items():
            for word in words:
                if word in text_lower:
                    return intent
        return None
