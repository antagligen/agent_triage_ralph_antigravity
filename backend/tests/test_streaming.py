
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set dummy key before importing modules that might check it
os.environ["OPENAI_API_KEY"] = "dummy"

from src.main import app, get_config
from src.config import AppConfig
from langchain_core.messages import AIMessage, HumanMessage

client = TestClient(app)

@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_model="gpt-4-turbo",
        system_prompt="sys prompt",
        sub_agents=[]
    )

@pytest.fixture
def mock_llm():
    with patch("src.orchestrator.get_llm") as mock:
        # Create a mock instance that returns an iterator for stream
        llm_instance = MagicMock()
        mock.return_value = llm_instance
        
        # We need to mock .invoke for the synchronous call inside get_orchestrator_node's logic 
        # BUT wait, LangGraph uses .invoke or .stream depending on how it's called.
        # The orchestrator node calls `llm.invoke`.
        # So we mock invoke to return an AIMessage.
        llm_instance.invoke.return_value = AIMessage(content="DIRECT_RESPONSE Hello there!")
        
        yield mock

def test_streaming_chat_endpoint(mock_config, mock_llm):
    # Override dependency
    app.dependency_overrides[get_config] = lambda: mock_config
    
    # We also need to mock build_graph because it instantiates the graph with the mocked LLM
    # However, since we patched ChatOpenAI where it is imported (src.orchestrator), it should work if we import it there.
    # But src.main imports orchestrator inside the function.
    
    with patch("src.orchestrator.get_llm") as mock_chat_cls:
        mock_instance = MagicMock()
        mock_chat_cls.return_value = mock_instance
        # The orchestrator logic calls invoke
        mock_instance.invoke.return_value = AIMessage(content="DIRECT_RESPONSE Streaming works!")
        
        response = client.post("/chat", json={"message": "Test Message"})
        
        assert response.status_code == 200
        # Check explicit SSE content type
        assert "text/event-stream" in response.headers["content-type"]
        
        # Iterate lines to check formatting
        content = response.text
        assert "event: thought" in content
        # Or more specifically, since we mocked "DIRECT_RESPONSE Streaming works!",
        # the node "orchestrator" should output a message.
        # The stream_graph_events yields "event: thought" for messages.
        
        assert "Streaming works!" in content
