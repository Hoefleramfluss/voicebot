import requests
from config.config import Config

class ResMioClient:
    def __init__(self):
        self.base_url = "https://api.resmio.com/v1/"  # Beispiel, siehe Doku
        self.doc_url = Config.RESMIO_API_DOC_URL

    def create_reservation(self, reservation_data):
        # TODO: Authentifizierung, echtes API-Schema laut Doku
        # Hier nur Stub!
        # response = requests.post(self.base_url + "reservations", json=reservation_data)
        # return response.json()
        return {"status": "stub", "sent": reservation_data}
