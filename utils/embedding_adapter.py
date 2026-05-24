import hashlib
import math
import re
from functools import lru_cache

from core.config import get_settings, is_embedding_remote_available

_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


class LocalHashEmbeddings:
    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = _TOKEN_RE.findall((text or "").lower())
        if not tokens:
            return vector

        for token in tokens:
            bucket = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % self.dimension
            vector[bucket] += 1.0

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


@lru_cache
def get_embeddings():
    settings = get_settings()

    if settings.embedding_provider == "openai":
        if not is_embedding_remote_available():
            return LocalHashEmbeddings()
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=settings.embedding_model)

    if settings.embedding_provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=settings.embedding_model)

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {settings.embedding_provider}")
