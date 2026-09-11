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
    only need to describe the "reached and held" shape, not the return."""
    zero: Pose = {bone: (0.0, 0.0, 0.0) for bone in pose}
    return AnimationClip(
        id=id,
        description=description,
        duration=duration,
        expression=expression,
        keyframes=[Keyframe(0.0, zero), Keyframe(peak_time, pose), Keyframe(duration, pose)],
    )


# Starting-point bone-rotation magnitudes (radians) -- these haven't been
# visually tuned against a real model yet, the same way avatar_scene's
# REST_POSE constants needed tuning after the fact. Expect to adjust per
# clip once seen running. Deliberately avoids "chest" on the x axis
# (owned by the idle-breathing sine wave) and finger bones (not
# guaranteed to be rigged on every VRM model) -- body language is
# conveyed through head/spine/chest/arm posture instead.
LIBRARY: list[AnimationClip] = [
    _clip(
        "happy_grin",
        "grins, smiles warmly, beams with delight, laughs, chuckles, smirks, "
        "a happy joyful excited reaction",
        duration=1.4,
        pose={
            "head": (-0.05, 0.0, 0.1),
            "chest": (0.0, 0.05, 0.05),
            "rightUpperArm": (0.0, 0.0, 0.8),
            "rightLowerArm": (0.0, 0.0, -0.4),
        },
        expression="happy",
    ),
    _clip(
        "proud_chest_pump",
        "stands proud, puffs up chest, hands on hips, confident and "
        "triumphant, feeling accomplished, boastful",
        duration=1.6,
        pose={
            "head": (-0.03, 0.0, 0.0),
            "chest": (0.0, 0.0, 0.08),
            "leftUpperArm": (0.0, 0.3, 0.5),
            "rightUpperArm": (0.0, -0.3, 0.5),
            "leftLowerArm": (0.0, 0.0, 0.6),
            "rightLowerArm": (0.0, 0.0, -0.6),
        },
        expression="happy",
    ),
    _clip(
        "sad_slump",
        "frowns, sighs sadly, slumps, looks downcast, disappointed, "
        "teary, dejected, heartbroken",
        duration=1.6,
        pose={
            "head": (0.15, 0.0, 0.0),
            "chest": (0.0, -0.03, -0.06),
            "spine": (0.05, 0.0, 0.0),
            "leftUpperArm": (0.1, 0.0, 0.15),
            "rightUpperArm": (0.1, 0.0, -0.15),
        },
        expression="sad",
    ),
    _clip(
        "angry_tense",
        "glares, scowls, growls, snarls, furrows brow, clenches fists, "
        "seethes with anger, frustrated and irritated",
        duration=1.2,
        pose={
            "head": (0.05, 0.0, 0.0),
            "chest": (0.0, 0.0, -0.05),
            "leftUpperArm": (0.0, 0.0, 0.3),
            "rightUpperArm": (0.0, 0.0, -0.3),
            "leftLowerArm": (0.2, 0.0, 0.0),
            "rightLowerArm": (0.2, 0.0, 0.0),
        },
        expression="angry",
        peak_time=0.15,
    ),
    _clip(
        "surprised_gasp",
        "gasps, widens eyes, startled, surprised, jolts back, flinches, "
        "taken aback, shocked",
        duration=1.0,
        pose={
            "head": (-0.1, 0.0, 0.0),
            "chest": (0.0, 0.0, -0.08),
            "leftUpperArm": (0.0, 0.0, 0.4),
            "rightUpperArm": (0.0, 0.0, -0.4),
        },
        expression="surprised",
        peak_time=0.1,
    ),
    _clip(
        "wave_greeting",
        "waves hello, greets warmly, says hi, welcomes you, waves "
        "goodbye, friendly greeting",
        duration=1.8,
        pose={
            "head": (-0.03, 0.1, 0.0),
            "rightUpperArm": (0.0, 0.0, 1.3),
            "rightLowerArm": (0.0, 0.0, -0.9),
        },
        peak_time=0.3,
    ),
    _clip(
        "thinking_ponder",
        "thinks, ponders, considers, contemplates, wonders, hums "
        "thoughtfully, deep in thought",
        duration=1.8,
        pose={
            "head": (0.0, 0.15, 0.05),
            "rightUpperArm": (0.0, 0.3, 1.0),
            "rightLowerArm": (1.4, 0.0, -0.3),
        },
        peak_time=0.4,
    ),
    _clip(
        "shrug",
        "shrugs, unsure, doesn't know, indifferent, whatever, no idea, "
        "uncertain",
        duration=1.1,
        pose={
            "head": (0.0, 0.0, 0.05),
            "chest": (0.0, 0.0, 0.04),
            "leftUpperArm": (0.0, 0.0, 0.4),
            "rightUpperArm": (0.0, 0.0, -0.4),
            "leftLowerArm": (0.3, 0.0, 0.0),
            "rightLowerArm": (0.3, 0.0, 0.0),
        },
        peak_time=0.2,
    ),
    _clip(
        "emphasis_gesture",
        "leans in, gestures for emphasis, makes a point, taps the "
        "table, emphasizes what they're saying, gestures while explaining",
        duration=1.2,
        pose={
            "head": (-0.02, 0.0, 0.0),
            "spine": (-0.05, 0.0, 0.0),
            "rightUpperArm": (0.0, 0.0, 0.5),
            "rightLowerArm": (0.5, 0.0, -0.2),
        },
        peak_time=0.25,
    ),
]
