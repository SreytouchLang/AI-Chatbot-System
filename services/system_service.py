import logging

from core.config import (
    get_settings,
    has_configured_secret,
    is_embedding_remote_available,
    is_llm_remote_available,
    is_transcription_available,
)
from db.redis_client import ping_redis
from db.vector import get_vectorstore, vector_collection_count

logger = logging.getLogger(__name__)

def get_setup_status() -> dict[str, object]:
    settings = get_settings()
    openai_missing = not has_configured_secret("OPENAI_API_KEY")
    missing: list[str] = []

    if "openai" in {
        settings.llm_provider,
        settings.embedding_provider,
        settings.transcription_provider,
    } and openai_missing:
        missing.append("OPENAI_API_KEY")

    if settings.llm_provider == "anthropic" and not has_configured_secret("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")

    if settings.llm_provider == "groq" and not has_configured_secret("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")

    if not is_llm_remote_available() or not is_embedding_remote_available():
        message = (
            "Demo mode is active. PDF and DOCX ingestion plus grounded chat work here. "
            "Add OPENAI_API_KEY to enable OpenAI answers and audio/video transcription."
        )
        return {
            "status": "local_mode",
            "ready": True,
            "missing": missing,
            "message": message,
            "mode": "local",
            "media_ready": is_transcription_available(),
        }

    if missing:
        keys_text = ", ".join(missing)
        return {
            "status": "needs_attention",
            "ready": False,
            "missing": missing,
            "message": f"Setup required: add {keys_text} to .env, restart the app, and refresh this page.",
            "mode": "blocking",
            "media_ready": is_transcription_available(),
        }

    return {
        "status": "ok",
        "ready": True,
        "missing": [],
        "message": "Setup complete.",
        "mode": "full",
        "media_ready": is_transcription_available(),
    }


def get_system_health() -> dict[str, object]:
    status = "ok"
    checks: dict[str, dict[str, object]] = {}

    setup = get_setup_status()
    if setup["ready"]:
        checks["setup"] = {
            "status": str(setup["status"]),
            "message": str(setup["message"]),
            "mode": setup.get("mode"),
            "missing": setup.get("missing", []),
            "media_ready": setup.get("media_ready", False),
        }
    else:
        status = "degraded"
        checks["setup"] = {
            "status": "error",
            "message": str(setup["message"]),
            "missing": setup["missing"],
        }

    try:
        ping_redis()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        status = "degraded"
        checks["redis"] = {"status": "error", "message": str(exc)}

    try:
        get_vectorstore()
        document_count = vector_collection_count()
        payload: dict[str, object] = {"status": "ok"}
        if document_count is not None:
            payload["documents"] = document_count
        checks["vectorstore"] = payload
    except Exception as exc:
        status = "degraded"
        checks["vectorstore"] = {"status": "error", "message": str(exc)}

    return {"status": status, "data": checks}


def log_startup_health() -> None:
    health = get_system_health()
    for name, payload in health["data"].items():
        if payload["status"] == "ok":
            logger.info("%s check passed", name)
        else:
            logger.warning("%s check failed: %s", name, payload.get("message", "unknown error"))
