"""
Source Registry Schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceRegistryOut(BaseModel):
    id: str
    organization_name: str
    source_name: str
    base_url: str
    country_code: str
    region: Optional[str] = None
    source_type: str
    trust_tier: str
    authority_type: str
    license_type: str
    license_status: str
    reuse_allowed: bool
    full_text_storage_allowed: bool
    attribution_required: bool
    attribution_text: Optional[str] = None
    reuse_policy_url: Optional[str] = None
    crawl_frequency: str
    active: bool
    last_reviewed: Optional[str] = None


class SourceDetailOut(SourceRegistryOut):
    terms_url: Optional[str] = None
    robots_url: Optional[str] = None
    supported_languages: List[str] = Field(default_factory=list)
    document_count: int = 0
    records_supported_count: int = 0
    health_status: Optional[str] = "HEALTHY"
