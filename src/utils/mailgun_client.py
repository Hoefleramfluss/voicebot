from config.config import Config
import logging

def send_email(to: str, subject: str, body: str):
    """Send email if ENABLE_MAIL is True in config. Otherwise, skip and log."""
    if not Config.ENABLE_MAIL:
        logging.info(f"Email sending disabled by config. Would send to {to}: {subject}\n{body}")
        return
    # Dummy-Implementierung für Deployment. Hier echte Mailgun-Integration ergänzen!
    print(f"[MAILGUN-FAKE] Sending email to {to}: {subject}\n{body}")
