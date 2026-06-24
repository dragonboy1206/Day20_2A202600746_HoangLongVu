"""Researcher agent – collects sources and creates concise research notes.

Educational notes:
- Uses tenacity for retry on transient LLM failures
- Validates output before storing in shared state
- Logs detailed trace for debugging
"""

import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

_MIN_ANSWER_LENGTH = 20


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _call_llm(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("researcher", {"query": state.request.query}) as span:
            system_prompt = (
                "Bạn là trợ lý nghiên cứu. Dựa trên câu hỏi của người dùng, "
                "hãy tạo một bản ghi chú nghiên cứu ngắn gọn, có cấu trúc rõ ràng. "
                "Liệt kê các ý chính, khái niệm quan trọng, và các nguồn tham khảo nếu có. "
                "Trả lời bằng tiếng Việt."
            )
            user_prompt = (
                f"Câu hỏi nghiên cứu: {state.request.query}\n\n"
                "Hãy tạo bản ghi chú nghiên cứu với các mục:\n"
                "1. Tóm tắt vấn đề\n"
                "2. Các khái niệm chính\n"
                "3. Chi tiết quan trọng\n"
                "4. Các nguồn tham khảo gợi ý"
            )

            try:
                response = self._call_llm(system_prompt=system_prompt, user_prompt=user_prompt)
            except Exception as exc:
                logger.error("Researcher LLM call failed: %s", exc)
                state.errors.append(f"researcher: {exc}")
                span["error"] = str(exc)
                return state

            content = response.content.strip()
            if len(content) < _MIN_ANSWER_LENGTH:
                logger.warning("Researcher output too short (%d chars)", len(content))
                content = f"[Fallback] Ghi chú nghiên cứu cho: {state.request.query}"
                state.errors.append("researcher: output too short, used fallback")

            source = SourceDocument(
                title="LLM-generated research notes",
                snippet=content[:500],
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )

            state.sources.append(source)
            state.research_notes = content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                    },
                )
            )
            span["tokens_in"] = response.input_tokens
            span["tokens_out"] = response.output_tokens
            state.record_route("researcher")
            return state
