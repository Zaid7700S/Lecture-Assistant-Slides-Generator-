# backend/nodes/synthesize.py
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState
from backend.logger import create_log_entry

load_dotenv()

def synthesize_plan(state: GraphState) -> dict:
    print("---NODE: SYNTHESIZE---")
    api_key = state.get("groq_api_key")
    model_name = "llama-3.3-70b-versatile"
    llm = ChatGroq(model=model_name, temperature=0, groq_api_key=api_key)
    
    with open("backend/prompts/synthesize_prompt.txt", "r") as f:
        prompt_template = f.read()
        
    claims_str = json.dumps(state["extracted_claims"], indent=2)
    
    prompt = prompt_template.replace("{topic}", state["topic"])
    prompt = prompt.replace("{lecture_duration}", str(state["lecture_duration"]))
    prompt = prompt.replace("{prioritized_claims}", claims_str)
    
    response = llm.invoke(prompt)
    
    log_entry = create_log_entry(
        node_name="synthesize",
        inputs={"topic": state["topic"], "duration": state["lecture_duration"]},
        prompt=prompt,
        output=response.content,
        model_name=model_name
    )
    
    return {"draft_plan": response.content, "logs": [log_entry]}