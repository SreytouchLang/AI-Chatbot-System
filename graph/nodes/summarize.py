from langchain_core.messages import HumanMessage, SystemMessage

from core.config import get_settings, is_llm_remote_available
from utils.local_assistant import build_local_summary
from utils.llm_adapter import get_llm

settings = get_settings()


def summarize(state):
    messages = state.get("messages") or []

    if len(messages) < settings.summary_trigger_messages:
        return {
            "summary": state.get("summary", ""),
            "messages": messages,
        }

    text = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in messages
    )
    if is_llm_remote_available():
        summary = get_llm(temperature=0, max_tokens=120).invoke(
            [
                SystemMessage(
                    content=(
                        "Summarize the conversation compactly for future context retention. "
                        "Preserve the user's goals, important facts, and answers already given."
                    )
                ),
                HumanMessage(
                    content=f"""
Existing summary:
{state.get("summary", "No summary yet.")}

Summarize this conversation in at most {settings.summary_max_lines} short lines.
- Focus on user intent, important questions, and useful answers.
- Write the summary in the primary language the user is using.

Conversation:
{text}
""".strip()
                )
            ]
        )
        next_summary = summary.content if isinstance(summary.content, str) else str(summary.content)
    else:
        next_summary = build_local_summary(
            previous_summary=state.get("summary", ""),
            messages=messages,
            max_lines=settings.summary_max_lines,
        )
    return {"summary": next_summary, "messages": messages[-settings.recent_message_window:]}
