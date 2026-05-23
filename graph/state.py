from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

class SourceDocument(TypedDict):
    source_file: str
    excerpt: str
    page_number: int | None


class State(TypedDict, total=False):
    user_id: str
    question: str
    top_k: int
    messages: list[BaseMessage]
    summary: str
    context: str
    source_documents: list[SourceDocument]
    answer: str
