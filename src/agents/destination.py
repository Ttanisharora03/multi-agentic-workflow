# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, DestinationOutput
from .utils import call_llm
# pyright: ignore [reportMissingImports]
from src.tools.search import search_dubai_info

def research_destinations(request: TravelRequest, fresh: bool = False, plan_id: str = "unknown") -> DestinationOutput:
    prompt = "You are a destination research agent."
    search_query = f"{', '.join(request.preferences)} in {request.destination}"
    live_info = search_dubai_info(search_query)
    user_input = (
        f"Destination: {request.destination}\n"
        f"Duration: {request.duration_days} days\n"
        f"Preferences: {', '.join(request.preferences)}\n"
        f"Avoidances: {', '.join(request.avoidances)}\n"
        f"Travelers: {request.traveler_count}\n\n"
        f"--- LIVE SEARCH DATA FOR CONTEXT ---\n{live_info}\n------------------------------------"
    )
    return call_llm(
        prompt=prompt,
        user_input=user_input,
        response_model=DestinationOutput,
        model="groq/llama-3.3-70b-versatile",
        agent_name="destination",
        fresh=fresh,
        plan_id=plan_id
    )
