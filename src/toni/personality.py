from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import random
from datetime import datetime
import logging
from pathlib import Path
from elevenlabs import generate, stream, set_api_key, save

from config.config import Config

logger = logging.getLogger(__name__)
config = Config()
set_api_key(config.ELEVENLABS_API_KEY)

@dataclass
class Context:
    """Holds conversation context and state."""
    user_name: str = ""
    last_intent: str = ""
    previous_responses: List[str] = None
    user_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        self.previous_responses = self.previous_responses or []
        self.user_preferences = self.user_preferences or {}

class ToniPersonality:
    """Implements Toni's charming Viennese personality."""
    
    def __init__(self):
        self.config = Config()
        self.voice_id = self.config.ELEVENLABS_VOICE_ID
        self.context = Context()
        
        # Common Viennese expressions and jokes
        self.greetings = [
            "Servas und Grias Di",
            "Grüß Di",
            "Seas",
            "Hallo, schön dassd da bist",
            "Na, wer is denn da?"
        ]
        
        self.goodbyes = [
            "Bis bald im {restaurant_name}!",
            "Auf Wiederschauen!",
            "Mach's gut!",
            "Tschüssikowski!",
            "Servus und baba!"
        ]
        
        self.wiener_schmaeh = [
            "Des klingt ja fast so spannend wie a Wiener Würstel!",
            "Da bin i dabei, wie a Wiener bei an Heurigen!",
            "Des is ja fast so gut wie unser Kaiserschmarrn!",
            "Na servas, des is ja a Ding!",
            "Da werd i ja ganz neugierig wie a Kind im Süßwarenladen!"
        ]
    
    async def generate_response(self, user_input: str) -> str:
        """Generate a response using OpenAI with Toni's personality."""
        try:
            import openai
            
            # Prepare the conversation history
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Du bist Toni, der digitale Gastgeber des Restaurants {self.config.RESTAURANT_NAME} "
                        f"in {self.config.RESTAURANT_LOCATION}. Deine Persönlichkeit ist charmant, witzig und herzlich, "
                        "mit Wiener Schmäh. Du sprichst in leichtem Wiener Dialekt und bist immer freundlich und hilfsbereit. "
                        "Antworte immer auf Deutsch, außer der Gast spricht eine andere Sprache an."
                    )
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
            
            # Add context if available
            if self.context.user_name:
                messages.insert(1, {
                    "role": "system",
                    "content": f"Der Gast heißt {self.context.user_name}."
                })
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            # Get the response text
            response_text = response.choices[0].message['content'].strip()
            
            # Add some Viennese flavor randomly
            if random.random() < 0.3:  # 30% chance to add a Viennese expression
                response_text += " " + random.choice(self.wiener_schmaeh)
            
            # Update context
            self.context.previous_responses.append((user_input, response_text))
            if len(self.context.previous_responses) > 5:  # Keep only last 5 exchanges
                self.context.previous_responses.pop(0)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Da ist mir leider ein kleiner Patzer unterlaufen. Könntest du das bitte wiederholen?"
    
    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs."""
        try:
            audio = generate(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2"
            )
            return audio
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    def get_greeting(self) -> str:
        """Get a random greeting with the user's name if available."""
        greeting = random.choice(self.greetings)
        if self.context.user_name:
            greeting += f", {self.context.user_name}!"
        else:
            greeting += "!"
        return greeting
    
    def get_goodbye(self) -> str:
        """Get a random goodbye message."""
        return random.choice(self.goodbyes).format(
            restaurant_name=self.config.RESTAURANT_NAME
        )
    
    def update_context(self, **kwargs) -> None:
        """Update the conversation context."""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
            else:
                self.context.user_preferences[key] = value

# Singleton instance
toni = ToniPersonality()
