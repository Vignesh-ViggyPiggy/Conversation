from llm import get_provider
from lore.retriever import format_for_prompt, search
from persona import BASE_PROMPT


class Brain:
    """Persona + working memory + LLM call. No persistence, no I/O beyond text in/out."""

    def __init__(self):
        self.provider = get_provider()
        self.history: list[dict] = []

    def respond(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        relevant_lore = format_for_prompt(search(user_input))
        system_prompt = f"{BASE_PROMPT}\n\n{relevant_lore}" if relevant_lore else BASE_PROMPT

        reply = self.provider.chat(system_prompt, self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        self.history = []
