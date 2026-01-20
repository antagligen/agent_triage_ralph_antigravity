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
    
    # Mock stream_graph_events logic indirectly by mocking what build_graph returns
    # But main.py calls stream_graph_events(app_workflow, ...)
    # which iterates app_workflow.astream(...)
    
    # So we need to mock app_workflow.astream to yield events
    
    async def mock_astream(*args, **kwargs):
        # Yield a partial thought
        yield {"orchestrator": {"messages": [MagicMock(content="Thinking...", type="ai")]}}
        # Yield the triage report
        yield {"triage": {"triage_report": report}}
        
    mock_workflow.astream = mock_astream
    mock_build_graph.return_value = mock_workflow
    
    response = client.post("/chat", json={"message": "Help me"})
    
    assert response.status_code == 200
    content = response.text
    
    # Check for event: thought
    assert "event: thought" in content
    assert "Thinking..." in content
    
    # Check for event: triage_report
    assert "event: triage_report" in content
    assert "root_cause" in content
    assert "Test Failure" in content

