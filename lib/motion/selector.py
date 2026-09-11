import numpy as np

from embeddings import get_embedding_provider

from .generator import ProceduralFallbackGenerator
from .library import LIBRARY
from .types import AnimationClip

MATCH_THRESHOLD = 0.45


class MotionSelector:
    """Classifies *action* text against a small hand-authored animation
    library (library.py) by semantic similarity -- reuses the same
    EmbeddingProvider already used for lore/memory search (see
    embeddings.py), so it follows whichever EMBEDDING_PROVIDER the app
    is already configured with. Falls back to a generic
    procedurally-generated gesture (generator.py) when nothing matches
    well enough, rather than leaving an action with no motion at all.

    This is the "classify, then fallback to generate" design: a real
    project would replace LIBRARY's hand-authored poses with retargeted
    motion-capture clips (e.g. from BEAT) and ProceduralFallbackGenerator
    with a trained co-speech model, without either swap changing this
    class or its caller (VoiceProvider.speak())."""

    def __init__(
        self,
        generator: ProceduralFallbackGenerator | None = None,
        library: list[AnimationClip] | None = None,
        threshold: float = MATCH_THRESHOLD,
    ):
        self._provider = get_embedding_provider()
        self._generator = generator or ProceduralFallbackGenerator()
        self._library = library or LIBRARY
        self._threshold = threshold
        self._library_vectors: np.ndarray | None = None

    def warm_up(self) -> None:
        """Loads the embedding model and embeds the whole library once,
        up front -- same purpose as Brain.provider.warm_up()/STT's
        warm_up(), so this cost doesn't land on the first *action* span
        of the first reply."""
        self._ensure_library_vectors()

    def _ensure_library_vectors(self) -> None:
        if self._library_vectors is None:
            descriptions = [clip.description for clip in self._library]
            self._library_vectors = np.array(self._provider.embed(descriptions))

    def select(self, action_text: str) -> AnimationClip:
        self._ensure_library_vectors()
        query = np.array(self._provider.embed([action_text])[0])
        scores = self._library_vectors @ query
        best_index = int(np.argmax(scores))
        if scores[best_index] >= self._threshold:
            return self._library[best_index]
        return self._generator.generate(action_text)
