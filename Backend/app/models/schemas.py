from typing import Any, Optional
from pydantic import BaseModel, Field


class CallRequest(BaseModel):
    message: str = Field(..., min_length=1)
    to_phone_number: str = Field(..., min_length=7)
    language_code: str = "en-IN"


class SourceDocument(BaseModel):
    file: str
    page: int
    doc_type: str
    manufacturer: str = "unknown"
    domain: str = "unknown"
    chunk_excerpt: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    domain_filter: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    query_metadata: dict[str, Any]


class IngestResponse(BaseModel):
    status: str
    documents_indexed: int
    total_chunks: int
    skipped_duplicates: int
    failed_documents: list[str] = []


class SupervisorDecision(BaseModel):
    """Final decision returned by the industrial supervisor."""

    issue: str = Field(description="Short description of the machine issue.")
    worker_can_resolve: bool = Field(
        description="True only when safe operator-level troubleshooting is sufficient."
    )
    confidence: float = Field(ge=0.0, le=1.0)
    troubleshooting_message: Optional[str] = Field(default=None)
    technician_message: Optional[str] = Field(default=None)
    manual_sources: list[SourceDocument] = Field(default_factory=list)
    technician_alert_sent: bool = False
    technician_call_sid: Optional[str] = None


class SuperviseTextRequest(BaseModel):
    message: str = Field(..., min_length=1)
    domain_filter: Optional[str] = None
    worker_id: Optional[str] = None
    machine_id: Optional[str] = None
    issue_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    collection: str
    total_chunks: int
    documents: list[str]
