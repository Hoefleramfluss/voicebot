# src/telegram/notifier.py

from loguru import logger
# <<< richtiger Pfad
from src.config.config import Config

def notifier(message: str) -> None:
    try:
        # Beispiel: python-telegram-bot
        from telegram import Bot
        bot = Bot(token=Config.TELEGRAM_TOKEN)
        bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Telegram‑Notifikation gesendet: {message}")
    except Exception as e:
        logger.error(f"Fehler beim Telegram‑Senden: {e!r}")
