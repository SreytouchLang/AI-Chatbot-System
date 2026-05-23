from db.redis_client import save_conversation

def store_memory(state):

    messages = state.get("messages") or []
    save_conversation(
        state["user_id"],
        messages,
        state.get("summary", ""),
    )

    return state
