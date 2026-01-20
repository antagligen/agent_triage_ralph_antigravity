from typing import List, Optional
import yaml
import json
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default prompts for each agent (fallbacks if files are missing)
DEFAULT_PROMPTS = {
    "orchestrator": "You are the Request Orchestrator. Analyze incoming requests and route to appropriate sub-agents.",
    "aci": "You are an expert Cisco ACI network diagnostics agent.",
    "infoblox": "You are an Infoblox IPAM and DNS specialist.",
    "palo_alto": "You are a Palo Alto firewall diagnostics expert.",
    "triage": "You are an SRE triage specialist. Analyze information from sub-agents and provide a unified report.",
}


def load_system_prompt(agent_name: str) -> str:
    """
    Loads a system prompt from backend/system_prompts/{agent_name}.txt.

    Args:
        agent_name: Name of the agent (orchestrator, aci, infoblox, palo_alto, triage)

    Returns:
        The prompt text from the file, or a default prompt if file not found.
    """
    # Determine the base directory for system_prompts
    # This works whether we're running from /app/src or /app
    current_dir = Path(__file__).resolve().parent  # backend/src
    prompts_dir = current_dir.parent / "system_prompts"  # backend/system_prompts

    prompt_file = prompts_dir / f"{agent_name}.txt"

    if prompt_file.exists():
        try:
            content = prompt_file.read_text(encoding="utf-8").strip()
            logger.debug(f"Loaded system prompt for '{agent_name}' from {prompt_file}")
            return content
        except Exception as e:
            logger.warning(f"Error reading prompt file for '{agent_name}': {e}")
    else:
        logger.warning(f"System prompt file not found: {prompt_file}")

    # Return default prompt
    default = DEFAULT_PROMPTS.get(agent_name, f"You are a helpful {agent_name} agent.")
    logger.info(f"Using default prompt for '{agent_name}'")
    return default

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
