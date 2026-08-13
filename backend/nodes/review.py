# backend/nodes/review.py
from backend.state import GraphState

def present_to_human(state: GraphState) -> dict:
    print("---NODE: REVIEW (HITL GATE)---")
    # In LangGraph, execution pauses *before* this node if we set interrupt_before.
    # When resumed, it will execute this node.
    # We don't need to do anything here except pass the state along.
    return {}