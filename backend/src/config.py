from typing import List, Optional
import yaml
import json
import os
from pydantic import BaseModel, Field

class SubAgentConfig(BaseModel):
    name: str = Field(..., description="Unique identifier for the sub-agent")
    description: str = Field(..., description="Description of the agent's expertise")
    tools: List[str] = Field(..., description="List of tools available to this agent")

class ACIDeviceConfig(BaseModel):
    apic_url: str = Field(..., description="URL of the APIC controller")

class DevicesConfig(BaseModel):
    aci: ACIDeviceConfig

class AppConfig(BaseModel):
    orchestrator_model: str = Field(..., description="LLM model name for the orchestrator")
    orchestrator_provider: str = Field(default="openai", description="Model provider (openai, google, gemini)")
    system_prompt: str = Field(..., description="System prompt for the orchestrator")
    sub_agents: List[SubAgentConfig] = Field(default_factory=list, description="Available sub-agents")
    devices: Optional[DevicesConfig] = Field(default=None, description="Device configuration")

def load_devices_config(path: str = "config/devices.yaml") -> Optional[DevicesConfig]:
    """
    Loads device configuration from a YAML file.
    """
    if not os.path.exists(path):
        # Optional, return None if not found
        return None

    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        return DevicesConfig(**data)

def load_config(path: str = "config.yaml") -> AppConfig:
    """
    Loads configuration from a YAML or JSON file.
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
    
    # Load devices config if available
    # Ideally this path should be relative to the config file or absolute
    # For now, we assume it's at the project root/config/devices.yaml
    # In docker, it will be at /app/config/devices.yaml if mounted, 
    # but we are running from /app/src usually. 
    # Let's check typical locations.
    
    devices_path = "config/devices.yaml"
    # If running in backend/, it might be ../config/devices.yaml
    if not os.path.exists(devices_path):
        # Try finding it relative to the config file loaded
        config_dir = os.path.dirname(os.path.abspath(path))
        potential_path = os.path.join(config_dir, "config", "devices.yaml") # if config.yaml is in root
        if os.path.exists(potential_path):
            devices_path = potential_path
        else:
             # If config.yaml is in backend/ and devices is in config/ (root)
             potential_path = os.path.join(config_dir, "..", "config", "devices.yaml")
             if os.path.exists(potential_path):
                 devices_path = potential_path

    devices = load_devices_config(devices_path)
    
    config = AppConfig(**data)
    if devices:
        config.devices = devices
        
    return config

def get_aci_credentials():
    """
    Retrieves ACI credentials from environment variables.
    """
    username = os.getenv("ACI_USERNAME")
    password = os.getenv("ACI_PASSWORD")
    
    if not username or not password:
        raise ValueError("ACI_USERNAME and ACI_PASSWORD environment variables must be set.")
        
    return username, password
