import random

import numpy as np

from embeddings import get_embedding_provider

from .generator import ProceduralFallbackGenerator
from .imported import load_imported_clips
from .library import LIBRARY
from .types import AnimationClip

MATCH_THRESHOLD = 0.45

# How close a clip's score has to be to the best score to count as "tied"
# with it -- covers both clips given the literal same description (whose
# embeddings, and therefore scores, will be near-identical) and clips
# with different but near-equally-good descriptions for this query.
TIE_EPSILON = 1e-3


class MotionSelector:
    """Classifies *action* text against the animation library by
    semantic similarity -- reuses the same EmbeddingProvider already
    used for lore/memory search (see embeddings.py), so it follows
    whichever EMBEDDING_PROVIDER the app is already configured with.
    Falls back to a generic procedurally-generated gesture (generator.py)
    when nothing matches well enough, rather than leaving an action with
    no motion at all.

    The library itself is two sources merged together: library.py's
    hand-authored clips (empty by default -- see that file) plus
    whatever's been dropped into lib/motion/clips/ (JSON files exported
    by avatar_scene/convert_mixamo.html, retargeted from real motion
    capture) -- both are just AnimationClip instances by the time they
    reach here, so this class doesn't care which produced which. An
    empty library (nothing imported yet) just means every action falls
    through to the generator below.

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
        of the first reply. No-op if the library is empty (nothing to
        embed yet -- e.g. before any clips have been imported)."""
        self._ensure_library_vectors()

    def _ensure_library_vectors(self) -> None:
        if self._library_vectors is None and self._library:
            descriptions = [clip.description for clip in self._library]
            self._library_vectors = np.array(self._provider.embed(descriptions))

    def select(self, action_text: str) -> AnimationClip:
        """Picks the best-matching clip for `action_text`, or falls back
        to the generator if nothing clears the threshold. When several
        clips tie (or nearly tie) for best -- e.g. multiple imported
        variants sharing the same description, like three different
        recorded waves -- one is chosen at random each time rather than
        always playing the same one, so a repeated action doesn't look
        identical every time it plays."""
        if not self._library:
            return self._generator.generate(action_text)
        self._ensure_library_vectors()
        query = np.array(self._provider.embed([action_text])[0])
        scores = self._library_vectors @ query
        best_score = float(scores.max())
        if best_score < self._threshold:
            return self._generator.generate(action_text)
        candidates = [i for i, score in enumerate(scores) if score >= best_score - TIE_EPSILON]
        return self._library[random.choice(candidates)]
