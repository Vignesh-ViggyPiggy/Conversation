import os
import threading
from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    @abstractmethod
    def speak(self, text: str, avatar=None) -> None:
        """Synthesize and play text as audio. If `avatar` (a
        VTubeStudioClient) is given and this provider can expose raw audio,
        mouth movement is streamed in sync with playback."""
        ...


class LocalVoiceProvider(VoiceProvider):
    """Offline TTS via pyttsx3 (system voices). Zero setup, no API key,
    robotic quality. Does not support avatar lip-sync -- pyttsx3 calls the
    OS speech engine directly and never exposes raw audio to analyze."""

    def __init__(self):
        import pyttsx3

        self.engine = pyttsx3.init()

    def speak(self, text: str, avatar=None) -> None:
        self.engine.say(text)
        self.engine.runAndWait()


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
        import sounddevice as sd

        audio_chunks = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            output_format=f"pcm_{self.SAMPLE_RATE}",
        )
        audio_bytes = b"".join(audio_chunks)
        samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        lipsync_thread = None
        if avatar is not None:
            from avatar import animate_mouth_from_audio

            lipsync_thread = threading.Thread(
                target=animate_mouth_from_audio,
                args=(avatar, samples, self.SAMPLE_RATE),
                daemon=True,
            )
            lipsync_thread.start()

        sd.play(samples, samplerate=self.SAMPLE_RATE)
        sd.wait()
        if lipsync_thread is not None:
            lipsync_thread.join(timeout=1)


def get_voice_provider() -> VoiceProvider | None:
    """Returns None (text-only) unless VOICE_PROVIDER is explicitly set."""
    provider = os.environ.get("VOICE_PROVIDER", "none").lower()
    if provider == "local":
        return LocalVoiceProvider()
    if provider == "elevenlabs":
        return ElevenLabsProvider()
    return None
