from typing import Optional
from fastapi import FastAPI, Depends
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()
from .config import AppConfig, load_config

app = FastAPI(title="AI Troubleshooting Agent")

@lru_cache()
def get_config() -> AppConfig:
    # Resolve config path relative to the backend directory
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config.yaml"
    return load_config(str(config_path))

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

from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio

import os
from pathlib import Path

# Mount static files
base_dir = Path(__file__).resolve().parent.parent
static_dir = base_dir / "static"
if not static_dir.exists():
    # Fallback or create if not exists to prevent crash
    static_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model_name: Optional[str] = None
    model_provider: Optional[str] = None

async def stream_graph_events(workflow, inputs):
    """
    Generator that creates SSE events from the LangGraph stream.
    """
    # Use .astream_events or .stream for detailed updates
    # simple .stream returns state updates
    async for event in workflow.astream(inputs, stream_mode="updates"):
        # Helper to format SSE
        # event is a dict of {node_name: state_update}
        
        for node_name, state_update in event.items():
            # We treat node updates as "thoughts" unless it's the final answer
            
            # If we have a new message
            if "messages" in state_update:
                messages = state_update["messages"]
                # For this simple graph, messages is usually a single message or list of messages
                if not isinstance(messages, list):
                    messages = [messages]
                
                for msg in messages:
                    # Construct valid JSON data
                    data = json.dumps({
                        "node": node_name,
                        "content": msg.content,
                        "type": msg.type
                    })
                    
                    if node_name == "orchestrator":
                        yield f"event: thought\ndata: {data}\n\n"
                    elif node_name == "network_specialist":
                         yield f"event: thought\ndata: {data}\n\n"
                    
                    # If it's a direct response from orchestrator (final answer)
                    # The logic in orchestrator returns END with a SystemMessage
                    # We might need to distinguish "final" better. 
                    # For now, let's assume the last message in the stream is the response, 
                    # BUT streaming doesn't know "last" easily until done.
                    # We'll just stream everything as thoughts and let the client decide, 
                    # OR we can refine this.
            
            # If we have next_node info (useful for debugging)
            if "next_node" in state_update:
                 data = json.dumps({"routing": state_update["next_node"]})
                 yield f"event: routing\ndata: {data}\n\n"

    # Send a completion event? Or just end stream.
    # Usually client closes on connection close.

@app.post("/chat")
async def chat(request: ChatRequest, config: AppConfig = Depends(get_config)):
    """
    Process a chat message through the LangGraph orchestrator with streaming.
    """
    from .orchestrator import build_graph
    from langchain_core.messages import HumanMessage
    
    # Check for overrides
    updated_kwargs = {}
    if request.model_name:
        updated_kwargs["orchestrator_model"] = request.model_name
    if request.model_provider:
        updated_kwargs["orchestrator_provider"] = request.model_provider
        
    if updated_kwargs:
        # Create a copy with updated fields if overrides exist
        # model_copy is deprecated in V2, using model_copy or copy depending on pydantic version
        # Assuming Pydantic V2 given modern env, but checking typical usage.
        # model_copy() is standard for V1/V2 compat in many places, but let's check imports.
        # The file uses `from pydantic import BaseModel, Field`.
        # Safe bet is model_copy(update=...)
        config = config.model_copy(update=updated_kwargs)

    app_workflow = build_graph(config)
    
    inputs = {"messages": [HumanMessage(content=request.message)]}
    
    return StreamingResponse(
        stream_graph_events(app_workflow, inputs),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    # Load config once at startup to verify it's valid, otherwise crash
    try:
        config = load_config()
        print(f"Config loaded successfully. Orchestrator: {config.orchestrator_model}")
    except Exception as e:
        print(f"Failed to load config: {e}")
        exit(1)
        
    uvicorn.run(app, host="0.0.0.0", port=8000)
