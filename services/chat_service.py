from functools import lru_cache

from core.exceptions import DependencyUnavailableError
from graph.builder import build_graph


@lru_cache
def get_chat_graph():
    return build_graph()


def conversation(user_id: str, q: str, top_k: int = 3) -> dict[str, object]:
    try:
        result = get_chat_graph().invoke(
            {
                "user_id": user_id,
                "question": q,
                "top_k": top_k,
            }
        )
    except Exception as exc:
        raise DependencyUnavailableError(
            "Chat service is unavailable right now.",
            details={"reason": str(exc)},
        ) from exc

    return {
        "user_id": user_id,
        "answer": result.get("answer", ""),
        "summary": result.get("summary", ""),
        "sources": result.get("source_documents", []),
    }
