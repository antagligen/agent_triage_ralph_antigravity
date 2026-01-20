import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from backend.src.sub_agents.aci import get_aci_agent_node, aci_diag
from backend.src.config import AppConfig
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
    # Mock get_llm to avoid missing API key error and return FakeChatModel
    with patch("backend.src.sub_agents.aci.get_llm") as mock_get_llm:
        mock_get_llm.return_value = FakeChatModel()

        node = get_aci_agent_node(mock_config)

        # Simulate a state passed from orchestrator
        state = {
            "messages": [HumanMessage(content="Check diagnostics for Leaf-101")],
            "next_node": "network_specialist"
        }

        result = node(state)
        assert result.summary == "Diagnostic completed"
        assert result.status == "SUCCESS"



# Better approach: Patch os.path.exists and load_endpoints_config
@patch("backend.src.sub_agents.aci.os.path.exists")
@patch("backend.src.sub_agents.aci.load_endpoints_config")
def test_aci_agent_loads_dynamic_tools_mocked(mock_load, mock_exists, mock_config):
    mock_exists.return_value = True
    mock_load.return_value = [{
        "name": "mocked_dynamic_tool",
        "description": "Desc",
        "path": "/api",
        "method": "GET",
        "parameters": []
    }]

    with patch("backend.src.sub_agents.aci.create_react_agent") as mock_create_agent, \
         patch("backend.src.sub_agents.aci.get_llm"):

        get_aci_agent_node(mock_config)

        args, kwargs = mock_create_agent.call_args
        tools = kwargs.get("tools")
        tool_names = [t.name for t in tools]

        assert "mocked_dynamic_tool" in tool_names
