import os
import re
import threading
from abc import ABC, abstractmethod

_NARRATION_PATTERN = re.compile(r"\*[^*]*\*")


def strip_narration(text: str) -> str:
    """Removes *action/narration* segments so TTS only speaks actual
    dialogue. The full text (narration included) still gets printed and
    kept in conversation history -- this only filters what's spoken."""
    cleaned = _NARRATION_PATTERN.sub("", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def _play_with_avatar_sync(samples, sample_rate: int, avatar) -> None:
    """Plays `samples` (float32, mono, in [-1, 1]) via sounddevice, and,
    if `avatar` is given, runs amplitude-based lip-sync in a background
    thread timed to match. Shared by every provider via VoiceProvider.speak()."""
    import sounddevice as sd

    lipsync_thread = None
    if avatar is not None:
        from avatar import animate_mouth_from_audio

        lipsync_thread = threading.Thread(
            target=animate_mouth_from_audio,
            args=(avatar, samples, sample_rate),
            daemon=True,
        )
        lipsync_thread.start()

    sd.play(samples, samplerate=sample_rate)
    sd.wait()
    if lipsync_thread is not None:
        lipsync_thread.join(timeout=1)


class VoiceProvider(ABC):
    @abstractmethod
    def _synthesize(self, text: str):
        """Returns (samples, sample_rate) -- float32 mono samples in
        [-1, 1] -- without playing them. Subclasses implement this;
        speak() below handles playback uniformly so wrapper providers
        (like RVCVoiceProvider) can intercept the samples in between."""
        ...

    def speak(self, text: str, avatar=None) -> None:
        """Synthesize and play text as audio. If `avatar` (an
        AvatarProvider) is given, mouth movement is streamed in sync
        with playback."""
        samples, sample_rate = self._synthesize(text)
        _play_with_avatar_sync(samples, sample_rate, avatar)


class LocalVoiceProvider(VoiceProvider):
    """Offline TTS via pyttsx3 (system voices: SAPI5 on Windows,
    NSSpeechSynthesizer on macOS, espeak on Linux). Zero setup, no API key,
    robotic quality, no usage limits.

    Renders to a temp WAV file (pyttsx3's save_to_file) instead of
    speaking directly through the engine -- speaking directly gives no
    access to the waveform at all, but rendering to a file first means the
    same raw samples can be played via sounddevice and, when an avatar is
    passed, analyzed for lip-sync -- same as the other providers, just
    fully local and free instead of needing an API key or usage quota.

    A fresh engine is created per call rather than reused -- pyttsx3's
    runAndWait() is documented to work reliably only once per engine
    instance; reusing one across calls can silently produce no audio, or
    hang outright, on the second and later calls."""

    def _synthesize(self, text: str):
        import tempfile
        import wave

        import numpy as np
        import pyttsx3

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            engine = pyttsx3.init()
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            engine.stop()

            with wave.open(tmp_path, "rb") as wf:
                sample_rate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
        finally:
            os.remove(tmp_path)

        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return samples, sample_rate


def _iter_stream_frames(response):
    """Parses tts_service's streaming wire format from a `requests`
    response opened with stream=True: a 4-byte little-endian sample_rate,
    then repeated (4-byte little-endian length, PCM16 payload) frames.
    Yields the sample_rate once as an int, then each frame's decoded
    float32 samples -- kept separate from playback so the parsing logic
    is testable without real audio hardware."""
    import struct

    import numpy as np

    byte_iter = response.iter_content(chunk_size=None)
    buf = bytearray()

    def read_exact(n):
        while len(buf) < n:
            chunk = next(byte_iter, None)
            if chunk is None:
                raise EOFError("stream ended before expected data arrived")
            buf.extend(chunk)
        result = bytes(buf[:n])
        del buf[:n]
        return result

    yield struct.unpack("<I", read_exact(4))[0]

    while True:
        try:
            length = struct.unpack("<I", read_exact(4))[0]
        except EOFError:
            return
        payload = read_exact(length)
        yield np.frombuffer(payload, dtype=np.int16).astype(np.float32) / 32768.0


class KokoroVoiceProvider(VoiceProvider):
    """Offline neural TTS via Kokoro-82M -- free (Apache 2.0), no usage
    limits, noticeably more natural than pyttsx3's OS voices. Runs as a
    separate local HTTP server (see tts_service/) in its own Python
    3.10/3.11 venv, since kokoro pins numpy exactly and has no prebuilt
    wheel for this project's Python 3.13 -- same "external local
    service" treatment already used for Ollama.

    speak() streams the reply sentence-by-sentence and starts playback
    on the first one rather than waiting for the entire reply to finish
    synthesizing -- without this, a multi-sentence reply's *whole* audio
    has to be generated before any of it is audible, which is what made
    TTS start noticeably after the text already appeared."""

    def __init__(
        self,
        voice: str | None = None,
        lang_code: str | None = None,
        server_url: str | None = None,
    ):
        self.voice = voice or os.environ.get("KOKORO_VOICE", "af_heart")
        self.lang_code = lang_code or os.environ.get("KOKORO_LANG", "a")
        self.server_url = (
            server_url or os.environ.get("KOKORO_SERVER_URL", "http://localhost:8500")
        ).rstrip("/")

    def speak(self, text: str, avatar=None) -> None:
        import requests
        import sounddevice as sd

        response = requests.post(
            f"{self.server_url}/synthesize_stream",
            json={"text": text, "voice": self.voice, "lang_code": self.lang_code},
            stream=True,
            timeout=60,
        )
        response.raise_for_status()

        frames = _iter_stream_frames(response)
        sample_rate = next(frames)

        out_stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype="float32")
        out_stream.start()
        try:
            for samples in frames:
                if samples.size == 0:
                    continue
                lipsync_thread = None
                if avatar is not None:
                    from avatar import animate_mouth_from_audio

                    lipsync_thread = threading.Thread(
                        target=animate_mouth_from_audio,
                        args=(avatar, samples, sample_rate),
                        daemon=True,
                    )
                    lipsync_thread.start()
                out_stream.write(samples.reshape(-1, 1))
                if lipsync_thread is not None:
                    lipsync_thread.join(timeout=1)
        finally:
            out_stream.stop()
            out_stream.close()

    def _synthesize(self, text: str):
        # Non-streaming fallback -- used when RVCVoiceProvider wraps this
        # provider, since RVC's file-based conversion needs a complete
        # buffer up front anyway, so streaming would gain nothing there.
        import io
        import wave

        import numpy as np
        import requests

        response = requests.post(
            f"{self.server_url}/synthesize",
            json={"text": text, "voice": self.voice, "lang_code": self.lang_code},
            timeout=60,
        )
        response.raise_for_status()

        with wave.open(io.BytesIO(response.content), "rb") as wf:
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return samples, sample_rate


class ElevenLabsProvider(VoiceProvider):
    """Hosted TTS via ElevenLabs. Needs an API key and a chosen or cloned
    voice_id. Requests raw PCM (rather than mp3) so the samples can be
    played via sounddevice and, when an avatar is passed, analyzed for
    amplitude-based lip-sync at the same time."""

    SAMPLE_RATE = 24000

    def __init__(self, voice_id: str | None = None):
        from elevenlabs.client import ElevenLabs

        self.client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
        self.voice_id = voice_id or os.environ.get("VOICE_ID")

    def _synthesize(self, text: str):
        import numpy as np

        audio_chunks = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            output_format=f"pcm_{self.SAMPLE_RATE}",
        )
        audio_bytes = b"".join(audio_chunks)
        samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return samples, self.SAMPLE_RATE


class RVCVoiceProvider(VoiceProvider):
    """Wraps a base VoiceProvider's output through a trained RVC voice
    pack (a small, reusable model file) before playback. A fast base TTS
    (Kokoro is the intended pairing) generates speech; RVC reshapes the
    timbre to match a specific trained voice. Lightweight at inference
    time since the character-specific work happened once, during
    training (e.g. via Applio) -- unlike full clone-per-call approaches.

    Needs RVC_MODEL_PATH pointing at a trained .pth voice pack. Defaults
    to CPU for the same reason as STT_DEVICE/XTTS_DEVICE elsewhere: a
    present GPU doesn't guarantee a correctly configured CUDA setup."""

    def __init__(
        self,
        base_provider: VoiceProvider,
        model_path: str | None = None,
        device: str | None = None,
    ):
        from rvc_python.infer import RVCInference

        self.base_provider = base_provider
        model_path = model_path or os.environ.get("RVC_MODEL_PATH")
        if not model_path:
            raise RuntimeError(
                "RVC_MODEL_PATH must point at a trained RVC voice pack (.pth file)"
            )

        self.rvc = RVCInference(device=device or os.environ.get("RVC_DEVICE", "cpu"))
        self.rvc.load_model(model_path)

    def _synthesize(self, text: str):
        import tempfile
        import wave

        import numpy as np

        base_samples, base_sample_rate = self.base_provider._synthesize(text)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as in_tmp:
            in_path = in_tmp.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_tmp:
            out_path = out_tmp.name

        try:
            pcm16 = (np.clip(base_samples, -1.0, 1.0) * 32767).astype(np.int16)
            with wave.open(in_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(base_sample_rate)
                wf.writeframes(pcm16.tobytes())

            self.rvc.infer_file(input_path=in_path, output_path=out_path)

            with wave.open(out_path, "rb") as wf:
                sample_rate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
        finally:
            os.remove(in_path)
            os.remove(out_path)

        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return samples, sample_rate


def get_voice_provider() -> VoiceProvider | None:
    """Returns None (text-only) unless VOICE_PROVIDER is explicitly set.
    RVC_MODEL_PATH, if set, wraps whichever base provider was selected in
    RVCVoiceProvider -- it's an optional layer on top of any of the three,
    not a separate VOICE_PROVIDER value of its own."""
    provider = os.environ.get("VOICE_PROVIDER", "none").lower()
    if provider == "local":
        base: VoiceProvider | None = LocalVoiceProvider()
    elif provider == "kokoro":
        base = KokoroVoiceProvider()
    elif provider == "elevenlabs":
        base = ElevenLabsProvider()
    else:
        base = None

    if base is None:
        return None

    rvc_model_path = os.environ.get("RVC_MODEL_PATH")
    if rvc_model_path:
        return RVCVoiceProvider(base, model_path=rvc_model_path)
    return base
