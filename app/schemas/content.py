"""
Content & Fact-Level Provenance Schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.cancer import CancerSummaryOut


class JurisdictionOut(BaseModel):
    scope: str
    country: str
    region: Optional[str] = None


class ProvenanceSourceOut(BaseModel):
    source_id: str
    organization: str
    source_name: str
    url: str
    trust_tier: str
    source_updated_at: Optional[str] = None
    retrieved_at: str
    last_verified_at: str
    license_status: str
    attribution_text: Optional[str] = None
    quote_snippet: Optional[str] = None


class ContentRecordOut(BaseModel):
    id: str
    category: str
    subcategory: Optional[str] = None
    content: str
    content_type: str
    jurisdiction: JurisdictionOut
    language: str
    audience: str
    disagreement_status: str
    disagreement_notes: Optional[str] = None
    version_number: int
    updated_at: str
    sources: List[ProvenanceSourceOut] = Field(default_factory=list)


class CancerCategoryDataOut(BaseModel):
    cancer: CancerSummaryOut
    category: str
    category_name: str
    category_description: str
    records: List[ContentRecordOut]


class ContentVersionOut(BaseModel):
    version_number: int
    content: str
    change_type: str
    change_reason: Optional[str] = None
    content_hash: str
    created_at: str
