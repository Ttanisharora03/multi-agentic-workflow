import pytest
from unittest.mock import patch
from src.agents.orchestrator import parse_request, merge_draft, DraftItinerary
from src.schemas import TravelRequest, DestinationOutput, LogisticsOutput, BudgetOutput, ReviewResult, Recommendation, Accommodation, DaySchedule, BudgetBreakdown

@patch('src.agents.orchestrator.call_llm')
def test_parse_request(mock_call_llm):
    mock_call_llm.return_value = TravelRequest(
        destination="Dubai",
        duration_days=3,
        budget_usd=1000.0,
        preferences=["food"],
        avoidances=["crowds"],
        traveler_count=2,
        raw_input="Plan a 3-day trip to Dubai for 2 people. 1k budget, love food, hate crowds."
    )
    
    req = parse_request("Plan a 3-day trip to Dubai for 2 people. 1k budget, love food, hate crowds.")
    assert req.destination == "Dubai"
    assert req.budget_usd == 1000.0

def test_merge_draft():
    req = TravelRequest(destination="Dubai", duration_days=1, budget_usd=500.0, preferences=[], avoidances=[], raw_input="")
    dest = DestinationOutput(recommendations=[
        Recommendation(name="Burj Khalifa", category="landmark", neighborhood="Downtown", estimated_duration_hours=2, crowd_level="high", best_time_to_visit="Morning", estimated_cost_usd=50.0, priority="must-do", description="")
    ], neighborhoods_summary={})
    
    log = LogisticsOutput(
        accommodations=[Accommodation(area="Downtown", hotel_tier="budget", estimated_nightly_cost_usd=100.0, nights=1, rationale="")],
        daily_schedule=[DaySchedule(day=1, theme="City Center", activities=["Burj Khalifa"], transport_modes=["Metro"], estimated_travel_time_mins=30, notes="")],
        transport_tips=[]
    )
    
    bud = BudgetOutput(total_estimated_usd=150.0, budget_limit_usd=500.0, remaining_usd=350.0, breakdown=[], alerts=[], is_within_budget=True)
    
    draft = merge_draft(req, dest, log, bud)
    assert draft.duration_days == 1
    assert len(draft.days) == 1
    assert draft.days[0].activities[0].name == "Burj Khalifa"
    assert draft.days[0].activities[0].cost_usd == 50.0
