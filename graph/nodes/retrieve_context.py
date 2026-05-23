from core.config import get_settings
from db.vector import similarity_search

settings = get_settings()

def retrieve_context(state):
    docs = similarity_search(
        state["question"],
        k=state.get("top_k", settings.retrieve_top_k),
    )

    context_parts: list[str] = []
    source_documents: list[dict[str, object]] = []

    for doc in docs:
        content = (doc.page_content or "").strip()
        if not content:
            continue

        metadata = doc.metadata or {}
        page_number = metadata.get("page_number")
        if page_number is None and isinstance(metadata.get("page"), int):
            page_number = metadata["page"] + 1

        context_parts.append(content)
        source_documents.append(
            {
                "source_file": metadata.get("source_file", "unknown"),
                "page_number": page_number,
                "excerpt": content[:240],
            }
        )

    return {
        "context": "\n\n".join(context_parts),
        "source_documents": source_documents,
    }
