import pytest
from unittest.mock import MagicMock, patch
from backend.src.config import AppConfig, SubAgentConfig
from backend.src.orchestrator import build_graph

# Mock AppConfig to avoid loading from disk
@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_provider="gemini",
        orchestrator_model="gemini-pro-mock",
        system_prompt="You are a helper",
        sub_agents=[
            SubAgentConfig(name="network_specialist", description="Network stuff", tools=["ping"])
        ]
    )

def test_model_propagation_to_sub_agents(mock_config):
    """
    Verify that the orchestrator and sub-agents both receive the correct model configuration.
    """
    
    # We need to patch get_llm in both locations where it is used
    with patch("backend.src.orchestrator.get_llm") as mock_get_llm_orch, \
         patch("backend.src.sub_agents.aci.get_llm") as mock_get_llm_aci:
        
        # Setup mocks to return a dummy object so code doesn't crash on invoke/bind
        mock_llm_instance = MagicMock()
        mock_get_llm_orch.return_value = mock_llm_instance
        mock_get_llm_aci.return_value = mock_llm_instance
        
        # Build the graph
        build_graph(mock_config)
        
        # Verify Orchestrator used the config
        mock_get_llm_orch.assert_called_with("gemini", "gemini-pro-mock", temperature=0)
        
        # Verify ACI Sub-agent used the config
        mock_get_llm_aci.assert_called_with("gemini", "gemini-pro-mock", temperature=0)

def test_model_propagation_override(mock_config):
    """
    Verify that if we change the config (like main.py does), it propagates.
    """
    # Override
    override_config = mock_config.model_copy(update={
        "orchestrator_provider": "openai", 
        "orchestrator_model": "gpt-4-mock"
    })
    
    with patch("backend.src.orchestrator.get_llm") as mock_get_llm_orch, \
         patch("backend.src.sub_agents.aci.get_llm") as mock_get_llm_aci:
             
        mock_llm_instance = MagicMock()
        mock_get_llm_orch.return_value = mock_llm_instance
        mock_get_llm_aci.return_value = mock_llm_instance
        
        build_graph(override_config)
        
        mock_get_llm_orch.assert_called_with("openai", "gpt-4-mock", temperature=0)
        mock_get_llm_aci.assert_called_with("openai", "gpt-4-mock", temperature=0)
