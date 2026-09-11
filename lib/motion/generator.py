import hashlib

from .types import AnimationClip, Keyframe, Pose

# Small set of generic, mood-neutral gestures used when an action doesn't
# match anything in library.py well enough. Deliberately generic-looking
# rather than an attempt at the actual described action -- there's no
# trained text/motion model behind this (see MotionSelector's docstring).
_FALLBACK_POSES: list[Pose] = [
    {"head": (0.06, 0.08, 0.0), "rightUpperArm": (0.0, 0.0, 0.3)},
    {"head": (-0.05, -0.06, 0.0), "chest": (0.0, 0.0, 0.03)},
    {
        "head": (0.0, 0.1, 0.04),
        "leftUpperArm": (0.0, 0.0, 0.25),
        "rightUpperArm": (0.0, 0.0, -0.25),
    },
]


class ProceduralFallbackGenerator:
    """Placeholder for the "generate" half of the classify-then-fallback
    pipeline: used whenever MotionSelector can't find a library clip
    that matches an action's text well enough. Deterministically derives
    a small generic gesture from the text (same text always picks the
    same template) so unmatched actions still get some movement instead
    of none -- this is not a real text-to-motion model, just enough to
    avoid leaving a gap. Swap this out for a real one later (e.g. a
    trained co-speech gesture model -- see the design discussion this
    came from) by implementing the same generate() signature; nothing
    else in the pipeline needs to change."""

    def generate(self, action_text: str) -> AnimationClip:
        index = int(hashlib.sha1(action_text.encode()).hexdigest(), 16) % len(_FALLBACK_POSES)
        pose = _FALLBACK_POSES[index]
        zero: Pose = {bone: (0.0, 0.0, 0.0) for bone in pose}
        return AnimationClip(
            id="generated_fallback",
            description=action_text,
            duration=1.0,
            expression=None,
            keyframes=[Keyframe(0.0, zero), Keyframe(0.25, pose), Keyframe(1.0, pose)],
        )
