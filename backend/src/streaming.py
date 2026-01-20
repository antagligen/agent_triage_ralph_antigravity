import json
from typing import Any, AsyncGenerator, Dict, Optional
from datetime import datetime, timezone


async def stream_graph_events(
    workflow: Any,
    inputs: Dict[str, Any],
    run_config: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """
    Generator that creates SSE events from the LangGraph stream.

    Uses astream_events() to capture detailed lifecycle events from sub-agents:
    - on_chain_start: When a sub-agent begins execution
    - on_tool_start: When a tool is being called
    - on_chain_end: When a sub-agent finishes execution
    """
    if run_config is None:
        run_config = {}

    # Events we care about for sub-agent thought streaming
    target_events = {"on_chain_start", "on_tool_start", "on_chain_end"}

    async for event in workflow.astream_events(inputs, config=run_config, version="v2"):
        event_type = event.get("event", "")

        # Filter to only the events we care about
        if event_type not in target_events:
            continue

        # Extract metadata for context
        metadata = event.get("metadata", {})
        data = event.get("data", {})
        name = event.get("name", "")

        # Get the langgraph node name from metadata (tells us which agent)
        node_name = metadata.get("langgraph_node", "")

        # Skip events without a node context
        if not node_name:
            continue

        # Build the thought event based on event type
        thought_data: Dict[str, Any] = {
            "node": node_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if event_type == "on_chain_start":
            thought_data["status"] = "chain_start"
            thought_data["message"] = f"Starting {name or node_name}..."

        elif event_type == "on_tool_start":
            tool_name = name or "unknown tool"
            tool_input = data.get("input", {})
            thought_data["status"] = "tool_start"
            thought_data["message"] = f"Calling tool: {tool_name}"
            thought_data["tool_name"] = tool_name
            if tool_input:
                thought_data["tool_input"] = tool_input

        elif event_type == "on_chain_end":
            thought_data["status"] = "chain_end"
            thought_data["message"] = f"Finished {name or node_name}"
            # Include output summary if available
            output = data.get("output", None)
            if output and isinstance(output, dict):
                # Summarize output for display
                thought_data["output_keys"] = list(output.keys())

        # Emit as SSE thought event
        sse_data = json.dumps(thought_data)
        yield f"event: thought\ndata: {sse_data}\n\n"

        # --- Legacy state update handling for backwards compatibility ---
        # Also emit triage_report if present in output
        if event_type == "on_chain_end":
            output = data.get("output", {})
            if isinstance(output, dict):
                # Handle Triage Report
                if "triage_report" in output and output["triage_report"]:
                    report = output["triage_report"]
                    # Convert Pydantic model to dict
                    if hasattr(report, "dict"):
                        report_data = report.dict()
                    elif hasattr(report, "model_dump"):
                        report_data = report.model_dump()
                    else:
                        report_data = report  # assume dict if not pydantic

                    report_json = json.dumps(report_data)
                    yield f"event: triage_report\ndata: {report_json}\n\n"

                # Handle routing info for debugging
                if "next_node" in output:
                    routing_data = json.dumps({"routing": output["next_node"]})
                    yield f"event: routing\ndata: {routing_data}\n\n"
