from lore.entries import LORE_ENTRIES


def search(query: str, k: int = 3) -> list[dict]:
    """Return up to k lore entries whose tags match the query, best match first."""
    query_lower = query.lower()
    scored = []
    for entry in LORE_ENTRIES:
        score = sum(1 for tag in entry["tags"] if tag in query_lower)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[:k]]


def format_for_prompt(entries: list[dict]) -> str:
    if not entries:
        return ""
    lines = "\n".join(f"- {entry['text']}" for entry in entries)
    return f"Relevant background:\n{lines}"
