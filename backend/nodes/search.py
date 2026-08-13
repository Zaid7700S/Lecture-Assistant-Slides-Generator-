# backend/nodes/search.py
from langchain_community.tools import DuckDuckGoSearchRun
from backend.state import GraphState

def web_search(state: GraphState) -> dict:
    print("---NODE: SEARCH---")
    topic = state["topic"]
    
    search = DuckDuckGoSearchRun()
    
    try:
        results = search.invoke(topic)
        print(f"Found {len(results)} characters of search results.")
    except Exception as e:
        print(f"DuckDuckGo Search failed on server: {e}")
        # Fallback so the graph doesn't crash on cloud environments
        results = f"Search API failed on the server. Please generate claims based on your internal knowledge of {topic}."
        
    return {"search_results": results}
