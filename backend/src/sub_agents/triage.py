from typing import List, Dict, Any, cast
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from ..config import AppConfig
from ..llm_factory import get_llm
from ..models import TriageReport, SubAgentResult

def get_triage_node(config: AppConfig):
    """
    Factory function to create the triage node.
    """
    llm = get_llm(config.orchestrator_provider, config.orchestrator_model, temperature=0)
    structured_llm = llm.with_structured_output(TriageReport)

    def triage_node(state: Dict[str, Any]):
        """
        Triage node that aggregates results and generates a final report.
        """
        sub_agent_results: List[SubAgentResult] = state.get("sub_agent_results", [])
        incident_data = state.get("incident_data", {})

        # Prepare payload for the LLM
        summaries = []
        for res in sub_agent_results:
            summaries.append(f"Agent Status: {res.status}\nSummary: {res.summary}")
        
        summaries_text = "\n---\n".join(summaries)
        
        system_prompt = (
            "You are a Senior Site Reliability Engineer (SRE). "
            "Your task is to analyze the following connectivity triage reports from various sub-agents "
            "and determine the root cause of the issue.\n\n"
            "Provide a concise Root Cause, Detailed Explanation, and Recommended Action."
        )
        
        user_content = (
            f"Incident Data: {incident_data}\n\n"
            f"Sub-Agent Reports:\n{summaries_text}"
        )

        try:
            report = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ])
            # If for some reason invoke doesn't return the model (e.g. mocking issues), handle it
            if not isinstance(report, TriageReport):
                 # Fallback/Error handling if the structured output fails to parse into the object directly
                 # In runtime with real LLM this should work if with_structured_output is correct
                 pass
                 
        except Exception as e:
            report = TriageReport(
                root_cause="Analysis Failed",
                details=f"Failed to generate triage report due to error: {str(e)}",
                action="Manual investigation required"
            )

        return {"triage_report": report}

    return triage_node
