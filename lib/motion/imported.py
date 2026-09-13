import json
from pathlib import Path

from .types import AnimationClip, Keyframe

# Where the avatar_scene/convert_*.html tools export clips -- each is a
# JSON file shaped like {"id", "description", "duration", "expression",
# and exactly one of "native_clip" (file-based converters: Mixamo, and
# formerly others) or "keyframes" (avatar_scene/webcam_mocap.html's
# recorded clips). Loaded fresh every call rather than cached, since
# these are meant to be dropped in/edited/removed during library
# curation, not fixed at process start like library.py's hand-authored
# LIBRARY.
CLIPS_DIR = Path(__file__).parent / "clips"


def load_imported_clips() -> list[AnimationClip]:
    if not CLIPS_DIR.is_dir():
        return []

    clips = []
    for path in sorted(CLIPS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        keyframes = None
        if "keyframes" in data:
            keyframes = [Keyframe(t=kf["t"], pose={k: tuple(v) for k, v in kf["pose"].items()}) for kf in data["keyframes"]]
        clips.append(
            AnimationClip(
                id=data["id"],
                description=data["description"],
                duration=data["duration"],
                expression=data.get("expression"),
                keyframes=keyframes,
                native_clip=data.get("native_clip"),
            )
        )
    return clips
