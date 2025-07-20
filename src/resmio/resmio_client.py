import requests
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from urllib.parse import urljoin

from config.config import Config

logger = logging.getLogger(__name__)

class ResMioClient:
    """Client for interacting with the Resmio API for restaurant reservations."""
    
    def __init__(self, api_key: str = None, location_id: str = None):
        """Initialize the Resmio client.
        
        Args:
            api_key: Resmio API key
            location_id: Resmio location ID
        """
        self.config = Config()
        self.api_key = api_key or self.config.RESMIO_API_KEY
        self.location_id = location_id or self.config.RESMIO_LOCATION_ID
        self.base_url = "https://api.resmio.com/v1/"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request to Resmio."""
        url = urljoin(self.base_url, endpoint)
        
        # Add location ID to query params if not already present
        if 'params' not in kwargs:
            kwargs['params'] = {}
        if 'location_id' not in kwargs['params'] and self.location_id:
            kwargs['params']['location_id'] = self.location_id
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Resmio API request failed: {e}")
            raise
    
    def create_reservation(
        self,
        customer_name: str,
        phone: str,
        covers: int,
        reservation_time: str,
        email: str = None,
        notes: str = None,
        table_id: str = None,
        custom_fields: Dict[str, Any] = None
    ) -> Dict:
        """Create a new reservation.
        
        Args:
            customer_name: Full name of the customer
            phone: Customer's phone number
            covers: Number of people
            reservation_time: Reservation time in ISO 8601 format
            email: Customer's email (optional)
            notes: Additional notes (optional)
            table_id: Specific table ID (optional)
            custom_fields: Additional custom fields (optional)
            
        Returns:
            Dictionary containing the reservation details
        """
        data = {
            "customer": {
                "name": customer_name,
                "phone": phone,
                "email": email
            },
            "covers": covers,
            "reservation_time": reservation_time,
            "status": "confirmed",
            "notes": notes,
            "table_id": table_id,
            "custom_fields": custom_fields or {}
        }
        
        # Remove None values
        if email is None:
            data["customer"].pop("email")
        if table_id is None:
            data.pop("table_id")
        if notes is None:
            data.pop("notes")
        
        return self._make_request("POST", "reservations", json=data)
    
    def check_availability(
        self,
        date: str,
        time: str,
        covers: int,
        duration: int = 120
    ) -> Dict:
        """Check table availability.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            covers: Number of people
            duration: Duration in minutes (default: 120)
            
        Returns:
            Dictionary with availability information
        """
        params = {
            "date": date,
            "time": time,
            "covers": covers,
            "duration": duration
        }
        
        return self._make_request("GET", "availability", params=params)
    
    def get_reservation(self, reservation_id: str) -> Dict:
        """Get reservation details by ID.
        
        Args:
            reservation_id: The reservation ID
            
        Returns:
            Dictionary with reservation details
        """
        return self._make_request("GET", f"reservations/{reservation_id}")
    
    def update_reservation(
        self,
        reservation_id: str,
        **updates
    ) -> Dict:
        """Update an existing reservation.
        
        Args:
            reservation_id: The reservation ID
            **updates: Fields to update (e.g., covers, reservation_time, notes)
            
        Returns:
            Dictionary with updated reservation details
        """
        return self._make_request(
            "PATCH", 
            f"reservations/{reservation_id}",
            json=updates
        )
    
    def cancel_reservation(self, reservation_id: str) -> Dict:
        """Cancel a reservation.
        
        Args:
            reservation_id: The reservation ID
            
        Returns:
            Confirmation of cancellation
        """
        return self._make_request(
            "POST",
            f"reservations/{reservation_id}/cancel"
        )

# Singleton instance
resmio_client = ResMioClient()
