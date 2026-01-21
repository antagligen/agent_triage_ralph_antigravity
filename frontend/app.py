import streamlit as st
import requests
import json
import os
from datetime import datetime

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
print(f"Backend URL configured: {BACKEND_URL}")
API_CHAT_URL = f"{BACKEND_URL}/chat"

st.set_page_config(
    page_title="Ralph - AI Troubleshooting Agent",
    page_icon="🤖",
    layout="wide"
)

# --- Load Custom CSS ---
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    try:
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"style.css not found at {css_path}")

load_css()

st.title("🤖 Ralph - AI Troubleshooting Agent")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tab state for sub-agents: {agent_name: {created: bool, logs: list, status: str, has_new_activity: bool}}
if "agent_tabs" not in st.session_state:
    st.session_state.agent_tabs = {}

# Track order of tab creation for consistent display
if "tab_order" not in st.session_state:
    st.session_state.tab_order = []

# Display name mapping for sub-agent tabs (raw node name -> display label)
AGENT_DISPLAY_NAMES: dict[str, str] = {
    "aci": "ACI",
    "infoblox": "Infoblox",
    "palo_alto": "Palo Alto",
    "triage": "Triage",
}


def get_agent_display_name(node_name: str) -> str:
    """Convert raw node name to properly formatted display label."""
    return AGENT_DISPLAY_NAMES.get(node_name.lower(), node_name.title())

# --- Helper Functions ---
def check_backend_health():
    """Checks if the backend is reachable."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    # Model Provider Selection
    provider = st.radio(
        "Model Provider",
        ["OpenAI", "Gemini"],
        index=1
    )

    # Model Name Selection based on Provider
    if provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    else:
        model_options = ["gemini-2.5-flash"]

    model_name = st.selectbox(
        "Model Name",
        model_options,
        index=0
    )

    st.divider()

    st.header("Connection Status")
    if st.button("Refresh Status"):
        st.rerun()

    is_online = check_backend_health()
    if is_online:
        st.success("🟢 Backend Online")
    else:
        st.error("🔴 Backend Offline")

    st.divider()

    if st.button("Clear History"):
        st.session_state.messages = []
        st.session_state.agent_tabs = {}
        st.session_state.tab_order = []
        st.rerun()

# --- Tab Container ---
# Build tab labels: Orchestrator first, then sub-agents in order of first call
tab_labels = ["Orchestrator"]
for name in st.session_state.tab_order:
    display_name = get_agent_display_name(name)
    if st.session_state.agent_tabs[name].get("has_new_activity", False):
        display_name += " 🟢"
    tab_labels.append(display_name)

tabs = st.tabs(tab_labels)

# --- Orchestrator Tab (Main Chat) ---
with tabs[0]:
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Sub-Agent Tabs ---
for i, agent_name in enumerate(st.session_state.tab_order):
    with tabs[i + 1]:
        agent_state = st.session_state.agent_tabs.get(agent_name, {})
        logs = agent_state.get("logs", [])
        status = agent_state.get("status", "idle")
        display_name = get_agent_display_name(agent_name)

        # Check for new activity and offer to clear it
        if agent_state.get("has_new_activity", False):
            if st.button("Mark Read", key=f"mark_read_{agent_name}"):
                st.session_state.agent_tabs[agent_name]["has_new_activity"] = False
                st.rerun()

        # Show status indicator
        if status == "running":
            st.markdown(f"""
                <div class="agent-status-running">
                    <div class="agent-spinner"></div>
                    {display_name} is processing...
                </div>
            """, unsafe_allow_html=True)
        elif status == "complete":
             st.markdown(f"""
                <div class="agent-status-complete">
                    ✅ {display_name} completed
                </div>
            """, unsafe_allow_html=True)

        # Display logs
        if logs:
            logs_html = ""
            for log in logs:
                # Handle legacy string logs if any (defensive)
                if isinstance(log, str):
                    logs_html += f'<div class="log-entry">{log}</div>'
                else:
                    # Map status to CSS class
                    status_slug = log.get('status', 'thought').lower()
                    status_class = f"log-type-{status_slug}"

                    timestamp_html = f'<span class="log-timestamp">{log["timestamp"]}</span>' if log.get("timestamp") else ''

                    logs_html += f"""
                    <div class="log-entry {status_class}">
                        {timestamp_html}
                        <span class="log-icon">{log["icon"]}</span>
                        <span class="log-message">{log["message"]}</span>
                    </div>
                    """

            st.markdown(f"""
            <div class="agent-log-wrapper">
                <div class="agent-log-header">Activity Log</div>
                <div class="agent-log-container">
                    {logs_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("No activity yet.")

# --- Chat Input & Streaming Logic ---
if prompt := st.chat_input("How can I help you troubleshoot?"):
    # 1. Display User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Prepare for Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # We'll use an expander for "Thoughts" that updates in real-time
        thought_expander = st.status("Thinking...", expanded=True)
        thought_text = ""

        full_response = ""

        try:
            # 3. Call Backend API with Streaming
            payload = {
                "message": prompt,
                "model_provider": provider.lower(),  # Backend expects lowercase
                "model_name": model_name
            }

            response = requests.post(
                API_CHAT_URL,
                json=payload,
                stream=True
            )

            if response.status_code == 200:
                # 4. Process SSE Stream
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')

                        if decoded_line.startswith("event:"):
                            event_type = decoded_line.split(":", 1)[1].strip()
                        elif decoded_line.startswith("data:"):
                            data_str = decoded_line.split(":", 1)[1].strip()

                            try:
                                data = json.loads(data_str)

                                if event_type == "thought":
                                    # Handle internal thought events (standardized format)
                                    node = data.get("node", "Unknown")
                                    status = data.get("status", "")
                                    message = data.get("message", "")

                                    # Check if this is a sub-agent (not orchestrator)
                                    is_subagent = node.lower() != "orchestrator" and node != "Unknown"

                                    if is_subagent:
                                        # Create tab for new sub-agent on first call
                                        # Defensive check: handle rapid events that may race
                                        if node not in st.session_state.agent_tabs:
                                            st.session_state.agent_tabs[node] = {
                                                "created": True,
                                                "logs": [],
                                                "status": "running",
                                                "has_new_activity": True
                                            }
                                            # Prevent duplicate entries in tab_order
                                            if node not in st.session_state.tab_order:
                                                st.session_state.tab_order.append(node)
                                                st.session_state.new_tab_created = True

                                        # Update sub-agent status
                                        if status == "chain_start":
                                            st.session_state.agent_tabs[node]["status"] = "running"
                                            # Show minimal status in orchestrator thinking expander
                                            display_name = get_agent_display_name(node)
                                            thought_text += f"🔄 **CALLING SUB-AGENT: {display_name}**\n\n"
                                            thought_expander.markdown(thought_text)
                                        elif status == "chain_end":
                                            st.session_state.agent_tabs[node]["status"] = "complete"
                                            display_name = get_agent_display_name(node)
                                            thought_text += f"✅ **{display_name} Complete**\n\n"
                                            thought_expander.markdown(thought_text)

                                        # Route event to sub-agent's log
                                        timestamp_str = data.get("timestamp", "")
                                        formatted_time = ""
                                        if timestamp_str:
                                            try:
                                                # Handle ISO format with potential Z or offset
                                                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                                formatted_time = dt.strftime("%H:%M:%S")
                                            except ValueError:
                                                formatted_time = ""

                                        status_icon = "🔄" if status == "chain_start" else "🔧" if status == "tool_start" else "✅" if status == "chain_end" else "💭"

                                        # Store structured log entry
                                        log_entry_data = {
                                            "timestamp": formatted_time,
                                            "status": status,
                                            "icon": status_icon,
                                            "message": message
                                        }

                                        st.session_state.agent_tabs[node]["logs"].append(log_entry_data)
                                        st.session_state.agent_tabs[node]["has_new_activity"] = True
                                    else:
                                        # Orchestrator events go to the thinking expander
                                        status_icon = "🔄" if status == "chain_start" else "🔧" if status == "tool_start" else "✅" if status == "chain_end" else "💭"
                                        new_thought = f"{status_icon} **[{node}]**: {message}\n\n"
                                        thought_text += new_thought
                                        thought_expander.markdown(thought_text)

                                elif event_type == "routing":
                                    # Handle routing events
                                    next_node = data.get("routing", "")
                                    thought_text += f"*Routing to: `{next_node}`*\n\n"
                                    thought_expander.markdown(thought_text)

                                elif event_type == "triage_report":
                                    # Handle Triage Report
                                    root_cause = data.get("root_cause", "Unknown")
                                    action = data.get("action", "No action specified")
                                    details = data.get("details", "")

                                    # Format the report
                                    report_md = f"""
                                    ### 🚨 Triage Report
                                    **Root Cause:** {root_cause}

                                    **Action:** {action}

                                    **Details:** {details}
                                    """
                                    full_response += report_md
                                    message_placeholder.markdown(full_response)

                                # We treat the actual message content as part of the thought stream
                                # if it comes from nodes, but usually the 'final' response
                                # comes differently or is just the accumulation of text.
                                # Based on current backend implementation, 'thought' events
                                # contain the content.
                                # Let's assume for now that if node is 'orchestrator'
                                # and it's sending content, it might be the final answer?
                                # Actually the backend streams EVERYTHING as thoughts currently.
                                # We need to decide what constitutes the "Final Answer".
                                # For this pass, we'll append everything to full_response
                                # AND show it in thoughts.

                                # Note: The new standardized format uses `message` field for
                                # thought events, not `content`. The `triage_report` event
                                # handles the final response display.

                            except json.JSONDecodeError:
                                pass # formatting error or keepalive
            else:
                st.error(f"Error: {response.status_code} - {response.text}")

            thought_expander.update(label="Finished Processing", state="complete", expanded=False)
            message_placeholder.markdown(full_response)

            # 5. Save valid response to history
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Force a rerun if a new tab was created so it appears in the UI
            if st.session_state.get("new_tab_created", False):
                st.session_state.new_tab_created = False
                st.rerun()

        except Exception as e:
            st.error(f"Connection failed: {e}")
