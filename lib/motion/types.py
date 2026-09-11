from dataclasses import dataclass

Pose = dict[str, tuple[float, float, float]]


@dataclass(frozen=True)
class Keyframe:
    t: float
    pose: Pose


@dataclass(frozen=True)
class AnimationClip:
    """A short, hand-authored (or generated) body pose sequence plus an
    optional facial expression, applied together as one unit -- see the
    design discussion this came out of: an "expression" isn't just a
    face blendshape, it's the whole body language (a grin might come
    with a small fist-pump; pride with hands on hips), so a single clip
    carries both rather than triggering two independent systems.

    Bone rotations are deltas (radians, xyz Euler) added on top of
    whatever the avatar's current rest/idle pose already is -- see
    avatar_scene/index.html's boneBaseline handling -- not absolute
    poses, so a clip composes with the standing rest pose and idle
    breathing instead of overriding them."""

    id: str
    description: str
    duration: float
    keyframes: list[Keyframe]
    expression: str | None = None

    def to_message(self) -> dict:
        return {
            "type": "motion",
            "duration": self.duration,
            "expression": self.expression,
            "keyframes": [{"t": kf.t, "pose": kf.pose} for kf in self.keyframes],
        }
