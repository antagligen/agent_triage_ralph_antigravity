from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from .config import AppConfig

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    next_node: str

def get_orchestrator_node(config: AppConfig):
    """
    Factory function to create the orchestrator node with the given configuration.
    """
    llm = ChatOpenAI(model=config.orchestrator_model, temperature=0)

    def orchestrator_node(state: AgentState):
        messages = state["messages"]
        
        # Construct system prompt with available sub-agents
        agent_descriptions = "\n".join([f"- {agent.name}: {agent.description}" for agent in config.sub_agents])
        
        system_message = (
            f"{config.system_prompt}\n\n"
            f"You are the orchestrator. Your job is to route the user's request to the appropriate expert.\n"
            f"Available Experts:\n{agent_descriptions}\n\n"
            f"If the request can be handled by an expert, reply with just the name of the expert (e.g., 'network_specialist').\n"
            f"If you can answer directly or the request is general, reply with 'DIRECT_RESPONSE' followed by your answer.\n"
            f"If you are unsure, default to answering directly."
        )

        response = llm.invoke([SystemMessage(content=system_message)] + list(messages))
        # Cast to str because content can be list in some LC versions/models
        content = str(response.content).strip()

        # Simple routing logic based on LLM output
        # In a real scenario, we might use function calling or structured output for robustness
        # For now, we check if the content matches a known agent name
        
        known_agents = {agent.name for agent in config.sub_agents}
        
        if content in known_agents:
            return {"next_node": content, "messages": [response]}
        elif content.startswith("DIRECT_RESPONSE"):
             # Strip the prefix for the final response
             final_response = content.replace("DIRECT_RESPONSE", "").strip()
             return {"next_node": END, "messages": [SystemMessage(content=final_response)]}
        else:
            # Assume it's a direct response if it doesn't match an agent name exactly
            return {"next_node": END, "messages": [response]}

    return orchestrator_node

def build_graph(config: AppConfig):
    """
    Builds the LangGraph state graph.
    """
    workflow = StateGraph(AgentState)
    
    orchestrator = get_orchestrator_node(config)
    
    workflow.add_node("orchestrator", orchestrator)
    
    # Placeholder for sub-agents (to be implemented in US-003)
    # For now, if the orchestrator routes to them, we just end (or we could add dummy nodes)
    # To make the graph valid, we need to handle the edges.
    
    def router(state: AgentState) -> Literal["orchestrator", "network_specialist", "__end__"]:
        nxt = state.get("next_node")
        if nxt == "network_specialist":
            return "network_specialist"
        return "__end__"

    workflow.set_entry_point("orchestrator")
    
    # Add ACI sub-agent
    from .sub_agents.aci import get_aci_agent_node
    aci_node = get_aci_agent_node(config)
    workflow.add_node("network_specialist", aci_node)
    
    # We add a conditional edge from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "network_specialist": "network_specialist",
            END: END
        }
    )
    
    # Add edge from sub-agent back to END (or orchestrator if we wanted a loop)
    workflow.add_edge("network_specialist", END)

    return workflow.compile()
