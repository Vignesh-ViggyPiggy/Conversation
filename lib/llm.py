import os
from abc import ABC, abstractmethod

MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 1.0


def _get_temperature() -> float:
    return float(os.environ.get("BRAIN_TEMPERATURE", DEFAULT_TEMPERATURE))


def _clean_text(text: str) -> str:
    """Some local models emit mojibake baked into their own output (UTF-8
    bytes decoded through the wrong codepage somewhere upstream of this
    app -- often in how the training data itself was encoded), e.g. an
    em dash showing up as "â€”". ftfy detects and repairs this class of
    corruption; harmless no-op on text that's already clean."""
    import ftfy

    return ftfy.fix_text(text)


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, messages: list[dict]) -> str:
        ...


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
        return _clean_text(response.content[0].text)


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
        return _clean_text(response.choices[0].message.content)


def get_provider() -> LLMProvider:
    provider = os.environ.get("BRAIN_PROVIDER", "anthropic").lower()
    if provider == "local":
        return LocalProvider()
    return AnthropicProvider()
