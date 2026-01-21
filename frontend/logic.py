import json
from datetime import datetime
from typing import Dict, Any, List

# Display name mapping for sub-agent tabs (raw node name -> display label)
AGENT_DISPLAY_NAMES: dict[str, str] = {
    "aci": "ACI",
    "infoblox": "Infoblox",
    "palo_alto": "Palo Alto",
    "triage": "Triage",
}

def initialize_session_state(state: Dict[str, Any]) -> None:
    """Initializes the session state with default values."""
    if "messages" not in state:
        state["messages"] = []

    # Tab state for sub-agents: {agent_name: {created: bool, logs: list, status: str, has_new_activity: bool}}
    if "agent_tabs" not in state:
        state["agent_tabs"] = {}

    # Track order of tab creation for consistent display
    if "tab_order" not in state:
        state["tab_order"] = []

def get_agent_display_name(node_name: str) -> str:
    """Convert raw node name to properly formatted display label."""
    return AGENT_DISPLAY_NAMES.get(node_name.lower(), node_name.title())

def process_event(data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a streaming event and updates the session state.
    Returns a dictionary with updates for the UI (e.g. thought_text, full_response).
    """
    ui_updates = {
        "thought_text_delta": "",
        "full_response_delta": "",
        "new_tab_created": False
    }

    event_type = data.get("type", "thought") # Default to thought if not specified in wrapper

    # Note: The data passed here is usually the inner 'data' from the SSE event
    # But checking how app.py parses it:
    # event_type comes from "event:" line
    # data comes from "data:" line

    # Let's assume the caller handles the top-level event type parsing and passes
    # the event_type as an argument or we handle the data dict directly.
    # Refactoring slightly to match app.py flow: caller parses line, gets event_type and data.

    # Actually, for cleaner separation, let's make this function receive the refined data
    # plus the event_type string.

    pass # Implementation details below in the actual write
    return ui_updates

def format_timestamp(timestamp_str: str) -> str:
    """Formats an ISO timestamp string to HH:MM:SS."""
    if not timestamp_str:
        return ""
    try:
        # Handle ISO format with potential Z or offset
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return ""

def handle_thought_event(data: Dict[str, Any], state: Dict[str, Any]) -> str:
    """
    Handles a 'thought' event.
    Updates agent_tabs in state.
    Returns the markdown text delta to be added to the thought expander.
    """
    node = data.get("node", "Unknown")
    status = data.get("status", "")
    message = data.get("message", "")
    timestamp_str = data.get("timestamp", "")

    thought_text_delta = ""

    # Check if this is a sub-agent (not orchestrator)
    is_subagent = node.lower() != "orchestrator" and node != "Unknown"

    if is_subagent:
        # Create tab for new sub-agent on first call
        if node not in state["agent_tabs"]:
            state["agent_tabs"][node] = {
                "created": True,
                "logs": [],
                "status": "running",
                "has_new_activity": True
            }
            # Prevent duplicate entries in tab_order
            if node not in state["tab_order"]:
                state["tab_order"].append(node)
                state["new_tab_created"] = True # handled by caller to trigger rerun

        # Update sub-agent status
        display_name = get_agent_display_name(node)

        if status == "chain_start":
            state["agent_tabs"][node]["status"] = "running"
            thought_text_delta += f"🔄 **CALLING SUB-AGENT: {display_name}**\n\n"
        elif status == "chain_end":
            state["agent_tabs"][node]["status"] = "complete"
            thought_text_delta += f"✅ **{display_name} Complete**\n\n"

        # Route event to sub-agent's log
        formatted_time = format_timestamp(timestamp_str)
        status_icon = "🔄" if status == "chain_start" else "🔧" if status == "tool_start" else "✅" if status == "chain_end" else "💭"

        log_entry_data = {
            "timestamp": formatted_time,
            "status": status,
            "icon": status_icon,
            "message": message
        }

        state["agent_tabs"][node]["logs"].append(log_entry_data)
        state["agent_tabs"][node]["has_new_activity"] = True

    else:
        # Orchestrator events go to the thinking expander
        status_icon = "🔄" if status == "chain_start" else "🔧" if status == "tool_start" else "✅" if status == "chain_end" else "💭"
        thought_text_delta += f"{status_icon} **[{node}]**: {message}\n\n"

    return thought_text_delta

def handle_routing_event(data: Dict[str, Any]) -> str:
    next_node = data.get("routing", "")
    return f"*Routing to: `{next_node}`*\n\n"

def handle_triage_report(data: Dict[str, Any]) -> str:
    root_cause = data.get("root_cause", "Unknown")
    action = data.get("action", "No action specified")
    details = data.get("details", "")

    return f"""
### 🚨 Triage Report
**Root Cause:** {root_cause}

**Action:** {action}

**Details:** {details}
"""
