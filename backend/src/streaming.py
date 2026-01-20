import json
from typing import Any, AsyncGenerator, Dict, Optional

async def stream_graph_events(workflow: Any, inputs: Dict[str, Any], run_config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
    """
    Generator that creates SSE events from the LangGraph stream.
    """
    if run_config is None:
        run_config = {}

    # Use .astream_events or .stream for detailed updates
    # simple .stream returns state updates
    async for event in workflow.astream(inputs, config=run_config, stream_mode="updates"):
        # Helper to format SSE
        # event is a dict of {node_name: state_update}
        
        for node_name, state_update in event.items():
            # We treat node updates as "thoughts" unless it's the final answer
            
            # If we have a new message
            if "messages" in state_update:
                messages = state_update["messages"]
                # For this simple graph, messages is usually a single message or list of messages
                if not isinstance(messages, list):
                    messages = [messages]
                
                for msg in messages:
                    # Construct valid JSON data
                    data = json.dumps({
                        "node": node_name,
                        "content": msg.content,
                        "type": msg.type
                    })
                    
                    if node_name == "orchestrator":
                        yield f"event: thought\ndata: {data}\n\n"
                    elif node_name == "network_specialist":
                         yield f"event: thought\ndata: {data}\n\n"
            
            # Handle Decision (Reasoning)
            if "decision" in state_update:
                decision = state_update["decision"]
                reasoning = None
                if isinstance(decision, dict):
                    reasoning = decision.get("reasoning")
                else:
                    reasoning = getattr(decision, "reasoning", None)
                    
                if reasoning:
                    data = json.dumps({
                        "node": node_name,
                        "content": reasoning,
                        "type": "ai"
                    })
                    yield f"event: thought\ndata: {data}\n\n"
                    
            # Handle Triage Report
            if "triage_report" in state_update and state_update["triage_report"]:
                report = state_update["triage_report"]
                # Convert Pydantic model to dict
                if hasattr(report, "dict"):
                     report_data = report.dict()
                else:
                     report_data = report # assume dict if not pydantic
                     
                data = json.dumps(report_data)
                yield f"event: triage_report\ndata: {data}\n\n"

            # If we have next_node info (useful for debugging)
            if "next_node" in state_update:
                 data = json.dumps({"routing": state_update["next_node"]})
                 yield f"event: routing\ndata: {data}\n\n"
