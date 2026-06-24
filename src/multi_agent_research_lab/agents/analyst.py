"""Analyst agent – turns research notes into structured insights.

Educational notes:
- Uses tenacity for retry on transient LLM failures
- Validates output before storing in shared state
- Logs detailed trace for debugging
"""

import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

_MIN_ANSWER_LENGTH = 20


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _call_llm(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("analyst", {"has_research": state.research_notes is not None}) as span:
            research = state.research_notes or "(không có ghi chú nghiên cứu)"
            system_prompt = (
                "Bạn là nhà phân tích. Dựa trên bản ghi chú nghiên cứu, "
                "hãy phân tích sâu hơn, trích xuất các khẳng định chính, "
                "so sánh các quan điểm khác nhau, và đánh giá độ tin cậy của bằng chứng. "
                "Trả lời bằng tiếng Việt."
            )
            user_prompt = (
                f"Ghi chú nghiên cứu:\n{research}\n\n"
                "Hãy phân tích với các mục:\n"
                "1. Các khẳng định chính\n"
                "2. So sánh quan điểm\n"
                "3. Đánh giá bằng chứng\n"
                "4. Kết luận phân tích"
            )

            try:
                response = self._call_llm(system_prompt=system_prompt, user_prompt=user_prompt)
            except Exception as exc:
                logger.error("Analyst LLM call failed: %s", exc)
                state.errors.append(f"analyst: {exc}")
                span["error"] = str(exc)
                return state

            content = response.content.strip()
            if len(content) < _MIN_ANSWER_LENGTH:
                logger.warning("Analyst output too short (%d chars), using fallback", len(content))
                content = f"[Fallback] Phân tích cho: {state.request.query}"
                state.errors.append("analyst: output too short, used fallback")

            state.analysis_notes = content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                    },
                )
            )
            span["tokens_in"] = response.input_tokens
            span["tokens_out"] = response.output_tokens
            state.record_route("analyst")
            return state
