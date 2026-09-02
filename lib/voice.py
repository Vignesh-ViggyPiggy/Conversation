import os
from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Synthesize and play text as audio."""
        ...


class LocalVoiceProvider(VoiceProvider):
    """Offline TTS via pyttsx3 (system voices). Zero setup, no API key, robotic quality."""

    def __init__(self):
        import pyttsx3

        self.engine = pyttsx3.init()

    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()


class ElevenLabsProvider(VoiceProvider):
    """Hosted TTS via ElevenLabs. Needs an API key and a chosen or cloned voice_id."""

    def __init__(self, voice_id: str | None = None):
        from elevenlabs import play
        from elevenlabs.client import ElevenLabs

        self._play = play
        self.client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
        self.voice_id = voice_id or os.environ.get("VOICE_ID")

    def speak(self, text: str) -> None:
        audio = self.client.text_to_speech.convert(voice_id=self.voice_id, text=text)
        self._play(audio)


def get_voice_provider() -> VoiceProvider | None:
    """Returns None (text-only) unless VOICE_PROVIDER is explicitly set."""
    provider = os.environ.get("VOICE_PROVIDER", "none").lower()
    if provider == "local":
        return LocalVoiceProvider()
    if provider == "elevenlabs":
        return ElevenLabsProvider()
    return None
