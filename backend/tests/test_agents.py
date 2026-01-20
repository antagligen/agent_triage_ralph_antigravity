import sys
import os
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Add backend to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.config import AppConfig
from backend.src.models import SubAgentResult, AgentStatus

# Mock Config
class MockConfig(AppConfig):
    orchestrator_provider: str = "openai"
    orchestrator_model: str = "gpt-3.5-turbo"
    system_prompt: str = "You are a helpful assistant."
    sub_agents: list = []

config = MockConfig()

# Set dummy API key
os.environ["OPENAI_API_KEY"] = "sk-dummy"

def mock_agent_invoke(state):
    return {"messages": state["messages"] + [AIMessage(content="Mock summary result from agent.")]}

def test_agents_mocked():
    print("Running Mocked Agent Tests...")
    
    # We patch create_react_agent in each module to return a mock agent
    # Since we can't easily patch the imported function in the test script (it's already imported in the modules),
    # we might need to patch where it is USED.
    # But since we import get_aci_agent_node, which imports create_react_agent...
    # It's better to patch 'langgraph.prebuilt.create_react_agent' globally or in the target modules.
    
    with patch('backend.src.sub_agents.aci.create_react_agent') as mock_create_aci, \
         patch('backend.src.sub_agents.infoblox.create_react_agent') as mock_create_infoblox, \
         patch('backend.src.sub_agents.palo_alto.create_react_agent') as mock_create_palo:
        
        # Setup mocks
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = mock_agent_invoke
        
        mock_create_aci.return_value = mock_agent
        mock_create_infoblox.return_value = mock_agent
        mock_create_palo.return_value = mock_agent

        # Import NODE getters here to ensure patches apply if they do lazy loading, 
        # or if we need to reload. 
        # Since they are specific functions, we just call them.
        from backend.src.sub_agents.aci import get_aci_agent_node
        from backend.src.sub_agents.infoblox import get_infoblox_agent_node
        from backend.src.sub_agents.palo_alto import get_palo_alto_agent_node

        # Test ACI
        print("Testing ACI Agent...")
        node = get_aci_agent_node(config)
        state = {"messages": [HumanMessage(content="Check diagnostics")]}
        result = node(state)
        print(f"Result: {result}")
        assert isinstance(result, SubAgentResult)
        assert result.status == AgentStatus.SUCCESS
        
        # Test Infoblox
        print("\nTesting Infoblox Agent...")
        node = get_infoblox_agent_node(config)
        result = node(state)
        print(f"Result: {result}")
        assert isinstance(result, SubAgentResult)
        assert result.status == AgentStatus.SUCCESS

        # Test Palo Alto
        print("\nTesting Palo Alto Agent...")
        node = get_palo_alto_agent_node(config)
        result = node(state)
        print(f"Result: {result}")
        assert isinstance(result, SubAgentResult)
        assert result.status == AgentStatus.SUCCESS

if __name__ == "__main__":
    try:
        test_agents_mocked()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
