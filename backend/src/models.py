from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"

class SubAgentResult(BaseModel):
    """Result from a sub-agent execution."""
    agent_name: str = Field(description="Name of the agent that produced this result")
    raw_data: Dict[str, Any] = Field(description="Raw data returned by the tool/API")
    summary: str = Field(description="Human-readable summary of the findings")
    status: AgentStatus = Field(description="Status of the execution")

class OrchestratorDecision(BaseModel):
    """Decision made by the Orchestrator."""
    next_steps: List[str] = Field(description="List of next steps or agents to call")
    reasoning: str = Field(description="Reasoning behind the decision")

class TriageReport(BaseModel):
    """Final triage report."""
    root_cause: str = Field(description="Identified root cause of the issue")
    details: Union[List[str], str] = Field(description="Detailed explanation or evidence")
    action: str = Field(description="Recommended action to resolve the issue")
    failed_agents: List[str] = Field(default_factory=list, description="List of agents that failed to execute")
