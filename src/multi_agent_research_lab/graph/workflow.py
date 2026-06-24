"""Multi-agent workflow – orchestrates supervisor → worker → supervisor loop.

Educational notes:
- No LangGraph dependency needed for this simple loop
- Each iteration: supervisor decides → worker executes → state updates
- Trace spans record duration and metadata for each step
"""

import logging
from typing import Literal

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    The workflow follows a simple supervisor → worker → supervisor loop:
      1. Supervisor inspects state and picks next worker.
      2. Worker executes and updates state.
      3. Repeat until supervisor says "done" or max iterations reached.
    """

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

    def _resolve_route(self, route: str) -> Literal["researcher", "analyst", "writer", "done"]:
        if "researcher" in route:
            return "researcher"
        if "analyst" in route:
            return "analyst"
        if "writer" in route:
            return "writer"
        return "done"

    def build(self) -> None:
        pass

    def run(self, state: ResearchState) -> ResearchState:
        settings = get_settings()
        max_iter = settings.max_iterations

        for i in range(max_iter):
            with trace_span("workflow_iteration", {"iteration": i}) as span:
                state = self.supervisor.run(state)
                last_route = state.route_history[-1] if state.route_history else ""
                target = self._resolve_route(last_route)

                span["target_agent"] = target

                if target == "done":
                    logger.info("Workflow done at iteration %d", i)
                    break

                logger.info("Iteration %d: running %s", i, target)

                if target == "researcher":
                    state = self.researcher.run(state)
                elif target == "analyst":
                    state = self.analyst.run(state)
                elif target == "writer":
                    state = self.writer.run(state)

        return state
