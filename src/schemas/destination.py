from pydantic import BaseModel
from typing import Optional

class Recommendation(BaseModel):
    name: str
    category: str
    neighborhood: str
    estimated_duration_hours: int
    crowd_level: str
    best_time_to_visit: str
    estimated_cost_usd: float
    priority: str
    description: str

class DestinationOutput(BaseModel):
    recommendations: list[Recommendation]
    neighborhoods_summary: dict
