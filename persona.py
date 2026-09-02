from character_loader import CHARACTER

PERSONA_NAME = CHARACTER["name"]
VOICE = CHARACTER["voice"]
CORE_LORE = CHARACTER["core_lore"]
EXAMPLES: list[tuple[str, str]] = [
    (ex["user"], ex["character"]) for ex in CHARACTER.get("examples", [])
]


def _format_examples() -> str:
    if not EXAMPLES:
        return ""
    # No added quoting: example lines may already contain quoted dialogue
    # of their own (e.g. a character sarcastically quoting a word back),
    # and wrapping those in another layer of quotes reads as broken.
    lines = "\n".join(f"User: {u}\n{PERSONA_NAME}: {c}" for u, c in EXAMPLES)
    return f"\nExample exchanges — match this voice exactly:\n{lines}\n"


BASE_PROMPT = f"{VOICE}\n{CORE_LORE}{_format_examples()}\nStay in character at all times."
