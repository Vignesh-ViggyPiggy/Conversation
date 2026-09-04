"""Kokoro TTS as a tiny local HTTP server, isolated in its own Python
3.10/3.11 venv -- kokoro pins numpy exactly and has no prebuilt wheel for
Python 3.13 (the main app's version), so it can't live in the same
environment. This mirrors how the main app already treats Ollama as an
external service rather than an in-process import.

Setup (from this directory):
    python3.11 -m venv .venv
    .venv\\Scripts\\activate        (Windows)   or   source .venv/bin/activate   (macOS/Linux)
    pip install -r requirements.txt
    uvicorn server:app --host 0.0.0.0 --port 8500

Then set KOKORO_SERVER_URL=http://localhost:8500 (the default) in the
main app's .env and VOICE_PROVIDER=kokoro.
"""

import io
import wave

import numpy as np
from fastapi import FastAPI, Response
from kokoro import KPipeline
from pydantic import BaseModel

SAMPLE_RATE = 24000

app = FastAPI()
_pipelines: dict[str, KPipeline] = {}


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    lang_code: str = "a"


def _get_pipeline(lang_code: str) -> KPipeline:
    # Cached per lang_code -- KPipeline() loads model weights, expensive
    # to redo on every request.
    if lang_code not in _pipelines:
        _pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return _pipelines[lang_code]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    pipeline = _get_pipeline(req.lang_code)

    chunks = []
    for _graphemes, _phonemes, audio in pipeline(req.text, voice=req.voice):
        if hasattr(audio, "numpy"):
            audio = audio.numpy()
        chunks.append(np.asarray(audio, dtype=np.float32))

    samples = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    pcm16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm16.tobytes())

    return Response(content=buf.getvalue(), media_type="audio/wav")
