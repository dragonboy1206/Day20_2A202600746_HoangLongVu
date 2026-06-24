"""Supervisor / router – decides which worker should run next.

Educational notes:
- Routing policy is state-driven: checks which fields are missing
- Tracks consecutive failures to prevent infinite retry loops
- Uses max_iterations as hard stop
"""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_FAILURES = 2


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop.

    Routing policy:
    - Check consecutive failures → stop if too many
    - research_notes is None → researcher
    - analysis_notes is None → analyst
    - final_answer is None → writer
    - all filled → done
    """

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        settings = get_settings()
        with trace_span("supervisor", {"iteration": state.iteration}) as span:
            agent_names = ("researcher", "analyst", "writer")
            consecutive_failures = sum(
                1 for e in reversed(state.errors) if e.split(":")[0] in agent_names
            )

            if state.iteration >= settings.max_iterations:
                logger.warning("Max iterations (%d) reached, stopping", settings.max_iterations)
                next_route = "done"
            elif consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.warning("Too many consecutive failures (%d), stopping", consecutive_failures)
                next_route = "done"
            elif state.research_notes is None:
                next_route = AgentName.RESEARCHER
            elif state.analysis_notes is None:
                next_route = AgentName.ANALYST
            elif state.final_answer is None:
                next_route = AgentName.WRITER
            else:
                next_route = "done"

            span["next_route"] = next_route
            span["consecutive_failures"] = consecutive_failures
            state.record_route(f"supervisor→{next_route}")
            return state
