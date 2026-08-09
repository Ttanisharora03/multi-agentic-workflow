# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
# pyrefly: ignore [missing-import]
from src.agents.budget import analyze_budget
# pyrefly: ignore [missing-import]
from src.schemas import TravelRequest, DestinationOutput, Recommendation, LogisticsOutput, Accommodation, DaySchedule, BudgetOutput

@patch('src.agents.budget.call_llm')
def test_analyze_budget(mock_call_llm):
    mock_call_llm.return_value = BudgetOutput(
        total_estimated_usd=1200.0,
        budget_limit_usd=1000.0,
        remaining_usd=-200.0,
        breakdown=[],
        alerts=[],
        is_within_budget=False
    )
    
    req = TravelRequest(destination="Dubai", duration_days=2, budget_usd=1000.0, preferences=[], avoidances=[], raw_input="")
    dest = DestinationOutput(recommendations=[], neighborhoods_summary={})
    log = LogisticsOutput(accommodations=[], daily_schedule=[], transport_tips=[])
    
    result = analyze_budget(req, dest, log)
    assert result.is_within_budget == False
    assert result.total_estimated_usd == 1200.0
