from pydantic import BaseModel
from typing import Optional

class Accommodation(BaseModel):
    area: str
    hotel_tier: str
    estimated_nightly_cost_usd: float
    nights: int
    rationale: str

class DaySchedule(BaseModel):
    day: int
    theme: str
    activities: list[str]
    transport_modes: list[str]
    estimated_travel_time_mins: int
    notes: str

class LogisticsOutput(BaseModel):
    accommodations: list[Accommodation]
    daily_schedule: list[DaySchedule]
    transport_tips: list[str]
