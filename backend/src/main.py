import asyncio
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage

from .config import AppConfig, load_config
from .orchestrator import build_graph
from .schemas import ChatRequest
from .streaming import stream_graph_events

# Load environment variables
load_dotenv()

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_PATH = BASE_DIR / "config.yaml"

# Initialize App
app = FastAPI(title="AI Troubleshooting Agent")

# Mount Static Files
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@lru_cache()
def get_config() -> AppConfig:
    """
    Cached configuration loader.
    """
    return load_config(str(CONFIG_PATH))


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-troubleshoot-agent"}


@app.get("/config")
def get_current_config(config: AppConfig = Depends(get_config)):
    """
    Returns the currently loaded configuration.
    Useful for verification.
    """
    return {
        "orchestrator_model": config.orchestrator_model,
        "sub_agents_count": len(config.sub_agents),
        "sub_agents": [agent.name for agent in config.sub_agents]
    }


@app.post("/chat")
async def chat(request: ChatRequest, config: AppConfig = Depends(get_config)):
    """
    Process a chat message through the LangGraph orchestrator with streaming.
    """
    
    # Check for overrides
    updated_kwargs = {}
    if request.model_name:
        updated_kwargs["orchestrator_model"] = request.model_name
    if request.model_provider:
        updated_kwargs["orchestrator_provider"] = request.model_provider
        
    if updated_kwargs:
        # Create a copy with updated fields if overrides exist
        # Using model_copy(update=...) for Pydantic V2 compatibility (and usually V1 compat too)
        config = config.model_copy(update=updated_kwargs)

    app_workflow = build_graph(config)
    
    inputs = {"messages": [HumanMessage(content=request.message)]}
    
    return StreamingResponse(
        stream_graph_events(app_workflow, inputs),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn
    
    # Verify config on startup
    try:
        config = load_config(str(CONFIG_PATH))
        print(f"Config loaded successfully. Orchestrator: {config.orchestrator_model}")
    except Exception as e:
        print(f"Failed to load config: {e}")
        exit(1)
        
    uvicorn.run(app, host="0.0.0.0", port=8000)
