import os
from abc import ABC, abstractmethod

MAX_TOKENS = 512


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, messages: list[dict]) -> str:
        ...


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = model or os.environ.get("BRAIN_MODEL", "claude-sonnet-5")

    def chat(self, system: str, messages: list[dict]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class LocalProvider(LLMProvider):
    """Any OpenAI-compatible local server: Ollama, llama.cpp server, LM Studio, vLLM."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        from openai import OpenAI

        self.client = OpenAI(
            base_url=base_url or os.environ.get("BRAIN_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.environ.get("BRAIN_API_KEY", "not-needed"),
        )
        self.model = model or os.environ.get("BRAIN_MODEL", "llama3.1")

    def chat(self, system: str, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "system", "content": system}, *messages],
        )
        return response.choices[0].message.content


def get_provider() -> LLMProvider:
    provider = os.environ.get("BRAIN_PROVIDER", "anthropic").lower()
    if provider == "local":
        return LocalProvider()
    return AnthropicProvider()
