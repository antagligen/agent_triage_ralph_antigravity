from typing import List, Annotated
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..config import AppConfig, get_aci_credentials
from ..llm_factory import get_llm

from ..models import SubAgentResult, AgentStatus



# Mocked Tools
@tool
def aci_diag(target: str) -> str:
    """Run diagnostics on a Cisco ACI target (simulated)."""
    return f"Diagnostics for {target}: Health Score=95, Faults=0. Everything looks normal on the fabric."

@tool
def ping(target: str) -> str:
    """Ping a network target."""
    return f"Ping to {target} successful. RTT=2ms."

@tool
def traceroute(target: str) -> str:
    """Traceroute to a network target."""
    return f"Traceroute to {target}: 1 hop, directly connected."


def get_aci_agent_node(config: AppConfig):
    """
    Creates the Cisco ACI sub-agent node.
    """
    # Load Credentials & Config
    try:
        username, password = get_aci_credentials()
        apic_url = config.devices.aci.apic_url if config.devices and config.devices.aci else "N/A"
        
        # Simulated Authentication
        print(f"--- ACI Agent Initializing ---")
        print(f"Target APIC: {apic_url}")
        print(f"Authenticated as: {username}")
        # In a real app, we would get a token here.
        
    except Exception as e:
        print(f"Failed to initialize ACI Config: {e}")

    tools = [aci_diag, ping, traceroute]

    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)
    
    agent = create_react_agent(llm, tools=tools)
    
    def aci_node(state) -> SubAgentResult:
        try:
            result = agent.invoke(state)
            # Extract the last message as the summary
            last_msg = result["messages"][-1]
            summary = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            
            return SubAgentResult(
                raw_data={"messages": [m.content for m in result["messages"]]},
                summary=str(summary),
                status=AgentStatus.SUCCESS
            )
        except Exception as e:
            return SubAgentResult(
                raw_data={"error": str(e)},
                summary=f"Error executing ACI agent: {str(e)}",
                status=AgentStatus.FAILURE
            )

    return aci_node
