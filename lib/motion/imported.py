import json
from pathlib import Path

from .types import AnimationClip

# Where avatar_scene/convert_mixamo.html's exported clips land -- each is a
# JSON file shaped like {"id", "description", "duration", "expression",
# "native_clip"}. Loaded fresh every call rather than cached, since these
# are meant to be dropped in/edited/removed during library curation, not
# fixed at process start like library.py's hand-authored LIBRARY.
CLIPS_DIR = Path(__file__).parent / "clips"


def load_imported_clips() -> list[AnimationClip]:
    if not CLIPS_DIR.is_dir():
        return []

    clips = []
    for path in sorted(CLIPS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        clips.append(
            AnimationClip(
                id=data["id"],
                description=data["description"],
                duration=data["duration"],
                expression=data.get("expression"),
                native_clip=data["native_clip"],
            )
        )
    return clips
