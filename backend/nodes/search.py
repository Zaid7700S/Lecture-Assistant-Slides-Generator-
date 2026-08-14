# backend/nodes/search.py
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from langchain_community.tools import DuckDuckGoSearchResults
from backend.state import GraphState

def _fetch_page_text(url: str, max_chars: int = 2000) -> str:
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())[:max_chars]
    except Exception:
        return ""

def web_search(state: GraphState) -> dict:
    print("---NODE: SEARCH---")
    topic = state["topic"]
    search = DuckDuckGoSearchResults(output_format="list")

    # Multiple angles so one narrow page can't dominate the source pool
    query_variants = [
        topic,
        f"{topic} overview",
        f"{topic} timeline key events",
        f"{topic} major eras periods",
    ]

    seen_domains = set()
    selected = []
    MAX_SOURCES = 6

    for q in query_variants:
        if len(selected) >= MAX_SOURCES:
            break
        try:
            raw = search.invoke(q)
        except Exception as e:
            print(f"Search variant '{q}' failed: {e}")
            continue
        for r in raw:
            url = r.get("link", "")
            domain = urlparse(url).netloc
            if not domain or domain in seen_domains:
                continue  # cap: 1 page per domain, no source can flood the pool
            seen_domains.add(domain)
            selected.append(r)
            if len(selected) >= MAX_SOURCES:
                break

    if not selected:
        return {"search_results": (
            f"No usable search results were found. Generate claims based on your "
            f"internal knowledge of {topic}, and use '[Source: General Knowledge - N/A]' as the citation."
        )}

    blocks = []
    for r in selected:
        title, url = r.get("title", ""), r.get("link", "")
        page_text = _fetch_page_text(url)
        body = page_text if len(page_text) > len(r.get("snippet", "")) else r.get("snippet", "")
        blocks.append(f"Title: {title}\nURL: {url}\nContent: {body}")

    print(f"Gathered {len(selected)} sources across {len(seen_domains)} domains.")
    return {"search_results": "\n\n".join(blocks)}
