import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    # Feature toggles for notification channels
    ENABLE_SMS = os.getenv("ENABLE_SMS", "false").lower() == "true"
    ENABLE_MAIL = os.getenv("ENABLE_MAIL", "false").lower() == "true"
    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_3794c7e1abbfc558322d8d980501ee72612c636068ffd768")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "TNBqK9B8EYhsR7cg6s2P")
    
    # Resmio
    RESMIO_API_KEY = os.getenv("RESMIO_API_KEY")
    RESMIO_LOCATION_ID = os.getenv("RESMIO_LOCATION_ID")
    
    # Notification
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    TEAM_NOTIFICATION_PHONE = os.getenv("TEAM_NOTIFICATION_PHONE", "+436641478060")
    
    # App Settings
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # URLs
    MENU_BREAKFAST_URL = "https://drive.google.com/file/d/1-FwErcbjAHZdDu7fa5B1oKtiHNlQELZv/view?usp=sharing"
    MENU_MAIN_URL = "https://static1.squarespace.com/static/66969736b6669c5579542828/t/686580f466f6673ea1f641fb/1751482637733/PDF.pdf"
    
    # Business Info
    RESTAURANT_NAME = "Höfler am Fluss"
    RESTAURANT_LOCATION = "Bad Erlach"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return not self.is_production
