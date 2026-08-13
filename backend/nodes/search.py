# backend/nodes/search.py
from langchain_community.tools import DuckDuckGoSearchResults
from backend.state import GraphState

def web_search(state: GraphState) -> dict:
    print("---NODE: SEARCH---")
    topic = state["topic"]
    
    # This tool returns formatted strings with URLs: [snippet: ...] (title: ... - link: ...)
    search = DuckDuckGoSearchResults()
    results = search.invoke(topic)
    
    print(f"Found structured search results with links.")
    return {"search_results": results}