import pytest
from unittest.mock import MagicMock, patch
from backend.src.sub_agents.triage import get_triage_node
from backend.src.models import SubAgentResult, AgentStatus, TriageReport
from backend.src.config import AppConfig, SubAgentConfig

@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_model="gpt-4",
        orchestrator_provider="openai",
        system_prompt="Test Prompt",
        sub_agents=[]
    )

@patch("backend.src.sub_agents.triage.get_llm")
def test_triage_node_success(mock_get_llm, mock_config):
    # Setup Mock LLM
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance
    
    # Mock structured output
    mock_structured_llm = MagicMock()
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm
    
    expected_report = TriageReport(
        root_cause="Firewall Rule Block",
        details="Traffic blocked by Palo Alto firewall rule ID 123",
        action="Unblock port 443"
    )
    mock_structured_llm.invoke.return_value = expected_report

    # Create Node
    triage_node = get_triage_node(mock_config)

    # Input State
    state = {
        "sub_agent_results": [
            SubAgentResult(
                raw_data={"foo": "bar"},
                summary="Packet dropped by firewall",
                status=AgentStatus.SUCCESS
            )
        ],
        "incident_data": {"source_ip": "10.0.0.1"}
    }

    # Execute
    result = triage_node(state)

    # Verify
    assert "triage_report" in result
    assert result["triage_report"] == expected_report
    mock_structured_llm.invoke.assert_called_once()

@patch("backend.src.sub_agents.triage.get_llm")
def test_triage_node_failure_handling(mock_get_llm, mock_config):
    # Setup Mock LLM to raise exception
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance
    mock_structured_llm = MagicMock()
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm
    
    # Simulate LLM failure
    mock_structured_llm.invoke.side_effect = Exception("API connection failed")

    # Create Node
    triage_node = get_triage_node(mock_config)

    # Input State
    state = {
        "sub_agent_results": [],
        "incident_data": {}
    }

    # Execute
    result = triage_node(state)

    # Verify fallback
    assert "triage_report" in result
    report = result["triage_report"]
    assert report.root_cause == "Analysis Failed"
    assert "API connection failed" in report.details
