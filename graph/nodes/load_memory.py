from db.redis_client import load_conversation


def load_memory(state):
    return load_conversation(state["user_id"])
