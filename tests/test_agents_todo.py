from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "supervisor→researcher"


def test_supervisor_routes_to_analyst() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state.research_notes = "some notes"
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "supervisor→analyst"


def test_supervisor_routes_to_writer() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state.research_notes = "some notes"
    state.analysis_notes = "some analysis"
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "supervisor→writer"


def test_supervisor_done_when_all_filled() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state.research_notes = "notes"
    state.analysis_notes = "analysis"
    state.final_answer = "answer"
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "supervisor→done"
