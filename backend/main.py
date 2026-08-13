import os
import uuid
from fastapi import FastAPI, Body, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from backend.graph import app_graph
from backend.deck_style import build_deck

load_dotenv()

app = FastAPI(title="Lecture Assistant Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lecture-assistant-orpin.vercel.app", 
        "http://localhost:5173",
        "http://localhost:3000"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
def read_root():
    return {"status": "Backend is running!"}

@app.post("/start-graph")
def start_graph(request: Request, payload: dict = Body(...)):
    try:
        topic = payload.get("topic", "Introduction to AI")
        duration = payload.get("lecture_duration", 30)
        
        groq_api_key = request.headers.get("X-Groq-Key")
        
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "topic": topic,
            "lecture_duration": duration,
            "logs": [],
            "groq_api_key": groq_api_key
        }
        
        app_graph.invoke(initial_state, config=config)
        current_state = app_graph.get_state(config)
        
        return {
            "thread_id": thread_id,
            "message": "Graph paused for HITL 1 (Plan Review).",
            "draft_plan": current_state.values.get("draft_plan", ""),
            "extracted_claims": current_state.values.get("extracted_claims", [])
        }
    except Exception as e:
        print(f"ERROR in start_graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/resume-graph")
def resume_graph(request: Request, payload: dict = Body(...)):
    try:
        thread_id = payload.get("thread_id")
        config = {"configurable": {"thread_id": thread_id}}
        
        if "verified_claims" in payload:
            verified_claims = payload.get("verified_claims")
            app_graph.update_state(config, {"verified_claims": verified_claims})
            app_graph.invoke(None, config=config)
            current_state = app_graph.get_state(config)
            return {
                "message": "Graph resumed and brief generated.",
                "final_brief": current_state.values.get("final_brief", {}),
                "logs": current_state.values.get("logs", [])
            }
        else:
            human_decision = payload.get("human_decision", "Approve")
            custom_text = payload.get("custom_text", "")
            
            app_graph.update_state(config, {
                "human_decision": human_decision,
                "custom_text": custom_text
            })
            
            app_graph.invoke(None, config=config)
            current_state = app_graph.get_state(config)
            
            if human_decision == "Approve":
                return {
                    "message": "Graph refined and paused for HITL 2 (Fact Verification).",
                    "refined_plan": current_state.values.get("draft_plan", ""),
                    "extracted_claims": current_state.values.get("extracted_claims", []),
                    "next_stage": "review_2"
                }
            else:
                return {
                    "message": "Plan reworked. Paused for HITL 1 review again.",
                    "draft_plan": current_state.values.get("draft_plan", ""),
                    "extracted_claims": current_state.values.get("extracted_claims", []),
                    "next_stage": "review_1"
                }
    except Exception as e:
        print(f"ERROR in resume_graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-pptx")
def download_pptx(payload: dict = Body(...)):
    try:
        thread_id = payload.get("thread_id")
        config = {"configurable": {"thread_id": thread_id}}

        current_state = app_graph.get_state(config)
        slides_data = current_state.values.get("final_brief", {}).get("slides", [])

        file_path = build_deck(slides_data, out_path="lecture_slides_temp.pptx")

        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename="lecture_deck.pptx"
        )
    except Exception as e:
        print(f"ERROR in download_pptx: {e}")
        raise HTTPException(status_code=500, detail=str(e))
