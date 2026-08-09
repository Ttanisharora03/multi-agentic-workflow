# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
# pyrefly: ignore [missing-import]
from src.graph.builder import build_planner_graph
# pyrefly: ignore [missing-import]
from src.schemas import (
    TravelRequest, DestinationOutput, LogisticsOutput, BudgetOutput, ReviewResult
)

@pytest.fixture
def graph():
    return build_planner_graph()

@pytest.fixture
def sample_request():
    return TravelRequest(
        destination="Dubai",
        duration_days=3,
        budget_usd=2000.0,
        preferences=["food"],
        avoidances=["crowds"],
        traveler_count=2,
        raw_input="Plan a 3-day trip to Dubai for 2 people with $2000 budget."
    )

def test_happy_path(graph, sample_request, mocker):
    mocker.patch("src.agents.orchestrator.parse_request", return_value=sample_request)
    mocker.patch("src.agents.destination.research_destinations", return_value=DestinationOutput(recommendations=[], neighborhoods_summary={}))
    mocker.patch("src.agents.logistics.plan_logistics", return_value=LogisticsOutput(accommodations=[], daily_schedule=[], transport_tips=[]))
    mocker.patch("src.agents.budget.analyze_budget", return_value=BudgetOutput(total_estimated_usd=1500.0, budget_limit_usd=2000.0, remaining_usd=500.0, breakdown=[], alerts=[], is_within_budget=True))
    mocker.patch("src.graph.nodes.ItineraryDetail", return_value=MagicMock())
    mocker.patch("src.agents.orchestrator.DraftItinerary", return_value=MagicMock())
    
    mock_draft = MagicMock()
    mock_draft.model_dump.return_value = {"destination": "Dubai"}
    mocker.patch("src.agents.orchestrator.merge_draft", return_value=mock_draft)
    
    mocker.patch("src.agents.review.review_itinerary", return_value=ReviewResult(
        approved=True, overall_score=0.9, issues=[], suggestions=[], verdict="Looks good"
    ))
    
    mock_final = MagicMock()
    mock_final.model_dump.return_value = {"destination": "Dubai", "final": True}
    mocker.patch("src.agents.orchestrator.finalize_plan", return_value=mock_final)

    state = {"raw_input": "Plan a trip to Dubai", "retry_count": 0, "errors": []}
    result = graph.invoke(state)

    assert result["review_result"].approved is True
    assert result["final_itinerary"]["final"] is True
    assert len(result["errors"]) == 0

def test_retry_path(graph, sample_request, mocker):
    mocker.patch("src.agents.orchestrator.parse_request", return_value=sample_request)
    mocker.patch("src.agents.destination.research_destinations", return_value=DestinationOutput(recommendations=[], neighborhoods_summary={}))
    mocker.patch("src.agents.logistics.plan_logistics", return_value=LogisticsOutput(accommodations=[], daily_schedule=[], transport_tips=[]))
    mocker.patch("src.agents.budget.analyze_budget", return_value=BudgetOutput(total_estimated_usd=1500.0, budget_limit_usd=2000.0, remaining_usd=500.0, breakdown=[], alerts=[], is_within_budget=True))
    mocker.patch("src.graph.nodes.ItineraryDetail", return_value=MagicMock())
    mocker.patch("src.agents.orchestrator.DraftItinerary", return_value=MagicMock())
    
    mock_draft = MagicMock()
    mock_draft.model_dump.return_value = {"destination": "Dubai"}
    mocker.patch("src.agents.orchestrator.merge_draft", return_value=mock_draft)
    
    # First review fails, second review succeeds
    review_mock = mocker.patch("src.agents.review.review_itinerary", side_effect=[
        ReviewResult(approved=False, overall_score=0.5, issues=["Too expensive"], suggestions=[], verdict="Fail"),
        ReviewResult(approved=True, overall_score=0.9, issues=[], suggestions=[], verdict="Pass")
    ])
    
    mock_final = MagicMock()
    mock_final.model_dump.return_value = {"destination": "Dubai", "final": True}
    mocker.patch("src.agents.orchestrator.finalize_plan", return_value=mock_final)

    state = {"raw_input": "Plan a trip to Dubai", "retry_count": 0, "errors": []}
    result = graph.invoke(state)

    assert review_mock.call_count == 2
    assert result["retry_count"] == 2
    assert result["review_result"].approved is True

def test_max_retries(graph, sample_request, mocker):
    mocker.patch("src.agents.orchestrator.parse_request", return_value=sample_request)
    mocker.patch("src.agents.destination.research_destinations", return_value=DestinationOutput(recommendations=[], neighborhoods_summary={}))
    mocker.patch("src.agents.logistics.plan_logistics", return_value=LogisticsOutput(accommodations=[], daily_schedule=[], transport_tips=[]))
    mocker.patch("src.agents.budget.analyze_budget", return_value=BudgetOutput(total_estimated_usd=1500.0, budget_limit_usd=2000.0, remaining_usd=500.0, breakdown=[], alerts=[], is_within_budget=True))
    mocker.patch("src.graph.nodes.ItineraryDetail", return_value=MagicMock())
    mocker.patch("src.agents.orchestrator.DraftItinerary", return_value=MagicMock())
    
    mock_draft = MagicMock()
    mock_draft.model_dump.return_value = {"destination": "Dubai"}
    mocker.patch("src.agents.orchestrator.merge_draft", return_value=mock_draft)
    
    # Always fails
    review_mock = mocker.patch("src.agents.review.review_itinerary", return_value=ReviewResult(
        approved=False, overall_score=0.5, issues=["Always fails"], suggestions=[], verdict="Fail"
    ))
    
    mock_final = MagicMock()
    mock_final.model_dump.return_value = {"destination": "Dubai", "final": True}
    mocker.patch("src.agents.orchestrator.finalize_plan", return_value=mock_final)

    state = {"raw_input": "Plan a trip to Dubai", "retry_count": 0, "errors": []}
    result = graph.invoke(state)

    assert review_mock.call_count == 3  # Initial + 2 retries
    assert result["retry_count"] == 3
    assert result["review_result"].approved is False

def test_error_handling(graph, mocker):
    mocker.patch("src.agents.orchestrator.parse_request", side_effect=Exception("Parsing failed"))

    state = {"raw_input": "Plan a trip to Dubai", "retry_count": 0, "errors": []}
    result = graph.invoke(state)

    assert len(result["errors"]) > 0
    assert "parse_request error: Parsing failed" in result["errors"]

def test_state_integrity(graph, sample_request, mocker):
    mocker.patch("src.agents.orchestrator.parse_request", return_value=sample_request)
    mocker.patch("src.agents.destination.research_destinations", return_value=DestinationOutput(recommendations=[], neighborhoods_summary={}))
    mocker.patch("src.agents.logistics.plan_logistics", return_value=LogisticsOutput(accommodations=[], daily_schedule=[], transport_tips=[]))
    mocker.patch("src.agents.budget.analyze_budget", return_value=BudgetOutput(total_estimated_usd=1500.0, budget_limit_usd=2000.0, remaining_usd=500.0, breakdown=[], alerts=[], is_within_budget=True))
    mocker.patch("src.graph.nodes.ItineraryDetail", return_value=MagicMock())
    mocker.patch("src.agents.orchestrator.DraftItinerary", return_value=MagicMock())
    
    mock_draft = MagicMock()
    mock_draft.model_dump.return_value = {"destination": "Dubai"}
    mocker.patch("src.agents.orchestrator.merge_draft", return_value=mock_draft)
    
    mocker.patch("src.agents.review.review_itinerary", return_value=ReviewResult(
        approved=True, overall_score=0.9, issues=[], suggestions=[], verdict="Looks good"
    ))
    
    mock_final = MagicMock()
    mock_final.model_dump.return_value = {"destination": "Dubai", "final": True}
    mocker.patch("src.agents.orchestrator.finalize_plan", return_value=mock_final)

    state = {"raw_input": "Test Integrity", "retry_count": 0, "errors": []}
    result = graph.invoke(state)

    # Check state integrity
    assert "travel_request" in result
    assert "destination_output" in result
    assert "logistics_output" in result
    assert "budget_output" in result
    assert "draft_itinerary" in result
    assert "review_result" in result
    assert "final_itinerary" in result
