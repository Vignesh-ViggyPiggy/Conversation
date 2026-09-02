import os
from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


def _normalize(vector: list[float]) -> list[float]:
    arr = np.array(vector)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm else vector


class LocalEmbeddingProvider(EmbeddingProvider):
    """Offline embeddings via sentence-transformers. No API key; first call
    downloads the model (~90MB for the default)."""

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer

        name = model_name or os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Hosted embeddings via OpenAI's API. Needs OPENAI_API_KEY."""

    def __init__(self, model: str | None = None):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model or os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [_normalize(item.embedding) for item in response.data]


def get_embedding_provider() -> EmbeddingProvider:
    provider = os.environ.get("EMBEDDING_PROVIDER", "local").lower()
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    return LocalEmbeddingProvider()
