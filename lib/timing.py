import os
import time

ENABLED = os.environ.get("DEBUG_TIMING", "").lower() in ("1", "true", "yes")


def log(label: str, start: float) -> None:
    """Prints elapsed time since `start` if DEBUG_TIMING is set. Cheap
    diagnostic for finding out which stage (lore/memory search, LLM
    call, TTS) actually accounts for a slow turn, instead of guessing."""
    if ENABLED:
        print(f"[timing] {label}: {time.perf_counter() - start:.2f}s")
