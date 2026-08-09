# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, DestinationOutput, LogisticsOutput, BudgetOutput, ItineraryDetail, ReviewResult
from .utils import call_llm
from pydantic import BaseModel
from typing import List

class ActivityDraft(BaseModel):
    name: str
    cost_usd: float

class DayDraft(BaseModel):
    activities: List[ActivityDraft]

class DraftItinerary(BaseModel):
    duration_days: int
    days: List[DayDraft]

def parse_request(raw_input: str) -> TravelRequest:
    prompt = "You are an orchestrator agent. Extract travel request details."
    user_input = f"Extract travel request details from this input:\n{raw_input}"
    return call_llm(prompt=prompt, user_input=user_input, response_model=TravelRequest)

def merge_draft(
    request: TravelRequest, 
    destination: DestinationOutput, 
    logistics: LogisticsOutput, 
    budget: BudgetOutput
) -> DraftItinerary:
    days = []
    for d_sched in logistics.daily_schedule:
        activities = []
        for act_name in d_sched.activities:
            cost = 0.0
            for rec in destination.recommendations:
                if rec.name == act_name:
                    cost = rec.estimated_cost_usd
                    break
            activities.append(ActivityDraft(name=act_name, cost_usd=cost))
        days.append(DayDraft(activities=activities))
    return DraftItinerary(duration_days=request.duration_days, days=days)

def finalize_plan(draft: DraftItinerary, review_result: ReviewResult) -> ItineraryDetail:
    prompt = "You are an orchestrator agent. Finalize the itinerary."
    user_input = (
        "Finalize the itinerary by applying review suggestions:\n"
        f"Draft: {draft.model_dump_json()}\n"
        f"Review: {review_result.model_dump_json()}\n"
    )
    return call_llm(prompt=prompt, user_input=user_input, response_model=ItineraryDetail)
