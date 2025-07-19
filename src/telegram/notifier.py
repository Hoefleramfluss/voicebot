import requests
from config.config import Config
from loguru import logger

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send(self, message: str):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": message}
        try:
            response = requests.post(url, json=data, timeout=5)
            response.raise_for_status()
            logger.info(f"Telegram-Message sent: {message}")
        except Exception as e:
            logger.error(f"Telegram: Fehler beim Senden: {e}")

    def send_team_alert(self, subject: str, details: str):
        msg = f"[VoiceBot-ALERT] {subject}\n{details}"
        self.send(msg)

notifier = TelegramNotifier(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)
