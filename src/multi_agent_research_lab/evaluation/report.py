"""Benchmark report rendering.

Educational notes:
- Renders comparison table for single-agent vs multi-agent
- Includes trace summary for debugging
"""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with comparison table."""

    lines = [
        "# Benchmark Report",
        "",
        "## Comparison: Single-Agent vs Multi-Agent",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality (0-10) | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "0.00" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "-" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |"
        )

    lines.extend([
        "",
        "## Analysis",
        "",
        "- **Latency**: Multi-agent will be higher due to multiple LLM calls",
        "- **Quality**: Multi-agent should produce more structured, cited responses",
        "- **Cost**: Both are 0 with Ollama (local model)",
        "",
        "## Trace Summary",
        "",
        "Each agent records: name, duration, input/output tokens, route, errors.",
        "Check `state.trace` for detailed execution log.",
        "",
    ])
    return "\n".join(lines) + "\n"
