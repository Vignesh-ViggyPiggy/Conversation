import asyncio
import json
import os
import threading
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class AvatarProvider(ABC):
    @abstractmethod
    def set_mouth_open(self, value: float) -> None:
        ...

    def set_expression(self, name: str, value: float) -> None:
        """Sets one of VRM's standard expression presets: "happy",
        "angry", "sad", "relaxed", "surprised", or "neutral" to clear.
        No-op by default -- only meaningful for providers that can
        actually drive expressions."""

    def close(self) -> None:
        pass


# Keyword -> VRM expression preset. Deliberately limited to the presets
# VRM avatars actually support out of the box -- this maps facial/vocal
# cues in *action* text to an expression, not arbitrary physical poses
# ("leans in", "crosses arms") which would need real animation clips
# this project doesn't have.
_EXPRESSION_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("happy", ("grin", "smil", "laugh", "chuckl", "smirk", "delight", "gleam", "wink")),
    ("angry", ("glare", "scowl", "growl", "snarl", "furrow", "clench", "seethe")),
    ("sad", ("frown", "sigh", "tear", "sniff", "droop", "slump", "wince")),
    ("surprised", ("gasp", "widen", "startl", "jolt", "flinch", "blink in surprise")),
    ("relaxed", ("relax", "settle", "ease back", "lean back")),
]


def expression_for_action(action_text: str) -> str | None:
    """Best-effort keyword match from an *action* span's text to a VRM
    expression preset name, or None if nothing recognized -- most
    action text (e.g. "leans in", "taps the table") won't map to any
    facial expression, which is expected and fine."""
    lowered = action_text.lower()
    for expression, keywords in _EXPRESSION_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return expression
    return None


VTS_WS_URL = os.environ.get("VTS_WS_URL", "ws://localhost:8001")
PLUGIN_NAME = "Conversation Character Brain"
PLUGIN_DEVELOPER = "local"
TOKEN_PATH = Path(os.environ.get("VTS_TOKEN_PATH", Path(__file__).parent.parent / ".vts_token"))


class VTubeStudioProvider(AvatarProvider):
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

    def set_expression(self, name: str, value: float) -> None:
        """Best-effort: VTube Studio activates expressions by hotkey, not
        by a generic name -- this only works if the loaded model has a
        hotkey literally named to match (e.g. "happy"), which is entirely
        up to how the user set up their model. Silently does nothing if
        no matching hotkey exists, rather than failing the whole app over
        an optional cosmetic feature."""
        try:
            hotkeys = self._send("HotkeyListRequest")["data"]["availableHotkeys"]
            match = next((h for h in hotkeys if h["name"].lower() == name.lower()), None)
            if match and value > 0:
                self._send("HotkeyTriggerRequest", {"hotkeyID": match["hotkeyID"]})
        except Exception:
            pass

    def close(self) -> None:
        self.ws.close()


class LocalSceneProvider(AvatarProvider):
    """Runs a local WebSocket server that avatar_scene/index.html connects
    to, broadcasting mouth-open values to every connected browser client.
    This is the counterpart to VTubeStudioProvider for the custom
    Three.js/three-vrm scene -- no external app, no auth handshake, we own
    both ends. Runs its own asyncio loop in a background thread so the
    rest of this synchronous codebase doesn't need to become async."""

    def __init__(self, host: str | None = None, port: int | None = None):
        import websockets

        self.host = host or os.environ.get("AVATAR_SCENE_HOST", "localhost")
        self.port = port or int(os.environ.get("AVATAR_SCENE_PORT", "9001"))
        self._clients: set = set()
        self._loop = asyncio.new_event_loop()
        self._server = None
        ready = threading.Event()

        self._thread = threading.Thread(
            target=self._run_loop, args=(websockets, ready), daemon=True
        )
        self._thread.start()
        if not ready.wait(timeout=5):
            raise RuntimeError(f"Avatar scene server failed to start on {self.host}:{self.port}")
        print(f"Avatar scene server listening on ws://{self.host}:{self.port}")

    def _run_loop(self, websockets, ready: threading.Event) -> None:
        asyncio.set_event_loop(self._loop)

        async def handler(websocket):
            self._clients.add(websocket)
            try:
                async for _ in websocket:
                    pass  # this server only broadcasts, it doesn't need to read
            finally:
                self._clients.discard(websocket)

        async def start():
            self._server = await websockets.serve(handler, self.host, self.port)
            ready.set()

        self._loop.run_until_complete(start())
        self._loop.run_forever()

    async def _broadcast(self, message: str) -> None:
        if not self._clients:
            return
        await asyncio.gather(
            *(client.send(message) for client in list(self._clients)),
            return_exceptions=True,
        )

    def set_mouth_open(self, value: float) -> None:
        value = max(0.0, min(1.0, value))
        message = json.dumps({"type": "mouth", "value": value})
        asyncio.run_coroutine_threadsafe(self._broadcast(message), self._loop)

    def set_expression(self, name: str, value: float) -> None:
        message = json.dumps({"type": "expression", "name": name, "value": value})
        asyncio.run_coroutine_threadsafe(self._broadcast(message), self._loop)

    def close(self) -> None:
        """Closes the server's listening socket and waits for it to finish
        before stopping the loop -- stopping the loop first (the previous
        behavior) tore down the pending connection-accept task mid-flight,
        producing a "Task was destroyed but it is pending!" warning."""

        async def shutdown():
            if self._server is not None:
                self._server.close()
                await self._server.wait_closed()

        future = asyncio.run_coroutine_threadsafe(shutdown(), self._loop)
        try:
            future.result(timeout=2)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)


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
    provider: AvatarProvider, audio: np.ndarray, sample_rate: int, window_ms: float = 50.0
) -> None:
    """Streams mouth-open values timed to match audio playback. Meant to
    run in a background thread alongside actual audio playback so the two
    happen concurrently."""
    levels = amplitude_windows(audio, sample_rate, window_ms)
    interval = window_ms / 1000.0
    for level in levels:
        provider.set_mouth_open(level)
        time.sleep(interval)
    provider.set_mouth_open(0.0)
