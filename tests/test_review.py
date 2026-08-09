import pytest
from unittest.mock import patch
from src.agents.review import review_itinerary
from src.schemas import TravelRequest, ReviewResult, ItineraryDetail, BudgetOutput

@patch('src.agents.review.call_llm')
def test_review_itinerary(mock_call_llm):
    mock_call_llm.return_value = ReviewResult(
        approved=True,
        overall_score=0.9,
        issues=[],
        suggestions=[],
        verdict="Looks great!"
    )
    
    req = TravelRequest(destination="Dubai", duration_days=2, budget_usd=1000.0, preferences=[], avoidances=[], raw_input="")
    
    draft = ItineraryDetail(
        destination="Dubai",
        duration_days=2,
        total_estimated_cost_usd=800.0,
        budget_limit_usd=1000.0,
        days=[],
        accommodations=[],
        budget_breakdown=BudgetOutput(total_estimated_usd=800.0, budget_limit_usd=1000.0, remaining_usd=200.0, breakdown=[], alerts=[], is_within_budget=True),
        review=ReviewResult(approved=False, overall_score=0.0, issues=[], suggestions=[], verdict="")
    )
    
    result = review_itinerary(draft, req)
    assert result.approved == True
    assert result.overall_score == 0.9
