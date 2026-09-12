from dataclasses import dataclass

Pose = dict[str, tuple[float, float, float]]


@dataclass(frozen=True)
class Keyframe:
    t: float
    pose: Pose


@dataclass(frozen=True)
class AnimationClip:
    """A short body pose sequence plus an optional facial expression,
    applied together as one unit -- see the design discussion this came
    out of: an "expression" isn't just a face blendshape, it's the whole
    body language (a grin might come with a small fist-pump; pride with
    hands on hips), so a single clip carries both rather than triggering
    two independent systems.

    Exactly one of `keyframes` or `native_clip` is set, never both:

    - `keyframes` (hand-authored in library.py, or the procedural
      fallback generator): bone rotations are deltas (radians, xyz
      Euler) added on top of whatever the avatar's current rest/idle
      pose already is -- see avatar_scene/index.html's boneBaseline
      handling -- not absolute poses, so a clip composes with the
      standing rest pose and idle breathing instead of overriding them.
      Played by a small custom interpolator (poseAtTime/applyMotionFrame
      in avatar_scene/index.html).

    - `native_clip` (imported from motion capture, e.g. a Mixamo
      animation retargeted onto this VRM's normalized bones -- see
      avatar_scene/convert_mixamo.html): a serialized THREE.AnimationClip
      (via THREE.AnimationClip.toJSON()), containing absolute
      quaternion/position tracks already retargeted to this specific
      VRM's normalized bone names. Played by three.js's own
      AnimationMixer, since re-deriving accurate Euler deltas from
      arbitrary large-rotation mocap quaternions isn't reliable (Euler
      composition breaks down / gimbal-locks outside small angles) --
      three.js's own quaternion interpolation handles this correctly
      already, so there's no reason to reinvent it."""

    id: str
    description: str
    duration: float
    keyframes: list[Keyframe] | None = None
    native_clip: dict | None = None
    expression: str | None = None

    def to_message(self) -> dict:
        message = {"type": "motion", "duration": self.duration, "expression": self.expression}
        if self.native_clip is not None:
            message["native_clip"] = self.native_clip
        else:
            message["keyframes"] = [{"t": kf.t, "pose": kf.pose} for kf in self.keyframes]
        return message
