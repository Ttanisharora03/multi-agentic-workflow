# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
# pyrefly: ignore [missing-import]
from src.agents.destination import research_destinations
# pyrefly: ignore [missing-import]
from src.schemas import TravelRequest, DestinationOutput, Recommendation

@patch('src.agents.destination.call_llm')
def test_research_destinations(mock_call_llm):
    mock_call_llm.return_value = DestinationOutput(
        recommendations=[
            Recommendation(
                name="Dubai Mall",
                category="experience",
                neighborhood="Downtown",
                estimated_duration_hours=4.0,
                crowd_level="high",
                best_time_to_visit="Morning",
                estimated_cost_usd=0.0,
                priority="must-do",
                description="Huge mall"
            )
        ],
        neighborhoods_summary={"Downtown": "Busy area"}
    )
    
    req = TravelRequest(
        destination="Dubai",
        duration_days=3,
        budget_usd=1000.0,
        preferences=["shopping"],
        avoidances=[],
        traveler_count=1,
        raw_input=""
    )
    
    result = research_destinations(req)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].name == "Dubai Mall"
