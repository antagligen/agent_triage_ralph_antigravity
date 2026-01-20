"""
Orchestrator Module

This module defines the main LangGraph orchestrator that routes user queries
to appropriate sub-agents or handles them directly.
"""
from typing import TypedDict, Annotated, Sequence, Literal, List, Dict, Any, cast
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .config import AppConfig
from .llm_factory import get_llm
from .models import OrchestratorDecision

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    next_node: str
    incident_data: Dict[str, Any]  # Shared state for incident data
    decision: OrchestratorDecision

def get_orchestrator_node(config: AppConfig):
    """
    Factory function to create the orchestrator node with the given configuration.
    """
    # Use structured output capable LLM if possible, otherwise rely on prompting
    # For this refactor we rely on Pydantic structured output support in LangChain logic
    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)

    def orchestrator_node(state: AgentState):
        messages = state["messages"]
        incident_data = state.get("incident_data", {})
        
        source_ip = incident_data.get("source_ip")
        destination_ip = incident_data.get("destination_ip")

        # 1. Input Validation Logic (Deterministic)
        # If we are missing critical IPs, we prefer to route to Infoblox for enrichment.
        if not source_ip or not destination_ip:
            # We can also use LLM to confirm, but hard logic is safer for this specific requirement
            reasoning = "Missing source_ip or destination_ip. Routing to Infoblox for IPAM enrichment."
            decision = OrchestratorDecision(
                next_steps=["infoblox"],
                reasoning=reasoning
            )
            return {"next_node": "infoblox", "decision": decision}

        # 2. LLM Planning Logic (for when data is present)
        # If we have IPs, we route to sub-agents (firewalls, etc.)
        # We can ask LLM if it wants to do anything specific, but per requirements:
        # "Route to Infoblox if data missing, or Sub-Agents if present"
        
        system_message = (
            f"{config.system_prompt}\n\n"
            f"You are the Request Orchestrator.\n"
            f"Current Incident Data: {incident_data}\n"
            f"The user has provided sufficient IP information. Analyze the request to confirm if we should proceed with firewall checks.\n"
            f"If standard diagnostics are needed, route to 'sub_agents'.\n"
        )
        
        # We use strict Pydantic output
        structured_llm = llm.with_structured_output(OrchestratorDecision)
        
        try:
            decision = structured_llm.invoke([SystemMessage(content=system_message)] + list(messages))  # type: ignore
        except Exception as e:
            # Fallback if LLM fails
            decision = OrchestratorDecision(
                next_steps=["sub_agents"],
                reasoning=f"LLM parsing failed, defaulting to full scan. Error: {e}"
            )

        # Force routing based on decision
        # The prompt might suggest 'sub_agents', or specific names.
        # For this pass, we treat 'sub_agents' as a parallel group.
        
        if not decision.next_steps:
             decision.next_steps = ["sub_agents"]

        # Simple router for the graph: if 'infoblox' in steps -> infoblox
        # If 'sub_agents' or others -> sub_agents node (which fans out)
        
        next_node = "sub_agents"
        if "infoblox" in decision.next_steps:
            next_node = "infoblox"
            
        return {"next_node": next_node, "decision": decision}

    return orchestrator_node

def build_graph(config: AppConfig):
    """
    Builds the LangGraph state graph.
    """
    workflow = StateGraph(AgentState)
    
    orchestrator = get_orchestrator_node(config)
    
    workflow.add_node("orchestrator", orchestrator)
    
    # -- Placeholder Nodes for Graph Structure (will be fully implemented in later US) --
    
    # 1. Infoblox Node
    # Just a dummy for now to allow graph compilation if referenced
    def infoblox_node(state):
        return {"incident_data": {**state.get("incident_data", {}), "source_ip": "1.2.3.4"}} # Mock enrichment
    workflow.add_node("infoblox", infoblox_node)

    # 2. Sub-Agents Node (Fan-out placeholder)
    def sub_agents_node(state):
        return {"sub_agent_results": []} 
    workflow.add_node("sub_agents", sub_agents_node)
    
    workflow.set_entry_point("orchestrator")
    
    # Conditional Edges
    def router(state: AgentState) -> Literal["infoblox", "sub_agents", "__end__"]:
        return cast(Literal["infoblox", "sub_agents", "__end__"], state["next_node"])

    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "infoblox": "infoblox",
            "sub_agents": "sub_agents",
            "__end__": END # Fallback
        }
    )
    
    # For now, end after the next step
    workflow.add_edge("infoblox", END)
    workflow.add_edge("sub_agents", END)

    return workflow.compile()

