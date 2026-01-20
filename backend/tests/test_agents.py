from typing import Any, Dict
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Adjust sys.path to ensure we can import backend
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.config import AppConfig
from backend.src.models import SubAgentResult, AgentStatus, OrchestratorDecision, TriageReport
from backend.src.sub_agents.aci import get_aci_agent_node
from backend.src.sub_agents.infoblox import get_infoblox_agent_node
from backend.src.sub_agents.palo_alto import get_palo_alto_agent_node
from backend.src.orchestrator import get_orchestrator_node
from backend.src.sub_agents.triage import get_triage_node

class MockConfig(AppConfig):
    orchestrator_provider: str = "openai"
    orchestrator_model: str = "gpt-3.5-turbo"
    system_prompt: str = "You are a helpful assistant."
    sub_agents: list = []

@pytest.fixture
def mock_config():
    return MockConfig()

@pytest.fixture
def mock_llm():
    mock = MagicMock()
    # Mock structured output for Orchestrator and Triage
    mock.with_structured_output.return_value = mock
    return mock

# --- Tests for Sub-Agents (ACI, Infoblox, Palo Alto) ---

@patch('backend.src.sub_agents.aci.create_react_agent')
@patch('backend.src.sub_agents.aci.load_system_prompt')
@patch('backend.src.sub_agents.aci.get_llm')
def test_aci_agent_initialization(mock_get_llm, mock_load_prompt, mock_create_agent, mock_config, mock_llm):
    """Verify ACI agent loads prompt and passes it to create_react_agent."""
    mock_load_prompt.return_value = "Mocked ACI Prompt"
    mock_get_llm.return_value = mock_llm

    # Run Factory
    get_aci_agent_node(mock_config)

    # Assertion
    mock_load_prompt.assert_called_with("aci")
    mock_create_agent.assert_called_once()
    _, kwargs = mock_create_agent.call_args
    assert kwargs.get("prompt") == "Mocked ACI Prompt"

@patch('backend.src.sub_agents.infoblox.create_react_agent')
@patch('backend.src.sub_agents.infoblox.load_system_prompt')
@patch('backend.src.sub_agents.infoblox.get_llm')
def test_infoblox_agent_initialization(mock_get_llm, mock_load_prompt, mock_create_agent, mock_config, mock_llm):
    """Verify Infoblox agent loads prompt and passes it to create_react_agent."""
    mock_load_prompt.return_value = "Mocked Infoblox Prompt"
    mock_get_llm.return_value = mock_llm

    get_infoblox_agent_node(mock_config)

    mock_load_prompt.assert_called_with("infoblox")
    mock_create_agent.assert_called_once()
    _, kwargs = mock_create_agent.call_args
    assert kwargs.get("prompt") == "Mocked Infoblox Prompt"

@patch('backend.src.sub_agents.palo_alto.create_react_agent')
@patch('backend.src.sub_agents.palo_alto.load_system_prompt')
@patch('backend.src.sub_agents.palo_alto.get_llm')
def test_palo_alto_agent_initialization(mock_get_llm, mock_load_prompt, mock_create_agent, mock_config, mock_llm):
    """Verify Palo Alto agent loads prompt and passes it to create_react_agent."""
    mock_load_prompt.return_value = "Mocked Palo Alto Prompt"
    mock_get_llm.return_value = mock_llm

    get_palo_alto_agent_node(mock_config)

    mock_load_prompt.assert_called_with("palo_alto")
    mock_create_agent.assert_called_once()
    _, kwargs = mock_create_agent.call_args
    assert kwargs.get("prompt") == "Mocked Palo Alto Prompt"

# --- Tests for Orchestrator ---

@patch('backend.src.orchestrator.load_system_prompt')
@patch('backend.src.orchestrator.get_llm')
def test_orchestrator_initialization_and_run(mock_get_llm, mock_load_prompt, mock_config, mock_llm):
    """Verify Orchestrator loads prompt dynamically during execution."""
    mock_load_prompt.return_value = "Mocked Orchestrator Prompt"
    mock_get_llm.return_value = mock_llm

    # Mock the LLM invoke response
    mock_decision = OrchestratorDecision(next_steps=["aci"], reasoning="test")
    mock_llm.invoke.return_value = mock_decision

    # Create Node
    node = get_orchestrator_node(mock_config)

    # Run Node
    state = {"messages": [HumanMessage(content="Test query")], "incident_data": {"source_ip": "1.1.1.1", "destination_ip": "2.2.2.2"}}
    result = node(state)

    # Assertions
    mock_load_prompt.assert_called_with("orchestrator")
    assert result["decision"] == mock_decision

# --- Tests for Triage ---

@patch('backend.src.sub_agents.triage.load_system_prompt')
@patch('backend.src.sub_agents.triage.get_llm')
def test_triage_initialization_and_run(mock_get_llm, mock_load_prompt, mock_config, mock_llm):
    """Verify Triage loads prompt dynamically during execution."""
    mock_load_prompt.return_value = "Mocked Triage Prompt"
    mock_get_llm.return_value = mock_llm

    # Mock Triage Report
    mock_report = TriageReport(
        root_cause="Test Cause",
        details="Test Details",
        action="Test Action",
        failed_agents=[]
    )
    mock_llm.invoke.return_value = mock_report

    # Create Node
    node = get_triage_node(mock_config)

    # Run Node
    state = {
        "sub_agent_results": [
            SubAgentResult(agent_name="aci", status=AgentStatus.SUCCESS, summary="Good", raw_data={})
        ],
        "incident_data": {}
    }
    result = node(state)

    # Assertions
    mock_load_prompt.assert_called_with("triage")
    assert result["triage_report"] == mock_report

# --- Test Agent Execution Wrapper (verifying behavior) ---

@patch('backend.src.sub_agents.aci.create_react_agent')
@patch('backend.src.sub_agents.aci.get_llm')
@patch('backend.src.sub_agents.aci.load_system_prompt')
def test_agent_execution_wrapper(mock_load, mock_get_llm, mock_create_agent, mock_config, mock_llm):
    """Verify the wrapper correctly formats the SubAgentResult."""
    # Setup Mock Agent
    mock_agent_instance = MagicMock()
    # Invoke returns a dict with 'messages'
    mock_agent_instance.invoke.return_value = {
        "messages": [
            HumanMessage(content="task"),
            AIMessage(content="Final Answer")
        ]
    }
    mock_create_agent.return_value = mock_agent_instance
    mock_get_llm.return_value = mock_llm

    # Get Node
    node = get_aci_agent_node(mock_config)

    # Execute
    state = {"messages": [HumanMessage(content="Go")]}
    result = node(state)

    # Verify Result
    assert isinstance(result, SubAgentResult)
    assert result.agent_name == "aci"
    assert result.status == AgentStatus.SUCCESS
    assert result.summary == "Final Answer"
