"""Command-line entrypoint for the lab starter."""

import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")


def _get_console() -> Console:
    return Console(file=sys.stdout, force_terminal=True)


def _print_safe(text: str, title: str | None = None) -> None:
    console = _get_console()
    try:
        if title:
            console.print(Panel.fit(text, title=title))
        else:
            console.print(text)
    except UnicodeEncodeError:
        sys.stdout.write(text + "\n")


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline using LLMClient directly."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    client = LLMClient()
    system_prompt = (
        "Bạn là trợ lý AI trả lời bằng tiếng Việt. "
        "Hãy trả lời câu hỏi một cách ngắn gọn, rõ ràng."
    )
    try:
        response = client.complete(system_prompt=system_prompt, user_prompt=query)
        state.final_answer = response.content
    except AgentExecutionError as exc:
        state.final_answer = f"Lỗi khi gọi LLM: {exc}"
        state.errors.append(str(exc))

    title = "Single-Agent Baseline"
    _print_safe(state.final_answer or "(no result)", title=title)


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except AgentExecutionError as exc:
        _print_safe(str(exc), title="Error")
        raise typer.Exit(code=1) from exc
    _print_safe(result.final_answer or "(no result)")


if __name__ == "__main__":
    app()
