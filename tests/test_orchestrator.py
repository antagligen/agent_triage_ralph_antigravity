import pytest
from unittest.mock import MagicMock, patch
from src.config import AppConfig, SubAgentConfig
from src.orchestrator import get_orchestrator_node, AgentState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

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
        
        # Should route to END (implied by ending execution in node logic for now)
        # But wait, our logic returns {"next_node": END, ...} for direct response
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
