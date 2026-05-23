from functools import lru_cache

from core.config import get_settings


@lru_cache
def get_embeddings():
    settings = get_settings()

    if settings.embedding_provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=settings.embedding_model)

    if settings.embedding_provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=settings.embedding_model)

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {settings.embedding_provider}")
