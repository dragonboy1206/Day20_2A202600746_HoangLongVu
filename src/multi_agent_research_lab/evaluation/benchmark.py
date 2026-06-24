"""Benchmark – single-agent vs multi-agent comparison.

Educational notes:
- Measures latency, token usage, citation coverage, and quality score
- Quality score is heuristic-based (length + structure)
- Citation coverage measures how many claims have supporting sources
"""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, token usage, and return metrics."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    total_input = sum(
        r.metadata.get("input_tokens", 0) or 0 for r in state.agent_results
    )
    total_output = sum(
        r.metadata.get("output_tokens", 0) or 0 for r in state.agent_results
    )
    estimated_cost = 0.0

    citation_coverage = 0.0
    if state.sources:
        claims = state.analysis_notes.count("1.") + 1 if state.analysis_notes else 1
        cited = len(state.sources)
        citation_coverage = min(cited / max(claims, 1), 1.0)

    quality_score = None
    if state.final_answer:
        length = len(state.final_answer)
        if length > 200:
            quality_score = 8.0
        elif length > 100:
            quality_score = 6.0
        elif length > 20:
            quality_score = 4.0
        else:
            quality_score = 2.0

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality_score,
        notes=(
            f"tokens_in={total_input} tokens_out={total_output} "
            f"citations={citation_coverage:.0%}"
        ),
    )
    return state, metrics
