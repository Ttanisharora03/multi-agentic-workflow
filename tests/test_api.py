# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from src.main import app
# pyrefly: ignore [missing-import]
from src.schemas.review import ReviewResult

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_plan_invalid_input():
    response = client.post("/api/v1/plan", json={})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_plan_creation_and_retrieval(mocker):
    # We will mock the graph invocation so we don't call real LLMs in tests
    mock_graph = mocker.MagicMock()
    
    mock_result = {
        "final_itinerary": {
            "destination": "Dubai",
            "duration_days": 3,
            "total_estimated_cost_usd": 1500.0,
            "budget_limit_usd": 2000.0,
            "days": [],
            "accommodations": [],
            "budget_breakdown": {
                "total_estimated_usd": 1500.0,
                "budget_limit_usd": 2000.0,
                "remaining_usd": 500.0,
                "breakdown": [],
                "alerts": [],
                "is_within_budget": True
            },
            "review": {
                "approved": True,
                "overall_score": 1.0,
                "issues": [],
                "suggestions": [],
                "verdict": "Perfect"
            }
        },
        "review_result": ReviewResult(
                approved=True,
                overall_score=1.0,
                issues=[],
                suggestions=[],
                verdict="Perfect"
            ),
        "errors": []
    }
    
    mock_graph.invoke.return_value = mock_result
    
    # Patch the graph dependency
    # pyrefly: ignore [missing-import]
    from src.api.routes import get_graph_dependency
    app.dependency_overrides[get_graph_dependency] = lambda: mock_graph
    
    response = client.post("/api/v1/plan", json={"query": "Plan a 3 day trip to Dubai"})
    
    assert response.status_code == 200
    data = response.json()
    print("API Error:", data.get("errors"))
    assert data["status"] == "completed"
    assert "plan_id" in data
    assert data["itinerary"]["destination"] == "Dubai"
    
    plan_id = data["plan_id"]
    
    # Test retrieval
    get_response = client.get(f"/api/v1/plan/{plan_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["plan_id"] == plan_id
    assert get_data["status"] == "completed"

def test_timeout_handling(mocker):
    mock_graph = mocker.MagicMock()
    mock_graph.invoke.side_effect = TimeoutError("Simulated timeout")
    
    # pyrefly: ignore [missing-import]
    from src.api.routes import get_graph_dependency
    app.dependency_overrides[get_graph_dependency] = lambda: mock_graph
    
    response = client.post("/api/v1/plan", json={"query": "Plan a trip"})
    assert response.status_code == 504
    assert "Request timed out" in response.json()["detail"]

def test_plan_audio_transcription(mocker):
    # Mock graph
    mock_graph = mocker.MagicMock()
    mock_result = {
        "final_itinerary": {
            "destination": "Dubai",
            "duration_days": 3,
            "total_estimated_cost_usd": 1500.0,
            "budget_limit_usd": 2000.0,
            "days": [],
            "accommodations": [],
            "budget_breakdown": {
                "total_estimated_usd": 1500.0,
                "budget_limit_usd": 2000.0,
                "remaining_usd": 500.0,
                "breakdown": [],
                "alerts": [],
                "is_within_budget": True
            },
            "review": {
                "approved": True,
                "overall_score": 1.0,
                "issues": [],
                "suggestions": [],
                "verdict": "Perfect"
            }
        },
        "review_result": ReviewResult(
                approved=True,
                overall_score=1.0,
                issues=[],
                suggestions=[],
                verdict="Perfect"
            ),
        "errors": []
    }
    mock_graph.invoke.return_value = mock_result
    # pyrefly: ignore [missing-import]
    from src.api.routes import get_graph_dependency
    app.dependency_overrides[get_graph_dependency] = lambda: mock_graph
    
    # Mock audio transcribe
    mocker.patch("src.api.routes.transcribe_audio", return_value="Plan a fun trip to Dubai")
    
    # Create fake audio file
    file_content = b"fake audio content"
    files = {"file": ("test.mp3", file_content, "audio/mpeg")}
    
    response = client.post("/api/v1/plan/audio", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "plan_id" in data
    assert data["itinerary"]["destination"] == "Dubai"
