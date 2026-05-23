from fastapi import APIRouter, File, Form, UploadFile
from schemas.router_schema import IngestRequest, IngestResponse
from services.ingest_service import ingest_file, ingest_uploaded_file

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_controller(request: IngestRequest) -> IngestResponse:
    result = ingest_file(request.file_name, str(request.source_url))
    return IngestResponse(data=result)


@router.post("/ingest/upload", response_model=IngestResponse)
async def ingest_upload_controller(
    file: UploadFile = File(...),
    file_name: str | None = Form(None),
) -> IngestResponse:
    result = await ingest_uploaded_file(file, file_name)
    return IngestResponse(data=result)
