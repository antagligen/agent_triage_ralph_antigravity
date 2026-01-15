
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.src.main import app, get_config
from backend.src.config import AppConfig

@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_model="default-model",
        orchestrator_provider="openai",
        system_prompt="test prompt",
        sub_agents=[]
    )

@pytest.fixture
def client(mock_config):
    app.dependency_overrides[get_config] = lambda: mock_config
    return TestClient(app)

@patch("backend.src.sub_agents.aci.get_llm")
@patch("backend.src.orchestrator.get_llm")
def test_chat_default_model(mock_orch_get_llm, mock_aci_get_llm, client):
    """Verify that default config is used when no overrides are provided."""
    # Mock return value to avoid actual LLM calls
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Response"
    mock_llm.invoke.return_value.type = "ai"
    
    # Setup both mocks
    mock_orch_get_llm.return_value = mock_llm
    mock_aci_get_llm.return_value = mock_llm

    response = client.post("/chat", json={"message": "hello"})
    
    assert response.status_code == 200
    # Check that get_llm was called with defaults for orchestrator
    mock_orch_get_llm.assert_called_with("openai", "default-model", temperature=0)

@patch("backend.src.sub_agents.aci.get_llm")
@patch("backend.src.orchestrator.get_llm")
def test_chat_override_model(mock_orch_get_llm, mock_aci_get_llm, client):
    """Verify that model_name override is respected."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Response"
    mock_llm.invoke.return_value.type = "ai"
    
    mock_orch_get_llm.return_value = mock_llm
    mock_aci_get_llm.return_value = mock_llm

    response = client.post("/chat", json={"message": "hello", "model_name": "gpt-4"})
    
    assert response.status_code == 200
    mock_orch_get_llm.assert_called_with("openai", "gpt-4", temperature=0)

@patch("backend.src.sub_agents.aci.get_llm")
@patch("backend.src.orchestrator.get_llm")
def test_chat_override_provider(mock_orch_get_llm, mock_aci_get_llm, client):
    """Verify that model_provider override is respected."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Response"
    mock_llm.invoke.return_value.type = "ai"
    
    mock_orch_get_llm.return_value = mock_llm
    mock_aci_get_llm.return_value = mock_llm

    response = client.post("/chat", json={"message": "hello", "model_provider": "gemini", "model_name": "gemini-pro"})
    
    assert response.status_code == 200
    mock_orch_get_llm.assert_called_with("gemini", "gemini-pro", temperature=0)
