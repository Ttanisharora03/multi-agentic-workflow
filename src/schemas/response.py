from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from .budget import BudgetOutput
from .review import ReviewResult

class ActivityDetail(BaseModel):
    name: str = Field(description="Name of the activity or place")
    duration: str = Field(description="Estimated duration (e.g., '2 hours')")
    cost: str = Field(description="Estimated cost in USD")
    notes: str = Field(description="Additional context or tips")

class DayDetail(BaseModel):
    day_number: int
    theme: str
    activities: List[ActivityDetail]
    transport_info: str = Field(description="How to get around on this day")

class ItineraryDetail(BaseModel):
    destination: str
    duration_days: int
    total_estimated_cost_usd: float
    budget_limit_usd: float
    days: List[DayDetail] = Field(default_factory=list)
    accommodations: List[Dict] = Field(default_factory=list)
    budget_breakdown: BudgetOutput
    review: Optional[ReviewResult] = None

class PlanResponse(BaseModel):
    plan_id: str
    status: Literal["completed", "failed", "partial"]
    itinerary: Optional[dict] = None
    budget_summary: Optional[BudgetOutput] = None
    review: Optional[ReviewResult] = None
    errors: list[str] = []
    processing_time_seconds: float
