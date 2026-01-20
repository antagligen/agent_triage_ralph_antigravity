import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.src.main import app
from backend.src.models import TriageReport

client = TestClient(app)

@patch("backend.src.main.build_graph")
def test_chat_returns_triage_report(mock_build_graph):
    """
    Test that the chat endpoint returns a stream containing the TriageReport.
    """
    # Mock the graph execution
    mock_workflow = MagicMock()

    # Create a fake TriageReport
    report = TriageReport(
        root_cause="Test Failure",
        details="Unit test simulation",
        action="Fix it"
    )

    # Mock astream_events to yield events in the new format
    # The streaming.py now uses astream_events with version="v2"
    async def mock_astream_events(*args, **kwargs):
        # Yield on_chain_start for orchestrator
        yield {
            "event": "on_chain_start",
            "name": "orchestrator",
            "metadata": {"langgraph_node": "orchestrator"},
            "data": {}
        }
        # Yield on_chain_end with triage_report in the output
        yield {
            "event": "on_chain_end",
            "name": "triage",
            "metadata": {"langgraph_node": "triage"},
            "data": {"output": {"triage_report": report}}
        }

    mock_workflow.astream_events = mock_astream_events
    mock_build_graph.return_value = mock_workflow

    response = client.post("/chat", json={"message": "Help me"})

    assert response.status_code == 200
    content = response.text

    # Check for event: thought (on_chain_start)
    assert "event: thought" in content
    assert "orchestrator" in content

    # Check for event: triage_report
    assert "event: triage_report" in content
    assert "root_cause" in content
    assert "Test Failure" in content
