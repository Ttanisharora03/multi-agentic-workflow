# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, ReviewResult
# pyrefly: ignore [missing-import]
from src.agents.orchestrator import DraftItinerary
from .utils import call_llm

def review_itinerary(draft: DraftItinerary, request: TravelRequest, fresh: bool = False, plan_id: str = "unknown") -> ReviewResult:
    prompt = "You are a review agent."
    user_input = f"Draft: {draft.model_dump_json()}\nRequest: {request.model_dump_json()}"
    return call_llm(prompt=prompt, user_input=user_input, response_model=ReviewResult, agent_name="review", fresh=fresh, plan_id=plan_id)
