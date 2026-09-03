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


class VoiceProvider(ABC):
    @abstractmethod
    def speak(self, text: str, avatar=None) -> None:
        """Synthesize and play text as audio. If `avatar` (an
        AvatarProvider) is given and this provider can expose raw audio,
        mouth movement is streamed in sync with playback."""
        ...


def _play_with_avatar_sync(samples, sample_rate: int, avatar) -> None:
    """Plays `samples` (float32, mono, in [-1, 1]) via sounddevice, and,
    if `avatar` is given, runs amplitude-based lip-sync in a background
    thread timed to match. Shared by every provider that can expose raw
    audio -- currently both of them."""
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


class LocalVoiceProvider(VoiceProvider):
    """Offline TTS via pyttsx3 (system voices: SAPI5 on Windows,
    NSSpeechSynthesizer on macOS, espeak on Linux). Zero setup, no API key,
    robotic quality, no usage limits.

    Renders to a temp WAV file (pyttsx3's save_to_file) instead of
    speaking directly through the engine -- speaking directly gives no
    access to the waveform at all, but rendering to a file first means the
    same raw samples can be played via sounddevice and, when an avatar is
    passed, analyzed for lip-sync -- same as ElevenLabsProvider, just
    fully local and free instead of needing an API key or usage quota.

    A fresh engine is created per speak() call rather than reused --
    pyttsx3's runAndWait() is documented to work reliably only once per
    engine instance; reusing one across calls can silently produce no
    audio, or hang outright, on the second and later calls."""

    def speak(self, text: str, avatar=None) -> None:
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
        _play_with_avatar_sync(samples, sample_rate, avatar)


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

    def speak(self, text: str, avatar=None) -> None:
        import numpy as np

        audio_chunks = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            output_format=f"pcm_{self.SAMPLE_RATE}",
        )
        audio_bytes = b"".join(audio_chunks)
        samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        _play_with_avatar_sync(samples, self.SAMPLE_RATE, avatar)


def get_voice_provider() -> VoiceProvider | None:
    """Returns None (text-only) unless VOICE_PROVIDER is explicitly set."""
    provider = os.environ.get("VOICE_PROVIDER", "none").lower()
    if provider == "local":
        return LocalVoiceProvider()
    if provider == "elevenlabs":
        return ElevenLabsProvider()
    return None
