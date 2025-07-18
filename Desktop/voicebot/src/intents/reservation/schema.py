from pydantic import BaseModel
from typing import Optional

class ReservationRequest(BaseModel):
    name: Optional[str]
    date: Optional[str]  # ISO8601
    time: Optional[str]  # HH:MM
    persons: Optional[int]
    occasion: Optional[str]
    group_size: Optional[int]
    children: Optional[bool]
    pets: Optional[bool]
    wheelchair: Optional[bool]
    terrace: Optional[bool]
    special_request: Optional[str]
