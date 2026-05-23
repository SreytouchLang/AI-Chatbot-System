import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default

    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_description: str
    developer_name: str
    developer_display_name: str
    redis_host: str
    redis_port: int
    redis_password: str | None
    vector_collection_name: str
    vector_persist_directory: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    transcription_provider: str
    transcription_model: str
    retrieve_top_k: int
    recent_message_window: int
    summary_trigger_messages: int
    summary_max_lines: int
    ingest_chunk_size: int
    ingest_chunk_overlap: int
    download_timeout_seconds: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AI Chatbot System"),
        app_version=os.getenv("APP_VERSION", "2.0.0"),
        app_description=os.getenv(
            "APP_DESCRIPTION",
            "Document and media-aware chatbot with FastAPI, LangGraph, Redis memory, Chroma retrieval, and transcription support. Developed by Sreytouch Lang (Jessica).",
        ),
        developer_name=os.getenv("DEVELOPER_NAME", "Sreytouch Lang"),
        developer_display_name=os.getenv("DEVELOPER_DISPLAY_NAME", "Sreytouch Lang (Jessica)"),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=_get_int("REDIS_PORT", 6379),
        redis_password=os.getenv("REDIS_PASSWORD") or None,
        vector_collection_name=os.getenv("VECTOR_COLLECTION_NAME", "policies"),
        vector_persist_directory=os.getenv("VECTOR_PERSIST_DIRECTORY", "./chroma_db"),
        llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "openai").lower(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        transcription_provider=os.getenv("TRANSCRIPTION_PROVIDER", "openai").lower(),
        transcription_model=os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
        retrieve_top_k=_get_int("RETRIEVE_TOP_K", 3),
        recent_message_window=_get_int("RECENT_MESSAGE_WINDOW", 6),
        summary_trigger_messages=_get_int("SUMMARY_TRIGGER_MESSAGES", 4),
        summary_max_lines=_get_int("SUMMARY_MAX_LINES", 4),
        ingest_chunk_size=_get_int("INGEST_CHUNK_SIZE", 800),
        ingest_chunk_overlap=_get_int("INGEST_CHUNK_OVERLAP", 120),
        download_timeout_seconds=_get_int("DOWNLOAD_TIMEOUT_SECONDS", 30),
    )
