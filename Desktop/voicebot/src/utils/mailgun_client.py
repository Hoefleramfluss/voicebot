import requests
import logging
from typing import Optional

MAILGUN_API_KEY = "d080d4df2dfb0aac4cba8e56890a3909-c5ea400f-c7b0aff6"
MAILGUN_DOMAIN = "sandboxa3c3d513c6354717bba82ca507161e33.mailgun.org"
MAILGUN_BASE_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}"

logger = logging.getLogger("mailgun")

def send_email(to: str, subject: str, text: str, html: Optional[str] = None, sender: Optional[str] = None) -> bool:
    if sender is None:
        sender = f"Toni vom Höfler am Fluss <toni@{MAILGUN_DOMAIN}>"
    data = {
        "from": sender,
        "to": [to],
        "subject": subject,
        "text": text,
    }
    if html:
        data["html"] = html
    try:
        response = requests.post(
            f"{MAILGUN_BASE_URL}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=data
        )
        response.raise_for_status()
        logger.info(f"Mailgun: E-Mail an {to} erfolgreich versendet.")
        return True
    except Exception as e:
        logger.error(f"Mailgun: Fehler beim Senden an {to}: {e}")
        return False
