import json

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.services import llm_client
from multi_agent_research_lab.services.llm_client import LLMClient


class _FakeResponse:
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {
                "message": {"content": "Xin chao tu Ollama"},
                "prompt_eval_count": 4,
                "eval_count": 5,
            }
        ).encode("utf-8")


def test_ollama_client_uses_chat_api(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse()

    monkeypatch.setattr(llm_client, "urlopen", fake_urlopen)

    settings = Settings(
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3.1:latest",
        TIMEOUT_SECONDS=30,
    )
    response = LLMClient(settings=settings).complete("Ban la tro ly.", "Chao ban")

    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["timeout"] == 30
    assert captured["payload"]["model"] == "llama3.1:latest"
    assert captured["payload"]["stream"] is False
    assert response.content == "Xin chao tu Ollama"
    assert response.input_tokens == 4
    assert response.output_tokens == 5
    assert response.cost_usd == 0.0
