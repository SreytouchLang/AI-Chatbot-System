from functools import lru_cache

from core.config import get_settings


@lru_cache
def get_llm(temperature: float = 0, max_tokens: int = 1000):
    settings = get_settings()

    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=settings.llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
