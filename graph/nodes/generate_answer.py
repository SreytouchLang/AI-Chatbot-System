from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.config import get_settings
from utils.llm_adapter import get_llm

chat = get_llm(temperature=0, max_tokens=120)
settings = get_settings()


def generate_answer(state):
    summary = state.get("summary", "")
    messages = state.get("messages") or []
    context = state.get("context", "")

    recent = messages[-settings.recent_message_window:]

    history = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in recent
    )

    response = chat.invoke(
        [
            SystemMessage(
                content=(
                    "You are a careful AI assistant for a document-aware chatbot. "
                    "Use retrieved document context first when it is relevant. "
                    "If the documents do not contain the answer, say that clearly instead of inventing facts. "
                    "Reply in the same primary language as the user's latest message."
                )
            ),
            HumanMessage(
                content=f"""
Conversation summary:
{summary or "No summary yet."}

Recent conversation:
{history or "No recent conversation."}

Retrieved document context:
{context or "No relevant document context was retrieved."}

User question:
{state["question"]}

Rules:
- Prefer the uploaded document context when it answers the question.
- If the context is insufficient, say you could not find the answer in the uploaded documents.
- Be concise, clear, and useful.
- Do not mention internal implementation details.
""".strip()
            ),
        ]
    )

    answer = response.content.strip() if isinstance(response.content, str) else str(response.content)

    return {
        "answer": answer,
        "messages": messages + [
            HumanMessage(content=state["question"]),
            AIMessage(content=answer),
        ],
    }
