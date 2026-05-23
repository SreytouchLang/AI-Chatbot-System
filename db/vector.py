from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from core.config import get_settings
from utils.embedding_adapter import get_embeddings


@lru_cache
def get_vectorstore() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=settings.vector_collection_name,
        persist_directory=settings.vector_persist_directory,
        embedding_function=get_embeddings(),
    )


def vector_collection_count() -> int | None:
    collection = getattr(get_vectorstore(), "_collection", None)
    if collection is None or not hasattr(collection, "count"):
        return None
    return collection.count()


def similarity_search(query: str, *, k: int) -> list[Document]:
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
