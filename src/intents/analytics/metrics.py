"""
Analytics/Sentiment/A-B-Test: Tracking von Calls, Intents, Sentiment, Konversionen.
"""

import random
from collections import defaultdict

class AnalyticsManager:
    def __init__(self):
        self.calls = 0
        self.intents = defaultdict(int)
        self.sentiments = []
        self.ab_groups = {}

    def log_call(self):
        self.calls += 1

    def log_intent(self, intent):
        self.intents[intent] += 1

    def log_sentiment(self, score):
        self.sentiments.append(score)

    def get_stats(self):
        return {
            "calls": self.calls,
            "intents": dict(self.intents),
            "sentiments": self.sentiments,
        }

    def assign_ab_group(self, session_id):
        if session_id not in self.ab_groups:
            self.ab_groups[session_id] = random.choice(["A", "B"])
        return self.ab_groups[session_id]
