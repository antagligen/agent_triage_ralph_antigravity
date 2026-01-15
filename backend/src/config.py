from typing import List, Optional
import yaml
import json
import os
from pydantic import BaseModel, Field

class SubAgentConfig(BaseModel):
    name: str = Field(..., description="Unique identifier for the sub-agent")
    description: str = Field(..., description="Description of the agent's expertise")
    tools: List[str] = Field(..., description="List of tools available to this agent")

class AppConfig(BaseModel):
    orchestrator_model: str = Field(..., description="LLM model name for the orchestrator")
    orchestrator_provider: str = Field(default="openai", description="Model provider (openai, google, gemini)")
    system_prompt: str = Field(..., description="System prompt for the orchestrator")
    sub_agents: List[SubAgentConfig] = Field(default_factory=list, description="Available sub-agents")

def load_config(path: str = "config.yaml") -> AppConfig:
    """
    Loads configuration from a YAML or JSON file.
    
    Args:
        path: Path to the configuration file (default: config.yaml)
        
    Returns:
        AppConfig: Validated application configuration
        
    Raises:
        FileNotFoundError: If existing file is not found
        ValueError: If file format is not supported
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, 'r') as f:
        if path.endswith('.yaml') or path.endswith('.yml'):
            data = yaml.safe_load(f)
        elif path.endswith('.json'):
            data = json.load(f)
        else:
            raise ValueError("Configuration file must be .yaml, .yml, or .json")
            
    return AppConfig(**data)
