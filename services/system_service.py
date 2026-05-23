import logging

from db.redis_client import ping_redis
from db.vector import get_vectorstore, vector_collection_count

logger = logging.getLogger(__name__)


def get_system_health() -> dict[str, object]:
    status = "ok"
    checks: dict[str, dict[str, object]] = {}

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
