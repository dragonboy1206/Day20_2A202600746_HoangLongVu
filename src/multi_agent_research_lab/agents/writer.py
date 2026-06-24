"""Writer agent – produces final answer from research and analysis notes.

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


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _call_llm(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("writer", {"query": state.request.query}) as span:
            research = state.research_notes or "(không có ghi chú nghiên cứu)"
            analysis = state.analysis_notes or "(không có phân tích)"
            audience = state.request.audience

            system_prompt = (
                f"Bạn là nhà viết nội dung chuyên nghiệp. Đối tượng độc giả: {audience}. "
                "Dựa trên ghi chú nghiên cứu và phân tích, hãy viết câu trả lời rõ ràng, "
                "mạch lạc, có trích dẫn nguồn khi có thể. Trả lời bằng tiếng Việt."
            )
            user_prompt = (
                f"Câu hỏi gốc: {state.request.query}\n\n"
                f"Ghi chú nghiên cứu:\n{research}\n\n"
                f"Phân tích:\n{analysis}\n\n"
                "Hãy viết câu trả lời hoàn chỉnh, dễ hiểu cho đối tượng độc giả."
            )

            try:
                response = self._call_llm(system_prompt=system_prompt, user_prompt=user_prompt)
            except Exception as exc:
                logger.error("Writer LLM call failed: %s", exc)
                state.errors.append(f"writer: {exc}")
                span["error"] = str(exc)
                return state

            content = response.content.strip()
            if len(content) < _MIN_ANSWER_LENGTH:
                logger.warning("Writer output too short (%d chars), using fallback", len(content))
                content = f"[Fallback] Câu trả lời cho: {state.request.query}"
                state.errors.append("writer: output too short, used fallback")

            state.final_answer = content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                    },
                )
            )
            span["tokens_in"] = response.input_tokens
            span["tokens_out"] = response.output_tokens
            state.record_route("writer")
            return state
