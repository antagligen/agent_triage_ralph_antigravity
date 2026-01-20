from typing import List, Annotated
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..config import AppConfig
from ..llm_factory import get_llm
from ..models import SubAgentResult, AgentStatus

# Mocked Tools
@tool
def get_ip_info(ip_address: str) -> str:
    """Retrieve details about an IP address from Infoblox."""
    return f"IP {ip_address} is assigned to host 'web-server-01' in subnet '10.0.0.0/24'. Status: Used."

@tool
def check_dns(hostname: str) -> str:
    """Check DNS records for a hostname."""
    return f"DNS record for {hostname}: A record points to 10.0.0.15. TTL: 3600."

def get_infoblox_agent_node(config: AppConfig):
    """
    Creates the Infoblox sub-agent node.
    """
    tools = [get_ip_info, check_dns]

    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)
    
    agent = create_react_agent(llm, tools=tools)
    
    def infoblox_node(state) -> SubAgentResult:
        try:
            result = agent.invoke(state)
            last_msg = result["messages"][-1]
            summary = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            
            return SubAgentResult(
                agent_name="infoblox",
                raw_data={"messages": [m.content for m in result["messages"]]},
                summary=str(summary),
                status=AgentStatus.SUCCESS
            )
        except Exception as e:
            return SubAgentResult(
                agent_name="infoblox",
                raw_data={"error": str(e)},
                summary=f"Error executing Infoblox agent: {str(e)}",
                status=AgentStatus.FAILURE
            )

    return infoblox_node
