"""
Source Registry Endpoints (Section 8)
"""
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.errors import SourceNotFoundError
from app.database.session import get_db
from app.repositories.source_repo import SourceRepository
from app.schemas.common import MetaInfo, PaginationMeta, StandardResponse
from app.schemas.source import SourceDetailOut, SourceRegistryOut

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=StandardResponse[List[SourceRegistryOut]])
def list_sources(
    country: Optional[str] = Query(None, description="Country filter, e.g. 'US', 'GB', 'GLOBAL'"),
    tier: Optional[str] = Query(None, description="Trust Tier, e.g. 'Tier 1'"),
    active: bool = Query(True, description="Filter active sources"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List approved authoritative sources registered in the Source Registry.
    """
    repo = SourceRepository(db)
    skip = (page - 1) * limit
    sources, total = repo.list_sources(
        country=country,
        trust_tier=tier,
        active_only=active,
        skip=skip,
        limit=limit,
    )

    data = [
        SourceRegistryOut(
            id=s.id,
            organization_name=s.organization_name,
            source_name=s.source_name,
            base_url=s.base_url,
            country_code=s.country_code,
            region=s.region,
            source_type=s.source_type,
            trust_tier=s.trust_tier,
            authority_type=s.authority_type,
            license_type=s.license_type,
            license_status=s.license_status,
            reuse_allowed=s.reuse_allowed,
            full_text_storage_allowed=s.full_text_storage_allowed,
            attribution_required=s.attribution_required,
            attribution_text=s.attribution_text,
            reuse_policy_url=s.reuse_policy_url,
            crawl_frequency=s.crawl_frequency,
            active=s.active,
            last_reviewed=s.last_reviewed.isoformat() + "Z" if s.last_reviewed else None,
        )
        for s in sources
    ]

    total_pages = math.ceil(total / limit) if limit > 0 else 1

    return StandardResponse(
        data=data,
        meta=MetaInfo(result_count=len(data)),
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get("/{id}", response_model=StandardResponse[SourceDetailOut])
def get_source(
    id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information, licensing terms, operational metrics, and health status for a specific source.
    """
    repo = SourceRepository(db)
    source = repo.get_source_by_id(id)
    if not source:
        raise SourceNotFoundError(id)

    metrics = repo.get_source_metrics(source.id)

    detail = SourceDetailOut(
        id=source.id,
        organization_name=source.organization_name,
        source_name=source.source_name,
        base_url=source.base_url,
        country_code=source.country_code,
        region=source.region,
        source_type=source.source_type,
        trust_tier=source.trust_tier,
        authority_type=source.authority_type,
        license_type=source.license_type,
        license_status=source.license_status,
        reuse_allowed=source.reuse_allowed,
        full_text_storage_allowed=source.full_text_storage_allowed,
        attribution_required=source.attribution_required,
        attribution_text=source.attribution_text,
        reuse_policy_url=source.reuse_policy_url,
        terms_url=source.terms_url,
        robots_url=source.robots_url,
        crawl_frequency=source.crawl_frequency,
        active=source.active,
        last_reviewed=source.last_reviewed.isoformat() + "Z" if source.last_reviewed else None,
        supported_languages=source.supported_languages or ["en"],
        document_count=metrics["document_count"],
        records_supported_count=metrics["records_supported_count"],
        health_status=metrics["health_status"],
    )

    return StandardResponse(
        data=detail,
        meta=MetaInfo(result_count=1),
    )
