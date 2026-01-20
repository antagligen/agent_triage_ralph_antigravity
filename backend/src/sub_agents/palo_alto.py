from typing import List, Annotated
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import create_react_agent
from ..config import AppConfig
from ..llm_factory import get_llm
from ..models import SubAgentResult, AgentStatus

# Mocked Tools
@tool
def check_firewall_logs(src_ip: str, dest_ip: str) -> str:
    """Check firewall logs for traffic between source and destination IPs."""
    return f"Traffic from {src_ip} to {dest_ip}: Allowed by rule 'Permit-Web-Traffic'. No drops found in last 1 hour."

@tool
def verify_policy(policy_name: str) -> str:
    """Verify if a specific security policy is active."""
    return f"Policy '{policy_name}' is Active. Action: Allow."

def get_palo_alto_agent_node(config: AppConfig):
    """
    Creates the Palo Alto sub-agent node.
    """
    tools = [check_firewall_logs, verify_policy]

    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)
    
    agent = create_react_agent(llm, tools=tools)
    
    def palo_node(state) -> SubAgentResult:
        try:
            result = agent.invoke(state)
            last_msg = result["messages"][-1]
            summary = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            
            return SubAgentResult(
                agent_name="palo_alto",
                raw_data={"messages": [m.content for m in result["messages"]]},
                summary=str(summary),
                status=AgentStatus.SUCCESS
            )
        except Exception as e:
            return SubAgentResult(
                agent_name="palo_alto",
                raw_data={"error": str(e)},
                summary=f"Error executing Palo Alto agent: {str(e)}",
                status=AgentStatus.FAILURE
            )

    return palo_node
