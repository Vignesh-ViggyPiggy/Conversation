import os
from abc import ABC, abstractmethod

MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 1.0


def _get_temperature() -> float:
    return float(os.environ.get("BRAIN_TEMPERATURE", DEFAULT_TEMPERATURE))


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, messages: list[dict]) -> str:
        ...

    def warm_up(self) -> None:
        """Best-effort: loads model weights now instead of lazily on the
        first real request. No-op by default -- only meaningful for
        providers backed by a local model that has to load weights into
        memory (see LocalProvider)."""


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str | None = None, temperature: float | None = None):
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = model or os.environ.get("BRAIN_MODEL", "claude-sonnet-5")
        self.temperature = temperature if temperature is not None else _get_temperature()

    def chat(self, system: str, messages: list[dict]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            temperature=self.temperature,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class LocalProvider(LLMProvider):
    """Any OpenAI-compatible local server: Ollama, llama.cpp server, LM Studio, vLLM."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
    ):
        from openai import OpenAI

        self.client = OpenAI(
            base_url=base_url or os.environ.get("BRAIN_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.environ.get("BRAIN_API_KEY", "not-needed"),
        )
        self.model = model or os.environ.get("BRAIN_MODEL", "llama3.1")
        self.temperature = temperature if temperature is not None else _get_temperature()

    def chat(self, system: str, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            temperature=self.temperature,
            messages=[{"role": "system", "content": system}, *messages],
        )
        return response.choices[0].message.content

    def warm_up(self) -> None:
        """Ollama-specific trick: POSTing to its native /api/generate
        with no "prompt" field loads the model into memory and returns
        immediately, without generating anything. For an 8B model,
        first-load can take a minute or more (weights coming off disk)
        -- paying that cost here, at startup, means it doesn't land in
        the middle of the first real conversation turn instead.
        keep_alive also gets set here so the model stays resident for
        the session rather than being evicted after Ollama's default
        5-minute idle timeout between turns.

        Silently does nothing if this isn't actually Ollama (the OpenAI
        compatibility layer some other local server might expose won't
        have this native endpoint) -- this is a nice-to-have, not
        something the app depends on."""
        import requests

        base_url = str(self.client.base_url).rstrip("/")
        native_base = base_url[: -len("/v1")] if base_url.endswith("/v1") else base_url
        keep_alive = os.environ.get("OLLAMA_KEEP_ALIVE", "30m")
        try:
            requests.post(
                f"{native_base}/api/generate",
                json={"model": self.model, "keep_alive": keep_alive},
                timeout=180,
            )
        except Exception:
            pass


def get_provider() -> LLMProvider:
    provider = os.environ.get("BRAIN_PROVIDER", "anthropic").lower()
    if provider == "local":
        return LocalProvider()
    return AnthropicProvider()
