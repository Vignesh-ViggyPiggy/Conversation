import uuid

from llm import get_provider
from lore.retriever import format_for_prompt, search
from memory.extractor import extract_facts
from memory.store import add_fact, format_facts, search_facts
from persona import BASE_PROMPT, PERSONA_NAME

IDLE_PROMPT = "[Nothing has been said in a while. Break the silence by saying something in character.]"


class Brain:
    """Persona + working memory + LLM call, plus persistent memory across sessions."""

    def __init__(self):
        self.provider = get_provider()
        self.history: list[dict] = []
        self.session_id = str(uuid.uuid4())

    def respond(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        relevant_lore = format_for_prompt(search(user_input))
        remembered = format_facts(search_facts(PERSONA_NAME, user_input))

        system_prompt = BASE_PROMPT
        if relevant_lore:
            system_prompt += f"\n\n{relevant_lore}"
        if remembered:
            system_prompt += f"\n\n{remembered}"

        reply = self.provider.chat(system_prompt, self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def idle_response(self) -> str:
        """Self-initiated response to fill silence, reusing respond() as-is
        (same persona/lore/memory pipeline) with a synthetic prompt instead
        of real user text. The prompt still lands in history, so later
        replies can coherently reference "you went quiet earlier"."""
        return self.respond(IDLE_PROMPT)

    def reset(self) -> str | None:
        """Ends the current session: one batched extraction call over its full
        transcript, saved under this session's id so it can be reviewed or
        deleted as a unit later (see memory_cli.py). Then starts a fresh
        session. Past sessions' facts are untouched. Returns the session id
        that was just finalized, or None if there was nothing to save."""
        finished_session_id = self.session_id
        had_history = bool(self.history)

        if had_history:
            for fact in extract_facts(self.provider, self.history):
                add_fact(PERSONA_NAME, finished_session_id, fact)

        self.history = []
        self.session_id = str(uuid.uuid4())
        return finished_session_id if had_history else None
