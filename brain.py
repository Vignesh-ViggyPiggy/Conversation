from llm import get_provider
from lore.retriever import format_for_prompt, search
from memory.extractor import extract_facts
from memory.store import add_fact, format_facts, get_facts
from persona import BASE_PROMPT, PERSONA_NAME


class Brain:
    """Persona + working memory + LLM call, plus persistent memory across sessions."""

    def __init__(self):
        self.provider = get_provider()
        self.history: list[dict] = []

    def respond(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        relevant_lore = format_for_prompt(search(user_input))
        remembered = format_facts(get_facts(PERSONA_NAME))

        system_prompt = BASE_PROMPT
        if relevant_lore:
            system_prompt += f"\n\n{relevant_lore}"
        if remembered:
            system_prompt += f"\n\n{remembered}"

        reply = self.provider.chat(system_prompt, self.history)
        self.history.append({"role": "assistant", "content": reply})

        for fact in extract_facts(self.provider, user_input, reply):
            add_fact(PERSONA_NAME, fact)

        return reply

    def reset(self) -> None:
        """Clears working memory (this session's conversation) only — persistent
        facts survive, by design, since forgetting them on every restart would
        defeat the point of persistent memory."""
        self.history = []
