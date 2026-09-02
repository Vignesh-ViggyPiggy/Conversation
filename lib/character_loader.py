import os
from pathlib import Path

import yaml

# characters/ lives at the repo root, one level up from lib/
CHARACTERS_DIR = Path(__file__).parent.parent / "characters"


def load(name: str | None = None) -> dict:
    name = name or os.environ.get("CHARACTER", "nova")
    path = CHARACTERS_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


# Loaded once at import time; persona.py and lore/entries.py both read from
# this same dict instead of each parsing the file themselves.
CHARACTER = load()
