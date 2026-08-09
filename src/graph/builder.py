# pyright: ignore [reportMissingImports]
from langgraph.graph import StateGraph, END
# pyrefly: ignore [missing-import]
from src.graph.state import PlannerState
# pyrefly: ignore [missing-import]
from src.graph.nodes import (
    parse_request_node, destination_node, logistics_node, budget_node, merge_node, review_node, finalize_node, retry_decision, retry_fan_out
)

def build_planner_graph():
    builder = StateGraph(PlannerState)
    builder.add_node("parse_request", parse_request_node)
    builder.add_node("destination", destination_node)
    builder.add_node("logistics", logistics_node)
    builder.add_node("budget", budget_node)
    builder.add_node("merge", merge_node)
    builder.add_node("review", review_node)
    builder.add_node("finalize", finalize_node)
    
    builder.set_entry_point("parse_request")
    builder.add_edge("parse_request", "destination")
    builder.add_edge("destination", "logistics")
    builder.add_edge("logistics", "budget")
    builder.add_edge("budget", "merge")
    builder.add_edge("merge", "review")
    
    builder.add_conditional_edges("review", retry_decision, {"retry": "parse_request", "finalize": "finalize"})
    builder.add_edge("finalize", END)
    
    return builder.compile()
