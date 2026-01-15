from fastapi import FastAPI, Depends
from functools import lru_cache
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
