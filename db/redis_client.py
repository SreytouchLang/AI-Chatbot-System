import json
from functools import lru_cache

import redis
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from core.config import get_settings


@lru_cache
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=True,
    )


def ping_redis() -> bool:
    return bool(get_redis_client().ping())


def load_conversation(user_id: str) -> dict[str, object]:
    data = get_redis_client().get(user_id)
    if not data:
        return {"messages": [], "summary": ""}

    payload = json.loads(data)
    messages: list[BaseMessage] = []

    for item in payload.get("messages", []):
        role = item.get("role")
        content = item.get("content", "")
        if not content:
            continue

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            messages.append(AIMessage(content=content))

    return {
        "messages": messages,
        "summary": payload.get("summary", ""),
    }


def save_conversation(user_id: str, messages: list[BaseMessage], summary: str) -> None:
    serialized: list[dict[str, str]] = []

    for message in messages:
        if isinstance(message, HumanMessage):
            serialized.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            serialized.append({"role": "ai", "content": message.content})

    get_redis_client().set(
        user_id,
        json.dumps({"summary": summary, "messages": serialized}),
    )
