from typing import TypedDict, Optional, List, Dict, Any
# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, DestinationOutput, LogisticsOutput, BudgetOutput, ReviewResult

class PlannerState(TypedDict, total=False):
    raw_input: str
    travel_request: Optional[TravelRequest]
    destination_output: Optional[DestinationOutput]
    logistics_output: Optional[LogisticsOutput]
    budget_output: Optional[BudgetOutput]
    draft_itinerary: Optional[Dict[str, Any]]
    review_result: Optional[ReviewResult]
    final_itinerary: Optional[Dict[str, Any]]
    errors: List[str]
    retry_count: int
