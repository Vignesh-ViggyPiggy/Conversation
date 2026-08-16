from llm import get_provider
from persona import PERSONA_PROMPT


class Brain:
    """Persona + working memory + LLM call. No persistence, no I/O beyond text in/out."""

    def __init__(self):
        self.provider = get_provider()
        self.history: list[dict] = []

    def respond(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        reply = self.provider.chat(PERSONA_PROMPT, self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        self.history = []
