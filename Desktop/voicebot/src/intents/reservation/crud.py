"""
Resmio CRUD-Modul: Erstellt, liest, aktualisiert und löscht Reservierungen über die Resmio-API.
Platzhalter für echte API-Integration.
"""

import os
import requests
from typing import Optional

RESMIO_API_KEY = os.getenv("RESMIO_API_KEY")
RESMIO_BASE_URL = "https://api.resmio.com/v1/"

class ResmioClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or RESMIO_API_KEY
        self.base_url = RESMIO_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def create_reservation(self, data):
        # TODO: Felder anpassen
        url = self.base_url + "reservations"
        resp = requests.post(url, json=data, headers=self.headers)
        return resp.json()

    def get_reservation(self, reservation_id):
        url = self.base_url + f"reservations/{reservation_id}"
        resp = requests.get(url, headers=self.headers)
        return resp.json()

    def update_reservation(self, reservation_id, data):
        url = self.base_url + f"reservations/{reservation_id}"
        resp = requests.patch(url, json=data, headers=self.headers)
        return resp.json()

    def delete_reservation(self, reservation_id):
        url = self.base_url + f"reservations/{reservation_id}"
        resp = requests.delete(url, headers=self.headers)
        return resp.status_code == 204
