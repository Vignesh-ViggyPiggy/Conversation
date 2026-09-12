from .types import AnimationClip, Keyframe, Pose


def _clip(
    id: str,
    description: str,
    duration: float,
    pose: Pose,
    expression: str | None = None,
    peak_time: float = 0.3,
) -> AnimationClip:
    """Builds a simple 3-keyframe clip: neutral (all-zero deltas) at
    t=0, `pose` reached by `peak_time`, then held at `pose` until
    `duration` -- the playback engine (avatar_scene/index.html) eases
    back to the idle rest pose on its own after `duration`, so clips
    only need to describe the "reached and held" shape, not the return.

    Kept around for hand-authoring simple procedural poses later if
    needed; the starter set built this way has been retired in favor of
    real motion-capture clips retargeted via convert_mixamo.html -- see
    LIBRARY below and lib/motion/imported.py."""
    zero: Pose = {bone: (0.0, 0.0, 0.0) for bone in pose}
    return AnimationClip(
        id=id,
        description=description,
        duration=duration,
        expression=expression,
        keyframes=[Keyframe(0.0, zero), Keyframe(peak_time, pose), Keyframe(duration, pose)],
    )


# Empty by design: the hand-authored starter set (happy_grin, shrug, etc.)
# has been removed in favor of real motion-capture clips -- download from
# Mixamo (or another source) into animation_raw/<source>/, retarget with
# avatar_scene/convert_mixamo.html, and the exported JSON in
# lib/motion/clips/ becomes part of the library automatically (see
# lib/motion/imported.py and MotionSelector). Add clips here with _clip()
# only for hand-authored procedural poses you want to maintain as code
# rather than as imported JSON.
LIBRARY: list[AnimationClip] = []
