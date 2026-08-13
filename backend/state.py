# backend/state.py
from typing import TypedDict, List, Optional, Annotated
import operator

class GraphState(TypedDict):
    topic: str
    lecture_duration: int
    search_results: str
    extracted_claims: Annotated[list[str], operator.add]
    draft_plan: str
    human_decision: str
    custom_text: str               # <-- ADD THIS
    verified_claims: list[str]     # <-- ADD THIS
    final_brief: Optional[dict]
    logs: Annotated[list[dict], operator.add] # <-- ADD THIS
    groq_api_key: str