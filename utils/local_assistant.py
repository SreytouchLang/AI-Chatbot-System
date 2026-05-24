import re
from collections.abc import Iterable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "their",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
    "you",
    "your",
}
_GREETING_TOKENS = {"hello", "hi", "hey", "morning", "afternoon", "evening"}
_QUESTION_SYNONYMS = {
    "payment": {"invoice", "due", "billing", "paid"},
    "term": {"due", "timeline", "policy"},
    "refund": {"return", "receipt", "cancel"},
    "policy": {"rule", "guideline", "term"},
}


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def _normalize_token(token: str) -> str:
    lowered = token.lower()
    if len(lowered) > 4 and lowered.endswith("ies"):
        return f"{lowered[:-3]}y"
    if len(lowered) > 4 and lowered.endswith("es"):
        return lowered[:-2]
    if len(lowered) > 3 and lowered.endswith("s"):
        return lowered[:-1]
    return lowered


def _content_tokens(text: str) -> set[str]:
    return {
        _normalize_token(token)
        for token in _TOKEN_RE.findall(text or "")
        if token not in _STOP_WORDS and len(token) > 1
    }


def _question_tokens(text: str) -> set[str]:
    tokens = _content_tokens(text)
    expanded = set(tokens)
    for token in tokens:
        expanded.update(_QUESTION_SYNONYMS.get(token, set()))
    return expanded


def _split_sentences(text: str) -> list[str]:
    parts = [
        " ".join(segment.split())
        for segment in _SENTENCE_SPLIT_RE.split((text or "").strip())
    ]
    return [part for part in parts if part]


def _score_sentence(sentence: str, question_tokens: set[str]) -> int:
    if not question_tokens:
        return 0
    sentence_tokens = _content_tokens(sentence)
    overlap = sentence_tokens & question_tokens
    if not overlap:
        return 0
    penalty = 2 if len(sentence_tokens) <= 4 else 0
    return (len(overlap) * 3 + min(len(sentence_tokens), 12)) - penalty


def _top_sentences(context: str, question: str, limit: int = 2) -> list[str]:
    sentences = _split_sentences(context)
    if not sentences:
        return []

    question_tokens = _question_tokens(question)
    ranked = sorted(
        enumerate(sentences),
        key=lambda item: (_score_sentence(item[1], question_tokens), len(item[1])),
        reverse=True,
    )

    selected: list[str] = []
    for _, sentence in ranked:
        if sentence in selected:
            continue
        if question_tokens and _score_sentence(sentence, question_tokens) <= 0 and selected:
            continue
        selected.append(sentence)
        if len(selected) >= limit:
            break

    if not selected:
        selected = sentences[:limit]

    return selected


def build_local_answer(
    *,
    question: str,
    context: str,
    source_documents: list[dict[str, object]] | None = None,
) -> str:
    normalized_question = " ".join((question or "").split())
    question_tokens = _question_tokens(normalized_question)

    if not context.strip():
        if question_tokens & _GREETING_TOKENS or normalized_question.lower() in _GREETING_TOKENS:
            return (
                "I’m ready to help with your documents. Upload a PDF or DOCX, then ask a question "
                "about what it says."
            )
        return (
            "I couldn't find supporting text in the uploaded files yet. Upload a PDF or DOCX, "
            "then ask a question about its contents."
        )

    selected_sentences = _top_sentences(context, normalized_question, limit=2)
    if selected_sentences and len(selected_sentences[0]) > 48:
        selected_sentences = selected_sentences[:1]
    answer_body = " ".join(selected_sentences).strip()
    if not answer_body:
        answer_body = _truncate(context, 240)

    source_file = ""
    if source_documents:
        first_source = source_documents[0].get("source_file")
        if isinstance(first_source, str) and first_source.strip():
            source_file = first_source.strip()

    if source_file:
        return f"Based on {source_file}, {answer_body}"
    return f"Based on the uploaded files, {answer_body}"


def build_local_summary(
    *,
    previous_summary: str,
    messages: Iterable[BaseMessage],
    max_lines: int,
) -> str:
    materialized = list(messages)
    user_messages = [
        _truncate(message.content, 120)
        for message in materialized
        if isinstance(message, HumanMessage) and isinstance(message.content, str)
    ]
    ai_messages = [
        _truncate(message.content, 140)
        for message in materialized
        if isinstance(message, AIMessage) and isinstance(message.content, str)
    ]

    lines: list[str] = []
    if previous_summary.strip() and not (user_messages or ai_messages):
        lines.append(_truncate(previous_summary, 140))
    if user_messages:
        lines.append(f"User asked: {user_messages[-1]}")
    if ai_messages:
        lines.append(f"Assistant answered: {ai_messages[-1]}")

    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines[:max_lines])
