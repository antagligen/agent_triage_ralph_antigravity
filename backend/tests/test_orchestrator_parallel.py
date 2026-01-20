import pytest
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from backend.src.config import AppConfig, SubAgentConfig
from backend.src.orchestrator import build_graph, AgentState, OrchestratorDecision
from backend.src.models import SubAgentResult, AgentStatus
from langchain_core.messages import HumanMessage
import os

os.environ["OPENAI_API_KEY"] = "sk-test"

@pytest.fixture
def mock_config():
    return AppConfig(
        orchestrator_provider="openai",
        orchestrator_model="gpt-4o",
        system_prompt="You are a helpful assistant.",
        sub_agents=[
            SubAgentConfig(name="test_agent", description="test", tools=["test_tool"])
        ]
    )

def test_parallel_execution_routing(mock_config):
    """
    Test that the orchestrator routes to multiple agents in parallel
    when 'sub_agents' (or specific list) is returned.
    """
    # Mock global get_llm to cover both orchestrator and sub-agents
    with patch("backend.src.llm_factory.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # Mock structured output
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        # Decision: Run generic sub_agents (which maps to aci, palo_alto)
        decision = OrchestratorDecision(
            next_steps=["sub_agents"],
            reasoning="Testing parallel fan-out"
        )
        mock_structured.invoke.return_value = decision

        # Build Graph
        app = build_graph(mock_config)

        # Initial State
        initial_state: Dict[str, Any] = {
            "messages": [HumanMessage(content="Check firewall and switch for 10.0.0.1")],
            "incident_data": {"source_ip": "10.0.0.1", "destination_ip": "10.0.0.2"}
        }

        # Run Graph
        # We expect: Orchestrator -> [ACI, Palo Alto] -> END
        # The result should contain sub_agent_results from both.

        # We need to mock the sub-agents internal calls to avoid actual API calls (even though they are mocked in `sub_agents` module, let's be safe or rely on their mocks).
        # Since `sub_agents` modules use their own `create_react_agent` and `llm`, we might strictly need to patch those too if we want pure unit test.
        # But `sub_agents` already have mock tools. Let's assume they run fast.

        # However, `create_react_agent` inside sub-agents will try to use `ChatOpenAI`.
        # We need to ensure `get_llm` returns a working mock for them too.
        # `get_llm` is globally patched above.

        # We need the mock_llm to behave "reasonably" for the agents too.
        # React agents need to output tool calls or final answer.
        # This is getting complex to mock fully end-to-end.

        # EASIER: We verify the `fan_out_router` logic directly or inspecting graph structure?
        # NO, better to verify graph execution.

        # Let's make the mock_llm return a generic "Final Answer" for the sub-agents so they finish immediately.
        # The React agent loop: LLM -> Tool? -> LLM -> Finish.
        # If LLM returns just content, it finishes.

        mock_llm.invoke.return_value = MagicMock(content="Mocked agent response", tool_calls=[])

        result = app.invoke(initial_state)

        # Check if we have results
        assert "sub_agent_results" in result
        results = result["sub_agent_results"]
        assert len(results) >= 2 # Should have ACI and Palo Alto

        # Identify sources (summaries should differ or we check logic)
        # Since we mocked LLM globally, they might return same summary unless we differentiate based on input.
        # But the *number* of results confirms parallel execution branches were taken.

def test_input_validation_routing(mock_config):
    """
    Test routing to Infoblox when IPs are missing.
    """
    app = build_graph(mock_config)
    initial_state: Dict[str, Any] = {
        "messages": [HumanMessage(content="Help me")],
        "incident_data": {} # Missing IPs
    }

    # We don't need to patch LLM here because orchestrator has hard logic before LLM.
    # But `get_llm` is called in factory, so we still expect it or need to patch factory.

    with patch("backend.src.llm_factory.get_llm"):
         result = app.invoke(initial_state)

         # Should route to Infoblox
         decision = result["decision"]
         assert "infoblox" in decision.next_steps

         # Infoblox agent would run.
         # Result should contain sub_agent_results (size 1)
         assert "sub_agent_results" in result
         assert len(result["sub_agent_results"]) == 1
