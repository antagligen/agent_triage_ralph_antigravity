import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from src.sub_agents.aci import get_aci_agent_node, aci_diag
from src.config import AppConfig
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_model="gpt-3.5-turbo", 
        system_prompt="sys prompt",
        sub_agents=[]
    )

def test_aci_diag_tool():
    # Tools must be invoked with a dict
    result = aci_diag.invoke({"target": "Flagship-Switch-01"})
    assert "Health Score=95" in result

class FakeChatModel(BaseChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Diagnostic completed"))])
    
    def bind_tools(self, tools, **kwargs):
        return self

    @property
    def _llm_type(self):
        return "fake"

def test_aci_agent_node_process(mock_config):
    # Mock ChatOpenAI to avoid missing API key error
    with patch("src.sub_agents.aci.ChatOpenAI") as mock_llm_cls:
        mock_llm_cls.return_value = FakeChatModel()
        
        node = get_aci_agent_node(mock_config)
        
        # Simulate a state passed from orchestrator
        state = {
            "messages": [HumanMessage(content="Check diagnostics for Leaf-101")],
            "next_node": "network_specialist"
        }
        
        result = node(state)
        assert "messages" in result
