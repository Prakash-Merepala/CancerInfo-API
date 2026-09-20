"""
Knowledge Coverage Endpoint (Section 39)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.coverage_repo import CoverageRepository
from app.schemas.common import MetaInfo, StandardResponse
from app.schemas.search import CancerCoverageItem, CoverageResponseOut

router = APIRouter(prefix="/coverage", tags=["Coverage & Transparency"])


@router.get("", response_model=StandardResponse[CoverageResponseOut])
def get_coverage(
    cancer: Optional[str] = Query(None, description="Optional cancer slug to get specific coverage, e.g. 'breast-cancer'"),
    db: Session = Depends(get_db),
):
    """
    Returns global or cancer-specific coverage transparency information.
    Enables developers to inspect what CancerInfo API actually knows, sources represented,
    available categories, and last verification dates.
    """
    repo = CoverageRepository(db)
    raw = repo.get_coverage(cancer_slug=cancer)

    cancers_list = [
        CancerCoverageItem(
            slug=c["slug"],
            canonical_name=c["canonical_name"],
            total_records=c["total_records"],
            categories_covered=c["categories_covered"],
            countries=c["countries"],
            supporting_sources=c["supporting_sources"],
            last_verified_at=c["last_verified_at"],
        )
        for c in raw["cancers"]
    ]

    payload = CoverageResponseOut(
        total_cancers=raw["total_cancers"],
        total_sources=raw["total_sources"],
        total_content_records=raw["total_content_records"],
        total_source_documents=raw["total_source_documents"],
        countries_represented=raw["countries_represented"],
        categories_available=raw["categories_available"],
        sources_by_trust_tier=raw["sources_by_trust_tier"],
        cancers=cancers_list,
    )

    return StandardResponse(
        data=payload,
        meta=MetaInfo(result_count=len(cancers_list)),
    )
