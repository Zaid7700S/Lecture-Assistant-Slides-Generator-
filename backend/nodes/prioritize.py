# backend/nodes/prioritize.py
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState

load_dotenv()

def prioritize_claims(state: GraphState) -> dict:
    print("---NODE: PRIORITIZE---")
    
    # Use the basic/light model for this task
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    
    with open("backend/prompts/prioritize_prompt.txt", "r") as f:
        prompt_template = f.read()
        
    claims_str = json.dumps(state["extracted_claims"], indent=2)
    prompt = prompt_template.format(claims=claims_str)
    
    response = llm.invoke(prompt)
    cleaned_response = response.content.replace("```json", "").replace("```", "").strip()
    
    try:
        prioritized_claims = json.loads(cleaned_response)
        print(f"Prioritized {len(prioritized_claims)} claims.")
    except json.JSONDecodeError:
        prioritized_claims = state["extracted_claims"] # Fallback to original order
        
    # Overwrite the extracted_claims with the prioritized list
    return {"extracted_claims": prioritized_claims}