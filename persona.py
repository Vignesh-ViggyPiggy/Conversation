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
    lines = "\n".join(f'User: "{u}"\n{PERSONA_NAME}: "{c}"' for u, c in EXAMPLES)
    return f"\nExample exchanges — match this voice exactly:\n{lines}\n"


BASE_PROMPT = f"{VOICE}\n{CORE_LORE}{_format_examples()}\nStay in character at all times."
