import io
import os
import wave
from abc import ABC, abstractmethod

import numpy as np


class STTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        ...


class LocalSTTProvider(STTProvider):
    """Offline transcription via faster-whisper. No API key; first call
    downloads the model."""

    def __init__(self, model_size: str | None = None):
        from faster_whisper import WhisperModel

        size = model_size or os.environ.get("STT_MODEL", "base.en")
        self.model = WhisperModel(size, compute_type="int8")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        segments, _ = self.model.transcribe(audio, language="en")
        return " ".join(segment.text.strip() for segment in segments).strip()


def _to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    clipped = np.clip(audio, -1.0, 1.0)
    pcm16 = (clipped * 32767).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())
    buffer.seek(0)
    return buffer.read()


class OpenAISTTProvider(STTProvider):
    """Hosted transcription via OpenAI's audio API. Needs OPENAI_API_KEY."""

    def __init__(self, model: str | None = None):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model or os.environ.get("STT_MODEL", "whisper-1")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        buffer = io.BytesIO(_to_wav_bytes(audio, sample_rate))
        buffer.name = "audio.wav"
        response = self.client.audio.transcriptions.create(model=self.model, file=buffer)
        return response.text.strip()


def get_stt_provider() -> STTProvider:
    provider = os.environ.get("STT_PROVIDER", "local").lower()
    if provider == "openai":
        return OpenAISTTProvider()
    return LocalSTTProvider()
