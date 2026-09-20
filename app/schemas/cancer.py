"""
Cancer Schemas
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CancerAliasOut(BaseModel):
    alias: str
    language: str
    alias_type: str
    country_code: Optional[str] = None
    confidence: float


class CancerSummaryOut(BaseModel):
    id: str
    slug: str
    canonical_name: str
    anatomical_site: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)


class CancerDetailOut(BaseModel):
    id: str
    slug: str
    canonical_name: str
    description: Optional[str] = None
    anatomical_site: Optional[str] = None
    aliases: List[CancerAliasOut] = Field(default_factory=list)
    taxonomy_codes: Dict[str, str] = Field(default_factory=dict)
    available_categories: List[str] = Field(default_factory=list)
    record_counts_by_category: Dict[str, int] = Field(default_factory=dict)


class CancerCategorySectionOut(BaseModel):
    category: str
    name: str
    description: str
    record_count: int
    countries_represented: List[str]
