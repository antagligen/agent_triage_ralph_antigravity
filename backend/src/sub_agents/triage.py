from typing import List, Dict, Any, cast
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from ..config import AppConfig, load_system_prompt
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

        # Separate successful and failed results
        successful_results = []
        failed_results = []
        for res in sub_agent_results:
            if res.status.value == "FAILURE":
                failed_results.append(res)
            else:
                successful_results.append(res)

        # Build list of failed agent names
        failed_agent_names = [res.agent_name for res in failed_results]

        # Prepare payload for the LLM
        success_summaries = []
        for res in successful_results:
            success_summaries.append(f"Agent: {res.agent_name}\nStatus: {res.status}\nSummary: {res.summary}")

        failure_summaries = []
        for res in failed_results:
            failure_summaries.append(f"Agent: {res.agent_name}\nStatus: {res.status}\nError: {res.summary}")

        success_text = "\n---\n".join(success_summaries) if success_summaries else "No successful results."
        failure_text = "\n---\n".join(failure_summaries) if failure_summaries else "None."

        system_prompt = load_system_prompt("triage")

        user_content = (
            f"Incident Data: {incident_data}\n\n"
            f"Successful Agent Reports:\n{success_text}\n\n"
            f"Failed Agents:\n{failure_text}"
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

            # Ensure failed_agents is populated even if LLM didn't return it
            if isinstance(report, TriageReport):
                report.failed_agents = failed_agent_names

        except Exception as e:
            report = TriageReport(
                root_cause="Analysis Failed",
                details=f"Failed to generate triage report due to error: {str(e)}",
                action="Manual investigation required",
                failed_agents=failed_agent_names
            )

        return {"triage_report": report}

    return triage_node
