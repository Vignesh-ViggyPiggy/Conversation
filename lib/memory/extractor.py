from llm import LLMProvider

EXTRACTION_SYSTEM_PROMPT = """You extract durable facts worth remembering long-term from a
conversation — things like the user's name, preferences, ongoing situations, or
running jokes. Ignore small talk and anything already obvious or temporary. Reply
with one fact per line, written as a short standalone statement. If nothing is
worth remembering, reply with exactly: NONE"""


def extract_facts(provider: LLMProvider, history: list[dict]) -> list[str]:
    """One batched extraction call over a whole session's transcript, rather than
    one call per exchange."""
    transcript = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)
    result = provider.chat(EXTRACTION_SYSTEM_PROMPT, [{"role": "user", "content": transcript}])
    lines = [line.strip("- ").strip() for line in result.splitlines()]
    return [line for line in lines if line and line.upper() != "NONE"]
