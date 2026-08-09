# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
# pyrefly: ignore [missing-import]
from src.agents.logistics import plan_logistics
# pyrefly: ignore [missing-import]
from src.schemas import TravelRequest, DestinationOutput, Recommendation, LogisticsOutput, Accommodation, DaySchedule

@patch('src.agents.logistics.call_llm')
def test_plan_logistics(mock_call_llm):
    mock_call_llm.return_value = LogisticsOutput(
        accommodations=[Accommodation(area="Marina", hotel_tier="luxury", estimated_nightly_cost_usd=300.0, nights=2, rationale="")],
        daily_schedule=[
            DaySchedule(day=1, theme="Beach", activities=["JBR Walk"], transport_modes=["Taxi"], estimated_travel_time_mins=20, notes="")
        ],
        transport_tips=[]
    )
    
    req = TravelRequest(destination="Dubai", duration_days=2, budget_usd=2000.0, preferences=[], avoidances=[], raw_input="")
    dest = DestinationOutput(recommendations=[
        Recommendation(name="JBR Walk", category="experience", neighborhood="Marina", estimated_duration_hours=2, crowd_level="medium", best_time_to_visit="Evening", estimated_cost_usd=0.0, priority="nice-to-have", description="")
    ], neighborhoods_summary={})
    
    result = plan_logistics(req, dest)
    assert len(result.accommodations) == 1
    assert result.accommodations[0].area == "Marina"
    assert len(result.daily_schedule) == 1
