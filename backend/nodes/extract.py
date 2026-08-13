# backend/nodes/extract.py
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState
from backend.logger import create_log_entry

load_dotenv()

def extract_claims(state: GraphState) -> dict:
    print("---NODE: EXTRACT---")
    api_key = state.get("groq_api_key")
    model_name = "openai/gpt-oss-20b"
    llm = ChatGroq(model=model_name, temperature=0, max_tokens=2000, groq_api_key=api_key)

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
    cleaned_response = response.content.replace("```json", "").replace("```", "").strip()

    try:
        claims = json.loads(cleaned_response)
    except json.JSONDecodeError:
        claims = ["Error parsing claims."]

    log_entry = create_log_entry(
        node_name="extract",
        inputs={"search_results_length": len(state["search_results"]), "min_claims": min_claims, "max_claims": max_claims},
        prompt=prompt,
        output=claims,
        model_name=model_name
    )

    return {"extracted_claims": claims, "logs": [log_entry]}