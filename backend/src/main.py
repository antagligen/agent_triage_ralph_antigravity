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


# Global checkpointer for persistence
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

@app.post("/chat")
async def chat(request: ChatRequest, config: AppConfig = Depends(get_config)):
    """
    Process a chat message through the LangGraph orchestrator with streaming.
    """
    import uuid

    # Check for overrides
    updated_kwargs = {}
    if request.model_name:
        updated_kwargs["orchestrator_model"] = request.model_name
    if request.model_provider:
        updated_kwargs["orchestrator_provider"] = request.model_provider

    if updated_kwargs:
        config = config.model_copy(update=updated_kwargs)

    # Use global checkpointer so state is persisted across builds (if we cached graph)
    # But current design rebuilds graph on config change.
    # We pass the checkpointer to valid it's used.
    app_workflow = build_graph(config, checkpointer=checkpointer)

    # Generate or reuse thread_id (for now, simple random one for every new chat request,
    # unless we want to support conversation history from frontend eventually)
    # Ideally frontend should send a conversation/thread ID. Use a random one for now.
    thread_id = str(uuid.uuid4())

    inputs = {"messages": [HumanMessage(content=request.message)]}

    # Pass thread_id to the runner
    run_config = {"configurable": {"thread_id": thread_id}}

    return StreamingResponse(
        stream_graph_events(app_workflow, inputs, run_config),
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
