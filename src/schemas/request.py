from pydantic import BaseModel
from typing import Optional

class TravelRequest(BaseModel):
    destination: Optional[str] = None
    duration_days: int
    budget_usd: float = 0.0
    preferences: list[str]
    avoidances: list[str]
    traveler_count: int = 1
    raw_input: Optional[str] = None

class PlanAPIRequest(BaseModel):
    query: str
    traveler_count: int = 1
