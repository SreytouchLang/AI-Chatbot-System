from functools import lru_cache
from pathlib import Path

from openai import OpenAI

from core.config import get_settings, is_transcription_available
from core.exceptions import IngestionError


@lru_cache
def get_transcription_client() -> OpenAI:
    settings = get_settings()
    if settings.transcription_provider != "openai":
        raise IngestionError(
            "Media transcription currently supports only the OpenAI provider.",
            details={"provider": settings.transcription_provider},
        )
    if not is_transcription_available():
        raise IngestionError(
            "Audio and video transcription need a real OPENAI_API_KEY. PDF and DOCX still work in local mode."
        )
    return OpenAI()


def transcribe_media(file_path: str) -> str:
    settings = get_settings()

    try:
        client = get_transcription_client()
        with open(file_path, "rb") as media_file:
            response = client.audio.transcriptions.create(
                model=settings.transcription_model,
                file=media_file,
            )
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(
            "Failed to transcribe the media file.",
            details={"file_name": Path(file_path).name, "reason": str(exc)},
        ) from exc

    transcript_text = getattr(response, "text", None)
    if isinstance(response, dict) and not transcript_text:
        transcript_text = response.get("text")

    cleaned = (transcript_text or "").strip()
    if not cleaned:
        raise IngestionError("The media file did not return any transcript text.")

    return cleaned
