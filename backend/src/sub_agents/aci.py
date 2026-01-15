from typing import List, Annotated
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..config import AppConfig
from ..llm_factory import get_llm

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
    # Filter tools based on config if needed, but for now we provide the set relevant to this agent
    tools = [aci_diag, ping, traceroute]
    

    # We use a separate model instance for the sub-agent, theoretically could be different from orchestrator
    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)
    
    # Using LangGraph's prebuilt react agent for simplicity
    agent = create_react_agent(llm, tools=tools)
    
    def aci_node(state):
        # The state comes from the orchestrator. 
        # We need to adapt it if the sub-agent expects a different state schema, 
        # but here we reuse the message history.
        result = agent.invoke(state)
        # The result from create_react_agent is the final state.
        # We return the updated messages.
        return {"messages": result["messages"]}

    return aci_node
