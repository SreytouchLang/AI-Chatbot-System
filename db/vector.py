import re
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from core.config import get_settings, is_embedding_remote_available
from utils.embedding_adapter import get_embeddings

_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")
_QUERY_SYNONYMS = {
    "payment": {"invoice", "due", "billing", "paid"},
    "term": {"due", "timeline", "policy"},
    "refund": {"return", "receipt", "cancel"},
    "policy": {"rule", "guideline", "term"},
}


def _normalize_token(token: str) -> str:
    lowered = token.lower()
    if len(lowered) > 4 and lowered.endswith("ies"):
        return f"{lowered[:-3]}y"
    if len(lowered) > 4 and lowered.endswith("es"):
        return lowered[:-2]
    if len(lowered) > 3 and lowered.endswith("s"):
        return lowered[:-1]
    return lowered


def _tokens(text: str) -> set[str]:
    return {_normalize_token(token) for token in _TOKEN_RE.findall(text or "")}


def _query_tokens(text: str) -> set[str]:
    tokens = _tokens(text)
    expanded = set(tokens)
    for token in tokens:
        expanded.update(_QUERY_SYNONYMS.get(token, set()))
    return expanded


def _rerank_documents(query: str, documents: list[Document], limit: int) -> list[Document]:
    query_tokens = _query_tokens(query)
    if not query_tokens:
        return documents[:limit]

    ranked = sorted(
        documents,
        key=lambda document: (
            len(query_tokens & _tokens(document.page_content or "")),
            len(document.page_content or ""),
        ),
        reverse=True,
    )
    filtered = [
        document
        for document in ranked
        if query_tokens & _tokens(document.page_content or "")
    ]
    return (filtered or ranked)[:limit]


def _all_documents() -> list[Document]:
    vectorstore = get_vectorstore()
    getter = getattr(vectorstore, "get", None)
    result = None

    if callable(getter):
        try:
            result = getter()
        except TypeError:
            result = getter(include=["documents", "metadatas"])
        except Exception:
            result = None

    if result is None:
        collection = getattr(vectorstore, "_collection", None)
        if collection is None:
            return []
        try:
            result = collection.get(include=["documents", "metadatas"])
        except Exception:
            return []

    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    return [
        Document(page_content=content or "", metadata=metadata or {})
        for content, metadata in zip(documents, metadatas)
        if content
    ]


def _collection_name() -> str:
    settings = get_settings()
    if settings.embedding_provider == "openai" and not is_embedding_remote_available():
        return f"{settings.vector_collection_name}_local"
    return settings.vector_collection_name


@lru_cache
def get_vectorstore() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=_collection_name(),
        persist_directory=settings.vector_persist_directory,
        embedding_function=get_embeddings(),
    )


def vector_collection_count() -> int | None:
    collection = getattr(get_vectorstore(), "_collection", None)
    if collection is None or not hasattr(collection, "count"):
        return None
    return collection.count()


def similarity_search(query: str, *, k: int) -> list[Document]:
    if not is_embedding_remote_available():
        documents = _all_documents() or get_vectorstore().similarity_search(query, k=max(k * 4, 8))
        return _rerank_documents(query, documents, k)
    return get_vectorstore().similarity_search(query, k=k)


def add_documents(documents: list[Document]) -> None:
    get_vectorstore().add_documents(documents)


def file_hash_exists(file_hash: str) -> bool:
    vectorstore = get_vectorstore()
    getter = getattr(vectorstore, "get", None)

    if callable(getter):
        try:
            result = getter(where={"file_hash": file_hash}, limit=1)
            ids = (result or {}).get("ids") or []
            if ids:
                return True
        except TypeError:
            pass
        except Exception:
            pass

    collection = getattr(vectorstore, "_collection", None)
    if collection is None:
        return False

    try:
        result = collection.get(where={"file_hash": file_hash}, limit=1)
    except TypeError:
        result = collection.get(where={"file_hash": file_hash})

    ids = (result or {}).get("ids") or []
    return bool(ids)
