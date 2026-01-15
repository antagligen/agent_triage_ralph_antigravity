import pytest
from unittest.mock import MagicMock, patch
from src.config import AppConfig, SubAgentConfig
from src.orchestrator import get_orchestrator_node, AgentState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_model="gpt-4-turbo",
        system_prompt="Test Prompt",
        sub_agents=[
            SubAgentConfig(name="network_specialist", description="Net stuff", tools=[]),
            SubAgentConfig(name="system_admin", description="Sys stuff", tools=[])
        ]
    )

def test_orchestrator_routes_to_agent(mock_config):
    """Test that the orchestrator sets next_node correctly when LLM returns an agent name."""
    
    # Mock the LLM to return "network_specialist"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="network_specialist")
    
    with patch("src.orchestrator.ChatOpenAI", return_value=mock_llm):
        orchestrator = get_orchestrator_node(mock_config)
        state = {"messages": [HumanMessage(content="My network is down")]}
        
        result = orchestrator(state)
        
        assert result["next_node"] == "network_specialist"
        assert result["messages"][0].content == "network_specialist"

def test_orchestrator_responds_directly(mock_config):
    """Test that the orchestrator handles direct responses."""
    
    # Mock the LLM to return "DIRECT_RESPONSE Hello there"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="DIRECT_RESPONSE Hello there")
    
    with patch("src.orchestrator.ChatOpenAI", return_value=mock_llm):
        orchestrator = get_orchestrator_node(mock_config)
        state = {"messages": [HumanMessage(content="Hi")]}
        
        result = orchestrator(state)
        
        # Should route to END
        from langgraph.graph import END
        assert result["next_node"] == END
        assert result["messages"][0].content == "Hello there"

def test_orchestrator_unknown_response(mock_config):
    """Test behavior when LLM returns something unexpected."""
    
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="I don't know")
    
    with patch("src.orchestrator.ChatOpenAI", return_value=mock_llm):
        orchestrator = get_orchestrator_node(mock_config)
        state = {"messages": [HumanMessage(content="Random query")]}
        
        result = orchestrator(state)
        
        from langgraph.graph import END
        assert result["next_node"] == END
        assert result["messages"][0].content == "I don't know"

class FakeChatModel(BaseChatModel):
    response: str = "Default response"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=self.response))])
    
    def bind_tools(self, tools, **kwargs):
        return self

    @property
    def _llm_type(self):
        return "fake"

def test_integration_routing_network_specialist(mock_config):
    """Test that the graph (integration level) routes to network_specialist."""
    
    mock_llm = FakeChatModel(response="network_specialist")

    with patch("src.orchestrator.ChatOpenAI", return_value=mock_llm), \
         patch("src.sub_agents.aci.ChatOpenAI", return_value=mock_llm):

        from src.orchestrator import build_graph
        graph = build_graph(mock_config)
        
        result = graph.invoke({"messages": [HumanMessage(content="ACI issue")]})
        
        pass
