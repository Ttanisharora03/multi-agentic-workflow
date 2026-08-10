# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, DestinationOutput, LogisticsOutput, BudgetOutput
from .utils import call_llm

def analyze_budget(request: TravelRequest, destination: DestinationOutput, logistics: LogisticsOutput, fresh: bool = False, plan_id: str = "unknown") -> BudgetOutput:
    prompt = "You are a budget analysis agent."
    user_input = f"Request: {request.model_dump_json()}\nDest: {destination.model_dump_json()}\nLogistics: {logistics.model_dump_json()}"
    return call_llm(prompt=prompt, user_input=user_input, response_model=BudgetOutput, agent_name="budget", fresh=fresh, plan_id=plan_id)
