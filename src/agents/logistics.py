# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, DestinationOutput, LogisticsOutput
from .utils import call_llm

def plan_logistics(request: TravelRequest, destination: DestinationOutput, fresh: bool = False, plan_id: str = "unknown") -> LogisticsOutput:
    prompt = "You are a logistics agent."
    user_input = f"Request: {request.model_dump_json()}\nDest: {destination.model_dump_json()}"
    return call_llm(prompt=prompt, user_input=user_input, response_model=LogisticsOutput, agent_name="logistics", fresh=fresh, plan_id=plan_id)
