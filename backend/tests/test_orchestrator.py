import pytest
from unittest.mock import MagicMock, patch
from backend.src.orchestrator import get_orchestrator_node, AgentState
from backend.src.config import AppConfig
from backend.src.models import OrchestratorDecision, SubAgentResult, AgentStatus

# Mock AppConfig
@pytest.fixture
def mock_config():
    config = MagicMock(spec=AppConfig)
    config.orchestrator_provider = "openai"
    config.orchestrator_model = "gpt-4o"
    config.system_prompt = "You are a helper."
    config.sub_agents = []
    return config

# Mock LLM Factory
@pytest.fixture
def mock_get_llm():
    with patch("backend.src.orchestrator.get_llm") as mock:
        yield mock

def test_missing_ips_routes_to_infoblox(mock_config, mock_get_llm):
    """Test that missing IPs route to infoblox deterministically."""
    # Setup
    orchestrator = get_orchestrator_node(mock_config)
    state = {
        "messages": [],
        "incident_data": {}, # Empty data
        "next_node": "",
        "decision": None
    }

    # Execute
    result = orchestrator(state)

    # Verify
    assert result["next_node"] == "infoblox"
    assert result["decision"].next_steps == ["infoblox"]
    assert "Missing source_ip" in result["decision"].reasoning

def test_present_ips_routes_to_sub_agents(mock_config, mock_get_llm):
    """Test that present IPs invoke LLM and route to sub_agents."""
    # Setup Mocks
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance
    
    # Mock the structured output
    mock_structured_llm = MagicMock()
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm
    
    expected_decision = OrchestratorDecision(
        next_steps=["sub_agents"],
        reasoning="Data looks good, checking firewalls."
    )
    mock_structured_llm.invoke.return_value = expected_decision

    # Setup State
    orchestrator = get_orchestrator_node(mock_config)
    state = {
        "messages": [],
        "incident_data": {
            "source_ip": "192.168.1.1",
            "destination_ip": "10.0.0.1"
        },
        "next_node": "",
        "decision": None
    }

    # Execute
    result = orchestrator(state)

    # Verify
    assert result["next_node"] == "sub_agents"
    assert result["decision"] == expected_decision
    # Ensure LLM was called (via with_structured_output)
    mock_structured_llm.invoke.assert_called_once()

def test_llm_failure_fallback(mock_config, mock_get_llm):
    """Test that if LLM fails, we fallback to sub_agents."""
    # Setup Mocks
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance
    
    mock_structured_llm = MagicMock()
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm
    
    # Simulate Error
    mock_structured_llm.invoke.side_effect = Exception("API Error")

    # Setup State
    orchestrator = get_orchestrator_node(mock_config)
    state = {
        "messages": [],
        "incident_data": {
            "source_ip": "1.1.1.1",
            "destination_ip": "2.2.2.2"
        },
        "next_node": "",
        "decision": None
    }

    # Execute
    result = orchestrator(state)

    # Verify
    assert result["next_node"] == "sub_agents"
    assert "LLM parsing failed" in result["decision"].reasoning
