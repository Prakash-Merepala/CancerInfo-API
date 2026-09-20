"""
Common Pydantic Schemas and Response Envelopes
"""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from app.core.constants import MEDICAL_DISCLAIMER

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Number of records per page")
    total_records: int = Field(..., description="Total number of matching records")
    total_pages: int = Field(..., description="Total pages available")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_prev: bool = Field(..., description="Whether a preceding page exists")


class MetaInfo(BaseModel):
    api_version: str = Field(default="v1", description="CancerInfo API version")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    result_count: int = Field(..., description="Number of results in this response")
    disclaimer: str = Field(default=MEDICAL_DISCLAIMER)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class StandardResponse(BaseModel, Generic[T]):
    data: T
    meta: MetaInfo
    pagination: Optional[PaginationMeta] = None
