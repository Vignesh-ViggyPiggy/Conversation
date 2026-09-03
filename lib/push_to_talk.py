import os

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000


def record_push_to_talk(key: str | None = None) -> np.ndarray:
    """Blocks until `key` is pressed, records audio while it's held, and
    returns the captured audio once released. Empty array if nothing was
    captured (e.g. released instantly)."""
    import keyboard

    key = key or os.environ.get("PUSH_TO_TALK_KEY", "space")
    print(f"(hold [{key}] to talk)")
    keyboard.wait(key)

    frames: list[np.ndarray] = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback):
        while keyboard.is_pressed(key):
            sd.sleep(50)

    if not frames:
        return np.zeros((0,), dtype="float32")
    return np.concatenate(frames, axis=0).flatten()
