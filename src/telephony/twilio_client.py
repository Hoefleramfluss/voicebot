from twilio.rest import Client
from config.config import Config

class TwilioClient:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

    def make_call(self, to_number, from_number, webhook_url):
        return self.client.calls.create(
            to=to_number,
            from_=from_number,
            url=webhook_url
        )
