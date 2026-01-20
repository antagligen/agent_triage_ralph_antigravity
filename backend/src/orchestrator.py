"""
Orchestrator Module

This module defines the main LangGraph orchestrator that routes user queries
to appropriate sub-agents or handles them directly.
"""
from typing import TypedDict, Annotated, Sequence, Literal, List, Dict, Any, cast, Optional
import operator
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .config import AppConfig
from .llm_factory import get_llm
from .models import OrchestratorDecision, SubAgentResult, TriageReport
from .sub_agents.infoblox import get_infoblox_agent_node
from .sub_agents.palo_alto import get_palo_alto_agent_node
from .sub_agents.aci import get_aci_agent_node
from .sub_agents.triage import get_triage_node

def merge_sub_agent_results(left: List[SubAgentResult], right: List[SubAgentResult]) -> List[SubAgentResult]:
    """Reducer to merge sub-agent results."""
    # Ensure we instantiate new lists to avoid mutation issues if any
    return (left or []) + (right or [])

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    next_node: str
    incident_data: Dict[str, Any]  # Shared state for incident data
    decision: OrchestratorDecision
    sub_agent_results: Annotated[List[SubAgentResult], merge_sub_agent_results]
    triage_report: Optional[TriageReport]

def get_orchestrator_node(config: AppConfig):
    """
    Factory function to create the orchestrator node with the given configuration.
    """
    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)

    def orchestrator_node(state: AgentState):
        messages = state["messages"]
        incident_data = state.get("incident_data", {})
        
        source_ip = incident_data.get("source_ip")
        destination_ip = incident_data.get("destination_ip")

        # 1. Input Validation Logic (Deterministic)
        if not source_ip or not destination_ip:
            reasoning = "Missing source_ip or destination_ip. Routing to Infoblox for IPAM enrichment."
            decision = OrchestratorDecision(
                next_steps=["infoblox"],
                reasoning=reasoning
            )
            return {"next_node": "infoblox", "decision": decision}

        # 2. LLM Planning Logic
        system_message = (
            f"{config.system_prompt}\n\n"
            f"You are the Request Orchestrator.\n"
            f"Current Incident Data: {incident_data}\n"
            f"The user has provided sufficient IP information. Analyze the request to confirm if we should proceed with firewall checks.\n"
            f"If standard diagnostics are needed, route to 'aci' and 'palo_alto'.\n"
        )
        
        structured_llm = llm.with_structured_output(OrchestratorDecision)
        
        try:
            decision = structured_llm.invoke([SystemMessage(content=system_message)] + list(messages))  # type: ignore
        except Exception as e:
            decision = OrchestratorDecision(
                next_steps=["aci", "palo_alto"], # Default to all relevant agents
                reasoning=f"LLM parsing failed, defaulting to full scan. Error: {e}"
            )

        # Ensure we have valid steps
        if not decision.next_steps:
             decision.next_steps = ["aci", "palo_alto"]

        return {"decision": decision}

    return orchestrator_node

def build_graph(config: AppConfig, checkpointer=None):
    """
    Builds the LangGraph state graph.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Create Nodes
    orchestrator = get_orchestrator_node(config)
    
    # Sub-agent factories return a callable `node(state) -> SubAgentResult`.
    # We need to wrap them to return `{"sub_agent_results": [result]}` compatible with AgentState.
    
    def wrap_sub_agent(agent_func):
        def wrapped_node(state: AgentState):
            result = agent_func(state)
            return {"sub_agent_results": [result]}
        return wrapped_node

    infoblox_node = wrap_sub_agent(get_infoblox_agent_node(config))
    aci_node = wrap_sub_agent(get_aci_agent_node(config))
    palo_alto_node = wrap_sub_agent(get_palo_alto_agent_node(config))
    
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("infoblox", infoblox_node)
    workflow.add_node("aci", aci_node)
    workflow.add_node("palo_alto", palo_alto_node)
    
    triage = get_triage_node(config)
    workflow.add_node("triage", triage)
    
    workflow.set_entry_point("orchestrator")
    
    # 2. Routing Logic
    def fan_out_router(state: AgentState) -> List[str]:
        """
        Determines which nodes to run next based on the orchestrator's decision.
        Returns a list of node names for parallel execution.
        """
        decision = state["decision"]
        next_steps = decision.next_steps
        
        nodes_to_run = []
        
        # specific string mapping or simple existence check
        if "infoblox" in next_steps:
            nodes_to_run.append("infoblox")
        
        if "aci" in next_steps or "sub_agents" in next_steps: # 'sub_agents' generic catch-all
             nodes_to_run.append("aci")
             
        if "palo_alto" in next_steps or "sub_agents" in next_steps:
             nodes_to_run.append("palo_alto")
        
        # If nothing matched but we have output, default to END to avoid infinite loop or error
        if not nodes_to_run:
            return [END]
            
        return nodes_to_run

    workflow.add_conditional_edges(
        "orchestrator",
        fan_out_router,
        # In LangGraph v0.2+, simpler conditional edges don't always strict map if returning list of nodes?
        # Actually checking docs: if returning list of keys, no map needed if keys exist.
        # But safest is to provide the map for inspection/visualization.
        ["infoblox", "aci", "palo_alto", END] 
    )
    
    # 3. Fan-in (Aggregation)
    # After sub-agents run, where do they go? 
    # For now, back to END. In US-005 (Triage), we will route them to 'triage'.
    
    workflow.add_edge("infoblox", "triage")
    workflow.add_edge("aci", "triage")
    workflow.add_edge("palo_alto", "triage")
    workflow.add_edge("triage", END)

    # 4. Persistence


    # 4. Persistence
    # Use passed checkpointer or default to None
    return workflow.compile(checkpointer=checkpointer)


