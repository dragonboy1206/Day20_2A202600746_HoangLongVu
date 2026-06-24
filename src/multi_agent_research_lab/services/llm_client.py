"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client with Ollama as the default backend."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion."""

        provider = self.settings.llm_provider.lower().strip()
        if provider == "ollama":
            return self._complete_ollama(system_prompt=system_prompt, user_prompt=user_prompt)

        raise AgentExecutionError(f"Unsupported LLM_PROVIDER: {self.settings.llm_provider}")

    def _complete_ollama(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        url = self.settings.ollama_base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.settings.ollama_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            raise AgentExecutionError(
                "Cannot connect to Ollama. Start Ollama and run "
                f"`ollama pull {self.settings.ollama_model}` first."
            ) from exc
        except TimeoutError as exc:
            raise AgentExecutionError("Ollama request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise AgentExecutionError("Ollama returned invalid JSON.") from exc

        message = data.get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise AgentExecutionError("Ollama returned an empty response.")

        return LLMResponse(
            content=content,
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            cost_usd=0.0,
        )
