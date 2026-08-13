# backend/nodes/input.py
from backend.state import GraphState

def read_user_prompt(state: GraphState) -> dict:
    print("---NODE: INPUT---")
    topic = state["topic"]
    duration = state["lecture_duration"]
    print(f"Topic: {topic}, Duration: {duration} mins")
    return {} # State is already set, nothing to update yet