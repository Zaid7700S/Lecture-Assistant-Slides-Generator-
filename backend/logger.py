# backend/logger.py
from datetime import datetime

def create_log_entry(node_name: str, inputs: any, prompt: str, output: any, model_name: str, human_decision: str = None):
    """Creates a standardized log dictionary for a graph node."""
    return {
        "timestamp": datetime.now().isoformat(),
        "node": node_name,
        "inputs": inputs,
        "prompt": prompt,
        "output": output,
        "model_settings": {
            "model": model_name,
            "temperature": 0,
            "seed": 42
        },
        "human_decision": human_decision
    }