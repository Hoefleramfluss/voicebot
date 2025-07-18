"""
Medienversand: WhatsApp- und E-Mail-Versand von Bestätigungen, Speisekarten, Gutscheinen, Videos.
"""
import os
import requests

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER")

# WhatsApp-Versand via Twilio

def send_whatsapp(to, message, media_url=None):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = {
        "From": f"whatsapp:{TWILIO_WHATSAPP}",
        "To": f"whatsapp:{to}",
        "Body": message
    }
    if media_url:
        data["MediaUrl"] = media_url
    try:
        requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN))
    except Exception:
        pass

# E-Mail-Versand via Mailgun

def send_email(to, subject, text, attachment_path=None):
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
    data = {
        "from": f"Höfler am Fluss <mailgun@{MAILGUN_DOMAIN}>",
        "to": [to],
        "subject": subject,
        "text": text
    }
    files = None
    if attachment_path:
        files = [("attachment", open(attachment_path, "rb"))]
    try:
        requests.post(url, auth=("api", MAILGUN_API_KEY), data=data, files=files)
    except Exception:
        pass
