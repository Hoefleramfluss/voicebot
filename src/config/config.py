import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    HEROKU_API_KEY = os.getenv("HEROKU_API_KEY")
    RESMIO_API_DOC_URL = os.getenv("RESMIO_API_DOC_URL")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    SUBDOMAIN = os.getenv("SUBDOMAIN")
    LOGGING_TARGET = os.getenv("LOGGING_TARGET", "webinterface")
