# pyright: ignore [reportMissingImports]
from src.graph.state import PlannerState
# pyright: ignore [reportMissingImports]
from src.agents import orchestrator, destination, logistics, budget, review
from typing import cast
# pyright: ignore [reportMissingImports]
from src.schemas import TravelRequest, DestinationOutput, LogisticsOutput, BudgetOutput, ReviewResult, ItineraryDetail

def parse_request_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        req = orchestrator.parse_request(state.get("raw_input", ""))
        return {"travel_request": req}
    except Exception as e:
        return {"errors": [f"parse_request error: {str(e)}"]}

def destination_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        dest = destination.research_destinations(cast(TravelRequest, state["travel_request"]))
        return {"destination_output": dest}
    except Exception as e:
        return {"errors": [f"destination_node error: {str(e)}"]}

def logistics_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        log = logistics.plan_logistics(
            cast(TravelRequest, state["travel_request"]),
            cast(DestinationOutput, state["destination_output"])
        )
        return {"logistics_output": log}
    except Exception as e:
        return {"errors": [f"logistics_node error: {str(e)}"]}

def budget_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        bud = budget.analyze_budget(
            cast(TravelRequest, state["travel_request"]),
            cast(DestinationOutput, state["destination_output"]),
            cast(LogisticsOutput, state["logistics_output"])
        )
        return {"budget_output": bud}
    except Exception as e:
        return {"errors": [f"budget_node error: {str(e)}"]}

def merge_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        draft = orchestrator.merge_draft(
            cast(TravelRequest, state["travel_request"]),
            cast(DestinationOutput, state["destination_output"]),
            cast(LogisticsOutput, state["logistics_output"]),
            cast(BudgetOutput, state["budget_output"])
        )
        return {"draft_itinerary": draft.model_dump()}
    except Exception as e:
        return {"errors": [f"merge_node error: {str(e)}"]}

def review_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        draft_obj = orchestrator.DraftItinerary(**cast(dict, state["draft_itinerary"]))
        res = review.review_itinerary(draft_obj, cast(TravelRequest, state["travel_request"]))
        retry_count = state.get("retry_count", 0) + 1
        return {"review_result": res, "retry_count": retry_count}
    except Exception as e:
        return {"errors": [f"review_node error: {str(e)}"]}

def finalize_node(state: PlannerState) -> dict:
    if state.get("errors"): return {}
    try:
        draft_obj = orchestrator.DraftItinerary(**cast(dict, state["draft_itinerary"]))
        final = orchestrator.finalize_plan(draft_obj, cast(ReviewResult, state["review_result"]))
        return {"final_itinerary": final.model_dump()}
    except Exception as e:
        return {"errors": [f"finalize_node error: {str(e)}"]}

def retry_decision(state: PlannerState) -> str:
    if "errors" in state and state["errors"]:
        return "finalize"
    
    res = state.get("review_result")
    if res and not res.approved and state.get("retry_count", 0) < 3:
        return "retry"
    return "finalize"

def retry_fan_out(state: PlannerState) -> dict:
    return {}
