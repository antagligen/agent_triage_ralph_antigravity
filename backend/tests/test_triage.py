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
                agent_name="palo_alto",
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
    assert result["triage_report"].root_cause == expected_report.root_cause
    assert result["triage_report"].failed_agents == []
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

@patch("backend.src.sub_agents.triage.get_llm")
def test_triage_node_partial_failure(mock_get_llm, mock_config):
    """Test that failed agents are tracked and reported in the triage output."""
    # Setup Mock LLM
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance
    mock_structured_llm = MagicMock()
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm
    
    expected_report = TriageReport(
        root_cause="Partial Data - ACI Unreachable",
        details="Based on available Palo Alto data. ACI agent failed.",
        action="Investigate ACI connectivity manually"
    )
    mock_structured_llm.invoke.return_value = expected_report

    # Create Node
    triage_node = get_triage_node(mock_config)

    # Input State with mixed success/failure
    state = {
        "sub_agent_results": [
            SubAgentResult(
                agent_name="palo_alto",
                raw_data={"logs": "allowed"},
                summary="No blocked traffic found",
                status=AgentStatus.SUCCESS
            ),
            SubAgentResult(
                agent_name="aci",
                raw_data={"error": "Connection refused"},
                summary="Error executing ACI agent: Connection refused",
                status=AgentStatus.FAILURE
            )
        ],
        "incident_data": {"source_ip": "10.0.0.1", "destination_ip": "10.0.0.2"}
    }

    # Execute
    result = triage_node(state)

    # Verify
    assert "triage_report" in result
    report = result["triage_report"]
    
    # Check that failed_agents is populated correctly
    assert report.failed_agents == ["aci"]
    
    # Verify the LLM was called with failure info in prompt
    call_args = mock_structured_llm.invoke.call_args[0][0]
    # Check that the user message contains failure info
    user_msg = call_args[1].content
    assert "aci" in user_msg
    assert "FAILURE" in user_msg or "Failed Agents" in user_msg

