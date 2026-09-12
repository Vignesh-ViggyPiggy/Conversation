import numpy as np

from embeddings import get_embedding_provider

from .generator import ProceduralFallbackGenerator
from .imported import load_imported_clips
from .library import LIBRARY
from .types import AnimationClip

MATCH_THRESHOLD = 0.45


class MotionSelector:
    """Classifies *action* text against the animation library by
    semantic similarity -- reuses the same EmbeddingProvider already
    used for lore/memory search (see embeddings.py), so it follows
    whichever EMBEDDING_PROVIDER the app is already configured with.
    Falls back to a generic procedurally-generated gesture (generator.py)
    when nothing matches well enough, rather than leaving an action with
    no motion at all.

    The library itself is two sources merged together: library.py's
    hand-authored starter clips, plus whatever's been dropped into
    lib/motion/clips/ (JSON files exported by
    avatar_scene/convert_mixamo.html, retargeted from real motion
    capture) -- both are just AnimationClip instances by the time they
    reach here, so this class doesn't care which produced which.

    This is the "classify, then fallback to generate" design:
    ProceduralFallbackGenerator is a placeholder for a real trained
    co-speech model, swappable without changing this class or its
    caller (VoiceProvider.speak())."""

    def __init__(
        self,
        generator: ProceduralFallbackGenerator | None = None,
        library: list[AnimationClip] | None = None,
        threshold: float = MATCH_THRESHOLD,
    ):
        self._provider = get_embedding_provider()
        self._generator = generator or ProceduralFallbackGenerator()
        self._library = library if library is not None else LIBRARY + load_imported_clips()
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
