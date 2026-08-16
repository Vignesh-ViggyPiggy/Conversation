import os

from anthropic import Anthropic

from persona import PERSONA_PROMPT

DEFAULT_MODEL = "claude-sonnet-5"
MAX_TOKENS = 512


class Brain:
    """Persona + working memory + LLM call. No persistence, no I/O beyond text in/out."""

    def __init__(self, model: str | None = None):
        self.client = Anthropic()
        self.model = model or os.environ.get("BRAIN_MODEL", DEFAULT_MODEL)
        self.history: list[dict] = []

    def respond(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=PERSONA_PROMPT,
            messages=self.history,
        )

        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        self.history = []
