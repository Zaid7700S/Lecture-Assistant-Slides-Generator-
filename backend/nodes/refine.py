# backend/nodes/refine.py
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState
from backend.logger import create_log_entry

load_dotenv()

def refine_plan(state: GraphState) -> dict:
    print("---NODE: REFINE---")
    api_key = state.get("groq_api_key")
    model_name = "llama-3.3-70b-versatile"
    llm = ChatGroq(model=model_name, temperature=0, groq_api_key=api_key)
    
    with open("backend/prompts/refine_prompt.txt", "r") as f:
        prompt_template = f.read()
        
    prompt = prompt_template.replace("{draft_plan}", state["draft_plan"])
    prompt = prompt.replace("{human_decision}", state["human_decision"])
    prompt = prompt.replace("{custom_text}", state.get("custom_text", "None"))
    prompt = prompt.replace("{lecture_duration}", str(state["lecture_duration"]))
    
    response = llm.invoke(prompt)
    
    log_entry = create_log_entry(
        node_name="refine",
        inputs={"draft_plan": state["draft_plan"]},
        prompt=prompt,
        output=response.content,
        model_name=model_name,
        human_decision=state["human_decision"]
    )
    
    return {"draft_plan": response.content, "logs": [log_entry]}