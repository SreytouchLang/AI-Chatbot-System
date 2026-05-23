from urllib.parse import urlparse

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl, field_validator

SUPPORTED_URL_FILE_TYPES = (
    ".aac",
    ".aif",
    ".aiff",
    ".avi",
    ".caf",
    ".docx",
    ".flac",
    ".m4a",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".ogg",
    ".pdf",
    ".wav",
    ".webm",
    ".wma",
)


class IngestRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    file_name: str = Field(..., min_length=1, max_length=120)
    source_url: HttpUrl = Field(
        ...,
        validation_alias=AliasChoices("source_url", "s3_url"),
        serialization_alias="source_url",
    )

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("file_name cannot be empty")
        return cleaned

    @field_validator("source_url")
    @classmethod
    def must_be_supported_document(cls, value: HttpUrl) -> HttpUrl:
        if not urlparse(str(value)).path.lower().endswith(SUPPORTED_URL_FILE_TYPES):
            raise ValueError(
                "source_url must point to a supported PDF, DOCX, audio, or video file"
            )
        return value


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(default="user_1", min_length=1, max_length=100)
    q: str = Field(..., min_length=1, description="User message")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of context chunks to retrieve")


class SourceDocumentResponse(BaseModel):
    source_file: str
    page_number: int | None = None
    excerpt: str


class ChatResponseData(BaseModel):
    user_id: str
    answer: str
    summary: str
    sources: list[SourceDocumentResponse] = Field(default_factory=list)


class ChatResponse(BaseModel):
    status: str = "success"
    data: ChatResponseData


class IngestResponseData(BaseModel):
    file_name: str
    source_url: str | None = None
    status: str
    file_hash: str | None = None
    num_pages: int = 0
    num_chunks: int = 0
    reason: str | None = None
    file_type: str | None = None
    input_type: str | None = None


class IngestResponse(BaseModel):
    status: str = "success"
    data: IngestResponseData
