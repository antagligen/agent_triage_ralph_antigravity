import streamlit as st
import requests
import json
import os

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
print(f"Backend URL configured: {BACKEND_URL}")
API_CHAT_URL = f"{BACKEND_URL}/chat"

st.set_page_config(
    page_title="Ralph - AI Troubleshooting Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Ralph - AI Troubleshooting Agent")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

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
        index=0
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
        st.rerun()

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If we saved thoughts, we could display them here too,
        # but for now let's focus on the conversation flow.

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

                                    # Format status indicator
                                    status_icon = "🔄" if status == "chain_start" else "🔧" if status == "tool_start" else "✅" if status == "chain_end" else "💭"

                                    # Append to the thought log
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

        except Exception as e:
            st.error(f"Connection failed: {e}")
