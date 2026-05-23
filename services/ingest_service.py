from fastapi import UploadFile

from core.exceptions import IngestionError
from ingest.policies import process_uploaded_file, process_url_file


def ingest_file(file_name: str, source_url: str) -> dict[str, object]:
    try:
        return process_url_file(file_name, source_url)
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(
            "Unable to ingest the file right now.",
            details={"reason": str(exc)},
        ) from exc


async def ingest_uploaded_file(
    upload: UploadFile,
    file_name: str | None = None,
) -> dict[str, object]:
    try:
        file_bytes = await upload.read()
        original_filename = upload.filename or "document"
        return process_uploaded_file(
            original_filename,
            file_bytes,
            file_name=file_name,
        )
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(
            "Unable to ingest the uploaded file right now.",
            details={
                "file_name": upload.filename or "document",
                "reason": str(exc),
            },
        ) from exc
    finally:
        await upload.close()
