# pyrefly: ignore [missing-import]
from src.graph.builder import build_planner_graph

_graph = None

def get_graph_dependency():
    global _graph
    if _graph is None:
        _graph = build_planner_graph()
    return _graph
