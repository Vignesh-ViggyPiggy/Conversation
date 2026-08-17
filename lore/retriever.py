import numpy as np

from embeddings import get_embedding_provider
from lore.entries import LORE_ENTRIES

MIN_SCORE = 0.3

_provider = None
_entry_vectors = None


def _provider_singleton():
    global _provider
    if _provider is None:
        _provider = get_embedding_provider()
    return _provider


def _entry_vectors_cached():
    global _entry_vectors
    if _entry_vectors is None and LORE_ENTRIES:
        texts = [entry["text"] for entry in LORE_ENTRIES]
        _entry_vectors = np.array(_provider_singleton().embed(texts))
    return _entry_vectors


def search(query: str, k: int = 3) -> list[dict]:
    """Up to k lore entries semantically similar to query, best match first.
    Entry embeddings are computed once and cached for the process's
    lifetime — lore is static after load, so only the query gets embedded
    on each call."""
    if not LORE_ENTRIES:
        return []

    vectors = _entry_vectors_cached()
    query_vec = np.array(_provider_singleton().embed([query])[0])
    scores = vectors @ query_vec

    ranked = sorted(range(len(LORE_ENTRIES)), key=lambda i: scores[i], reverse=True)
    return [LORE_ENTRIES[i] for i in ranked if scores[i] >= MIN_SCORE][:k]


def format_for_prompt(entries: list[dict]) -> str:
    if not entries:
        return ""
    lines = "\n".join(f"- {entry['text']}" for entry in entries)
    return f"Relevant background:\n{lines}"
