"""
Telegram-Alerts: Interne Benachrichtigungen und Fallback bei API-Ausfällen.
"""
import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message, file_path=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception:
        pass
    if file_path:
        send_telegram_file(file_path)

def send_telegram_file(file_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    files = {"document": open(file_path, "rb")}
    data = {"chat_id": TELEGRAM_CHAT_ID}
    try:
        requests.post(url, files=files, data=data)
    except Exception:
        pass
