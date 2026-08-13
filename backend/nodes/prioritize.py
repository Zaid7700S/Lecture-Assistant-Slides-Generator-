# backend/nodes/prioritize.py
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState
from backend.logger import create_log_entry

load_dotenv()

def prioritize_claims(state: GraphState) -> dict:
    print("---NODE: PRIORITIZE---")
    
    # Get API key from state
    api_key = state.get("groq_api_key")
    
    model_name = "openai/gpt-oss-20b"
    llm = ChatGroq(model=model_name, temperature=0, groq_api_key=api_key)
    
    with open("backend/prompts/prioritize_prompt.txt", "r") as f:
        prompt_template = f.read()
        
    claims_str = json.dumps(state["extracted_claims"], indent=2)
    prompt = prompt_template.replace("{claims}", claims_str)
    
    response = llm.invoke(prompt)
    cleaned_response = response.content.replace("```json", "").replace("```", "").strip()
    
    try:
        prioritized_claims = json.loads(cleaned_response)
        print(f"Prioritized {len(prioritized_claims)} claims.")
    except json.JSONDecodeError:
        prioritized_claims = state["extracted_claims"] # Fallback to original order
        
    log_entry = create_log_entry(
        node_name="prioritize",
        inputs={"claims_count": len(state["extracted_claims"])},
        prompt=prompt,
        output=prioritized_claims,
        model_name=model_name
    )
        
    return {"extracted_claims": prioritized_claims, "logs": [log_entry]}
