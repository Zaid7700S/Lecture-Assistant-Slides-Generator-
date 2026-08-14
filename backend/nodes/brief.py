# backend/nodes/brief.py
import json
import re
import math
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.state import GraphState
from backend.logger import create_log_entry

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"

FIXED_SLIDE_ROLES = ["Title", "Introduction", "Key Findings", "Risks", "Summary", "Further Reading"]
FIXED_SLIDE_COUNT = len(FIXED_SLIDE_ROLES)
BATCH_SIZE = 4

def compute_target_slide_count(duration: int) -> int:
    n = round(duration)
    return max(10, min(40, n))

def safe_parse_json(raw_output: str):
    json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
    if not json_match:
        return None
    json_str = json_match.group(0)
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def _fit_topics_to_length(topics, n, topic_label):
    topics = list(topics or [])[:n]
    while len(topics) < n:
        idx = len(topics) + 1
        topics.append({
            "title": f"{topic_label}: Additional Perspective {idx}",
            "subtitle": ""
        })
    return topics

def _ensure_custom_coverage(topics, custom_text, n):
    """Guarantee the human's requested addition survives the outline stage,
    even if the LLM ignored the REQUESTED ADDITIONS instruction."""
    if not custom_text or not custom_text.strip():
        return topics

    needle = custom_text.strip().lower()[:40]
    covered = any(
        needle in (t.get("title", "") + " " + t.get("subtitle", "")).lower()
        for t in topics
    )
    if covered:
        return topics

    print("Custom addition not found in outline output — injecting it manually.")
    injected = {
        "title": custom_text.strip()[:60],
        "subtitle": "Requested addition",
    }
    # Replace the last topic rather than exceeding content_slide_count
    return topics[:max(n - 1, 0)] + [injected]

def _fallback_content_slide(topic):
    return {
        "title": topic.get("title", "Untitled"),
        "subtitle": topic.get("subtitle", ""),
        "bullets": [
            f"Content for this slide could not be generated automatically and needs a manual pass on '{topic.get('title', '')}'."
        ],
    }

def _fallback_special_slides(topic):
    return [
        {"title": "Title", "subtitle": topic, "bullets": []},
        {"title": "Introduction", "subtitle": "", "bullets": [f"This lecture introduces {topic} and its key ideas."]},
        {"title": "Key Findings", "subtitle": "", "bullets": [f"Findings for {topic} could not be generated automatically."]},
        {"title": "Risks", "subtitle": "", "bullets": [
            "Risk content could not be generated automatically.",
            "Please review this section manually.",
            "Consider re-running generation for this deck.",
        ]},
        {"title": "Summary", "subtitle": "", "bullets": [f"Summary for {topic} could not be generated automatically."]},
        {"title": "Further Reading", "subtitle": "", "bullets": ["Further reading could not be generated automatically."]},
    ]

def generate_brief(state: GraphState) -> dict:
    print("---NODE: FINAL BRIEF---")
    api_key = state.get("groq_api_key")

    with open("backend/prompts/outline_prompt.txt", "r") as f:
        outline_template = f.read()
    with open("backend/prompts/content_batch_prompt.txt", "r") as f:
        batch_template = f.read()
    with open("backend/prompts/special_slides_prompt.txt", "r") as f:
        special_template = f.read()

    topic = state["topic"]
    duration = state["lecture_duration"]
    claims_to_use = state.get("verified_claims", state["extracted_claims"])
    claims_str = json.dumps(claims_to_use, indent=2)
    refined_plan = state["draft_plan"]

    logs = []
    target_total = compute_target_slide_count(duration)
    content_slide_count = max(4, target_total - FIXED_SLIDE_COUNT)
    print(f"Target total slides: {target_total} ({content_slide_count} content + {FIXED_SLIDE_COUNT} fixed)")

    outline_llm = ChatGroq(model=MODEL_NAME, temperature=0,
                            response_format={"type": "json_object"}, max_tokens=2500, groq_api_key=api_key)

    outline_prompt = outline_template.replace("{content_slide_count}", str(content_slide_count))
    outline_prompt = outline_prompt.replace("{refined_plan}", refined_plan)
    outline_prompt = outline_prompt.replace("{extracted_claims}", claims_str)
    outline_prompt = outline_prompt.replace("{custom_additions}", state.get("custom_text") or "None")  # NEW

    outline_response = outline_llm.invoke(outline_prompt)
    outline_json = safe_parse_json(outline_response.content) or {}
    topics = _fit_topics_to_length(outline_json.get("topics", []), content_slide_count, topic)
    topics = _ensure_custom_coverage(topics, state.get("custom_text"), content_slide_count)  # NEW

    logs.append(create_log_entry(
        node_name="brief.outline",
        inputs={"content_slide_count": content_slide_count},
        prompt=outline_prompt,
        output=topics,
        model_name=MODEL_NAME,
    ))

    content_llm = ChatGroq(model=MODEL_NAME, temperature=0,
                            response_format={"type": "json_object"}, max_tokens=2200, groq_api_key=api_key)

    content_slides = []
    for i in range(0, len(topics), BATCH_SIZE):
        batch = topics[i:i + BATCH_SIZE]

        batch_prompt = batch_template.replace("{slide_count}", str(len(batch)))
        batch_prompt = batch_prompt.replace("{topics}", json.dumps(batch, indent=2))
        batch_prompt = batch_prompt.replace("{claims}", claims_str)
        batch_prompt = batch_prompt.replace("{refined_plan}", refined_plan)

        try:
            batch_response = content_llm.invoke(batch_prompt)
            batch_json = safe_parse_json(batch_response.content) or {}
            batch_slides = batch_json.get("slides", [])
        except Exception as e:
            print(f"Batch {i // BATCH_SIZE + 1} failed: {e}")
            batch_slides = []

        fixed_batch = []
        for j, t in enumerate(batch):
            if j < len(batch_slides) and batch_slides[j].get("bullets"):
                fixed_batch.append(batch_slides[j])
            else:
                fixed_batch.append(_fallback_content_slide(t))
        content_slides.extend(fixed_batch)

        logs.append(create_log_entry(
            node_name=f"brief.batch_{i // BATCH_SIZE + 1}",
            inputs={"topics": batch},
            prompt=batch_prompt,
            output=fixed_batch,
            model_name=MODEL_NAME,
        ))

    special_llm = ChatGroq(model=MODEL_NAME, temperature=0,
                            response_format={"type": "json_object"}, max_tokens=2500, groq_api_key=api_key)

    special_prompt = special_template.replace("{topic}", topic)
    special_prompt = special_prompt.replace("{refined_plan}", refined_plan)
    special_prompt = special_prompt.replace("{extracted_claims}", claims_str)

    special_response = special_llm.invoke(special_prompt)
    special_json = safe_parse_json(special_response.content) or {}
    special_slides = special_json.get("slides", [])

    if len(special_slides) != FIXED_SLIDE_COUNT:
        print(f"Special slides count mismatch ({len(special_slides)}), using fallback.")
        special_slides = _fallback_special_slides(topic)

    logs.append(create_log_entry(
        node_name="brief.special",
        inputs={"topic": topic},
        prompt=special_prompt,
        output=special_slides,
        model_name=MODEL_NAME,
    ))

    title_slide, intro_slide, findings_slide, risks_slide, summary_slide, reading_slide = special_slides

    all_slides = [title_slide, intro_slide, *content_slides,
                  findings_slide, risks_slide, summary_slide, reading_slide]

    slide_deck = {"slides": all_slides}
    print(f"Generated {len(all_slides)} slides (target was {target_total}).")

    return {"final_brief": slide_deck, "logs": logs}
