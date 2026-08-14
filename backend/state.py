# backend/state.py
from typing import TypedDict, List, Optional, Annotated
import operator

class GraphState(TypedDict):
    topic: str
    lecture_duration: int
    search_results: str
    extracted_claims: list[str]        # CHANGED: no reducer — each node fully replaces this
    draft_plan: str
    human_decision: str
    custom_text: str
    verified_claims: list[str]
    final_brief: Optional[dict]
    logs: Annotated[list[dict], operator.add]   # unchanged — logs SHOULD accumulate
    groq_api_key: str
