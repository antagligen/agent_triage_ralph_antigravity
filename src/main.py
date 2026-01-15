from fastapi import FastAPI, Depends
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()
from .config import AppConfig, load_config

app = FastAPI(title="AI Troubleshooting Agent")

@lru_cache()
def get_config() -> AppConfig:
    return load_config()

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

from pydantic import BaseModel
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest, config: AppConfig = Depends(get_config)):
    """
    Process a chat message through the LangGraph orchestrator.
    """
    # Import inside function to avoid potential circular import if we move things around later
    # and to ensure config is fully loaded
    from .orchestrator import build_graph
    from langchain_core.messages import HumanMessage
    
    app_workflow = build_graph(config)
    
    # Run the graph
    inputs = {"messages": [HumanMessage(content=request.message)]}
    result = app_workflow.invoke(inputs)
    
    # Extract the last message content
    last_message = result["messages"][-1]
    return {"response": last_message.content}

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
