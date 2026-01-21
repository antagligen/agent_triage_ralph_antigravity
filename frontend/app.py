import streamlit as st
import requests
import json
import os
import logic
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
logic.initialize_session_state(st.session_state)

def get_agent_display_name(node_name: str) -> str:
    """Convert raw node name to properly formatted display label."""
    return logic.get_agent_display_name(node_name)

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
                                    # Handle thought event via logic module
                                    delta = logic.handle_thought_event(data, st.session_state)
                                    if delta:
                                        thought_text += delta
                                        thought_expander.markdown(thought_text)

                                    # Check if we need to rerun (new tab created)
                                    if st.session_state.get("new_tab_created", False):
                                        # We defer the rerun until the end of the loop or handle it immediately?
                                        # In the previous code it set a flag.
                                        # logic.handle_thought_event sets st.session_state["new_tab_created"] = True
                                        pass

                                elif event_type == "routing":
                                    # Handle routing event
                                    delta = logic.handle_routing_event(data)
                                    thought_text += delta
                                    thought_expander.markdown(thought_text)

                                elif event_type == "triage_report":
                                    # Handle Triage Report
                                    delta = logic.handle_triage_report(data)
                                    full_response += delta
                                    message_placeholder.markdown(full_response)

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
