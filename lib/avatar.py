import json
import os
import time
import uuid
from pathlib import Path

import numpy as np

VTS_WS_URL = os.environ.get("VTS_WS_URL", "ws://localhost:8001")
PLUGIN_NAME = "Conversation Character Brain"
PLUGIN_DEVELOPER = "local"
TOKEN_PATH = Path(os.environ.get("VTS_TOKEN_PATH", Path(__file__).parent.parent / ".vts_token"))


class VTubeStudioClient:
    """Minimal VTube Studio API client: auth handshake + parameter
    injection, enough to drive mouth-open from audio amplitude. See
    https://github.com/DenchiSoft/VTubeStudio for the full API."""

    def __init__(self):
        import websocket

        self.ws = websocket.create_connection(VTS_WS_URL, timeout=5)
        self._authenticate()

    def _send(self, message_type: str, data: dict | None = None) -> dict:
        request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(uuid.uuid4()),
            "messageType": message_type,
            "data": data or {},
        }
        self.ws.send(json.dumps(request))
        return json.loads(self.ws.recv())

    def _authenticate(self) -> None:
        token = TOKEN_PATH.read_text().strip() if TOKEN_PATH.exists() else None

        if not token:
            response = self._send(
                "AuthenticationTokenRequest",
                {"pluginName": PLUGIN_NAME, "pluginDeveloper": PLUGIN_DEVELOPER},
            )
            token = response["data"]["authenticationToken"]
            TOKEN_PATH.write_text(token)
            print("VTube Studio: approve the plugin popup in the app if prompted.")

        response = self._send(
            "AuthenticationRequest",
            {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER,
                "authenticationToken": token,
            },
        )
        if not response["data"].get("authenticated"):
            raise RuntimeError(
                f"VTube Studio authentication failed: {response['data'].get('reason')}"
            )

    def set_mouth_open(self, value: float) -> None:
        value = max(0.0, min(1.0, value))
        self._send(
            "InjectParameterDataRequest",
            {
                "faceFound": False,
                "mode": "set",
                "parameterValues": [{"id": "MouthOpen", "value": value}],
            },
        )

    def close(self) -> None:
        self.ws.close()


def amplitude_windows(audio: np.ndarray, sample_rate: int, window_ms: float = 50.0) -> list[float]:
    """Splits audio into window_ms chunks and returns a 0-1 mouth-open value
    per chunk, based on RMS amplitude normalized against this clip's own
    loudest window."""
    window_size = max(1, int(sample_rate * window_ms / 1000))
    num_windows = max(1, len(audio) // window_size)

    levels = []
    for i in range(num_windows):
        chunk = audio[i * window_size : (i + 1) * window_size]
        if len(chunk) == 0:
            continue
        rms = float(np.sqrt(np.mean(chunk.astype("float64") ** 2)))
        levels.append(rms)

    if not levels:
        return []

    peak = max(levels) or 1.0
    return [min(1.0, level / peak) for level in levels]


def animate_mouth_from_audio(
    client: VTubeStudioClient, audio: np.ndarray, sample_rate: int, window_ms: float = 50.0
) -> None:
    """Streams mouth-open values timed to match audio playback. Meant to
    run in a background thread alongside actual audio playback so the two
    happen concurrently."""
    levels = amplitude_windows(audio, sample_rate, window_ms)
    interval = window_ms / 1000.0
    for level in levels:
        client.set_mouth_open(level)
        time.sleep(interval)
    client.set_mouth_open(0.0)
