import pytest
import sys
import os
from typing import Dict, Any, List

# Ensure backend/frontend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.logic import initialize_session_state, get_agent_display_name, handle_thought_event, handle_routing_event, handle_triage_report

def test_initialize_session_state() -> None:
    state: Dict[str, Any] = {}
    initialize_session_state(state)
    assert "messages" in state
    assert state["messages"] == []
    assert "agent_tabs" in state
    assert state["agent_tabs"] == {}
    assert "tab_order" in state
    assert state["tab_order"] == []

    # Should not overwrite existing state
    state["messages"] = ["existing"]
    initialize_session_state(state)
    assert state["messages"] == ["existing"]

def test_get_agent_display_name() -> None:
    assert get_agent_display_name("aci") == "ACI"
    assert get_agent_display_name("infoblox") == "Infoblox"
    assert get_agent_display_name("palo_alto") == "Palo Alto"
    assert get_agent_display_name("triage") == "Triage"
    assert get_agent_display_name("unknown_agent") == "Unknown_Agent"

def test_handle_thought_event_new_tab() -> None:
    state: Dict[str, Any] = {"agent_tabs": {}, "tab_order": []}
    data: Dict[str, Any] = {
        "node": "aci",
        "status": "chain_start",
        "message": "Starting ACI",
        "timestamp": "2023-10-27T10:00:00Z"
    }

    delta = handle_thought_event(data, state)

    assert "aci" in state["agent_tabs"]
    assert state["tab_order"] == ["aci"]
    assert state["agent_tabs"]["aci"]["status"] == "running"
    assert "CALLING SUB-AGENT: ACI" in delta
    assert state["new_tab_created"] is True

def test_handle_thought_event_existing_tab() -> None:
    state: Dict[str, Any] = {
        "agent_tabs": {
            "aci": {
                "created": True,
                "logs": [],
                "status": "running",
                "has_new_activity": False
            }
        },
        "tab_order": ["aci"]
    }
    data: Dict[str, Any] = {
        "node": "aci",
        "status": "tool_start",
        "message": "Running tool",
        "timestamp": "2023-10-27T10:00:05Z"
    }

    delta = handle_thought_event(data, state)

    assert len(state["agent_tabs"]["aci"]["logs"]) == 1
    log = state["agent_tabs"]["aci"]["logs"][0]
    assert log["status"] == "tool_start"
    assert log["message"] == "Running tool"
    assert log["timestamp"] == "10:00:05"
    assert state["agent_tabs"]["aci"]["has_new_activity"] is True
    assert delta == "" # No delta for existing sub-agent logs

def test_handle_thought_event_orchestrator() -> None:
    state: Dict[str, Any] = {"agent_tabs": {}, "tab_order": []}
    data: Dict[str, Any] = {
        "node": "Orchestrator",
        "status": "chain_start",
        "message": "Thinking...",
        "timestamp": "2023-10-27T10:00:00Z"
    }

    delta = handle_thought_event(data, state)

    assert "Orchestrator" not in state["agent_tabs"]
    assert "Thinking..." in delta

def test_handle_routing_event() -> None:
    data: Dict[str, Any] = {"routing": "aci"}
    delta = handle_routing_event(data)
    assert "*Routing to: `aci`*" in delta

def test_handle_triage_report() -> None:
    data: Dict[str, Any] = {
        "root_cause": "Network issue",
        "action": "Restart switch",
        "details": "Switch 1 is down"
    }
    delta = handle_triage_report(data)
    assert "Network issue" in delta
    assert "Restart switch" in delta
    assert "Switch 1 is down" in delta
