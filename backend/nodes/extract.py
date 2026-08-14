# backend/nodes/extract.py
import json
import re
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState
from backend.logger import create_log_entry

load_dotenv()

def _safe_parse_claims(raw_output: str):
    array_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    if not array_match:
        return None
    json_str = re.sub(r',\s*([}\]])', r'\1', array_match.group(0))
    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None

def extract_claims(state: GraphState) -> dict:
    print("---NODE: EXTRACT---")
    api_key = state.get("groq_api_key")
    model_name = "openai/gpt-oss-20b"
    llm = ChatGroq(model=model_name, temperature=0, max_tokens=3000, groq_api_key=api_key)

    with open("backend/prompts/extract_prompt.txt", "r") as f:
        prompt_template = f.read()

    duration = state.get("lecture_duration", 30)
    min_claims = max(6, duration // 3)
    max_claims = min(20, max(min_claims + 4, duration // 2))

    prompt = prompt_template.replace("{topic}", state["topic"])
    prompt = prompt.replace("{search_results}", state["search_results"])
    prompt = prompt.replace("{min_claims}", str(min_claims))
    prompt = prompt.replace("{max_claims}", str(max_claims))

    response = llm.invoke(prompt)
    claims = _safe_parse_claims(response.content)

    if not claims:
        print(f"Claim parsing failed. Raw output: {response.content[:300]}")
        claims = ["Error parsing claims."]

    log_entry = create_log_entry(
        node_name="extract",
        inputs={"search_results_length": len(state["search_results"]), "min_claims": min_claims, "max_claims": max_claims},
        prompt=prompt,
        output=claims,
        model_name=model_name
    )

    return {"extracted_claims": claims, "logs": [log_entry]}
