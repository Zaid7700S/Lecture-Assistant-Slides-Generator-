# backend/graph.py
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from backend.state import GraphState
from backend.nodes.input import read_user_prompt
from backend.nodes.search import web_search
from backend.nodes.extract import extract_claims
from backend.nodes.prioritize import prioritize_claims
from backend.nodes.synthesize import synthesize_plan
from backend.nodes.review import present_to_human
from backend.nodes.refine import refine_plan
from backend.nodes.verify import verify_claims
from backend.nodes.brief import generate_brief

workflow = StateGraph(GraphState)

workflow.add_node("input", read_user_prompt)
workflow.add_node("search", web_search)
workflow.add_node("extract", extract_claims)
workflow.add_node("prioritize", prioritize_claims)
workflow.add_node("synthesize", synthesize_plan)
workflow.add_node("review", present_to_human)
workflow.add_node("refine", refine_plan)
workflow.add_node("verify", verify_claims)
workflow.add_node("brief", generate_brief)

workflow.set_entry_point("input")
workflow.add_edge("input", "search")
workflow.add_edge("search", "extract")
workflow.add_edge("extract", "prioritize")
workflow.add_edge("prioritize", "synthesize")
workflow.add_edge("synthesize", "review")
workflow.add_edge("review", "refine")

# CONDITIONAL EDGE: If user clicked "Rework", go back to Review (HITL 1). Otherwise, go to Verify (HITL 2).
def route_after_refine(state: GraphState) -> str:
    if state.get("human_decision") == "Approve":
        return "verify"
    return "review"

workflow.add_conditional_edges(
    "refine",
    route_after_refine,
    {
        "review": "review",
        "verify": "verify"
    }
)

workflow.add_edge("verify", "brief")
workflow.set_finish_point("brief")

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["review", "verify"])
