# src/resmio/resmio_client.py

import os
import requests
from loguru import logger
# korrigierter Import aus Deinem src-Paket
from src.config.config import Config

class ResMioClient:
    BASE_URL = "https://api.resmio.net/v1"

    def __init__(self):
        self.api_key = Config.RESMIO_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_reservation(self, parsed):
        """
        Erwartet ein Dict mit keys: persons, date, time, occasion, special_request, children, terrace
        """
        payload = {
            "covers": parsed["persons"],
            "datetime": f"{parsed['date']}T{parsed['time']}:00",
            "metadata": {
                "occasion": parsed.get("occasion"),
                "special_request": parsed.get("special_request"),
                "children": parsed.get("children"),
                "terrace": parsed.get("terrace"),
            }
        }
        try:
            resp = requests.post(
                f"{self.BASE_URL}/reservations",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            logger.info(f"ResMio: Reservation successful: {resp.json()}")
            return resp.json()
        except Exception as e:
            logger.error(f"ResMio: Fehler bei Reservierung: {e!r}")
            return {"error": str(e)}
