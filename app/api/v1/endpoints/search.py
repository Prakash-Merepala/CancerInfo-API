"""
Search Endpoint (Section 22)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.search_repo import SearchRepository
from app.schemas.cancer import CancerSummaryOut
from app.schemas.common import MetaInfo, StandardResponse
from app.schemas.content import ContentRecordOut, JurisdictionOut, ProvenanceSourceOut
from app.schemas.search import SearchResultItem, SearchResultsOut

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=StandardResponse[SearchResultsOut])
def search(
    q: str = Query(..., min_length=1, description="Search query string, e.g. 'bowel cancer', 'CRC', 'pancreatic symptoms'"),
    category: Optional[str] = Query(None, description="Optional canonical category filter"),
    country: Optional[str] = Query(None, description="Country filter, e.g. 'US', 'GB', 'AU', 'GLOBAL'"),
    source: Optional[str] = Query(None, description="Source ID filter, e.g. 'nci-us', 'who-global'"),
    audience: Optional[str] = Query(None, description="Audience filter, e.g. 'patient'"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Search across canonical cancer names, aliases, and fact-level content records.
    Understands canonical names, abbreviations, and common names.
    """
    repo = SearchRepository(db)
    raw_results = repo.search(
        query_str=q,
        category=category,
        country=country,
        source_id=source,
        audience=audience,
        limit=limit,
    )

    items = []
    for r in raw_results:
        cancer_obj = r["cancer"]
        cancer_out = CancerSummaryOut(
            id=cancer_obj.id,
            slug=cancer_obj.slug,
            canonical_name=cancer_obj.canonical_name,
            anatomical_site=cancer_obj.anatomical_site,
            aliases=[a.alias for a in cancer_obj.aliases],
        )

        record_out = None
        if r.get("record"):
            rec = r["record"]
            sources_out = [
                ProvenanceSourceOut(
                    source_id=cs.source.id,
                    organization=cs.source.organization_name,
                    source_name=cs.source.source_name,
                    url=cs.source_url,
                    trust_tier=cs.source.trust_tier,
                    source_updated_at=cs.source_updated_at.isoformat() + "Z" if cs.source_updated_at else None,
                    retrieved_at=cs.retrieved_at.isoformat() + "Z",
                    last_verified_at=cs.last_verified_at.isoformat() + "Z",
                    license_status=cs.source.license_status,
                    attribution_text=cs.attribution_text or cs.source.attribution_text,
                    quote_snippet=cs.quote_snippet,
                )
                for cs in rec.sources
            ]
            record_out = ContentRecordOut(
                id=rec.id,
                category=rec.category,
                subcategory=rec.subcategory,
                content=rec.content,
                content_type=rec.content_type,
                jurisdiction=JurisdictionOut(
                    scope=rec.jurisdiction_scope,
                    country=rec.country_code,
                    region=rec.region_code,
                ),
                language=rec.language,
                audience=rec.audience,
                disagreement_status=rec.disagreement_status,
                disagreement_notes=rec.disagreement_notes,
                version_number=rec.version_number,
                updated_at=rec.updated_at.isoformat() + "Z",
                sources=sources_out,
            )

        items.append(
            SearchResultItem(
                match_type=r["match_type"],
                score=r["score"],
                cancer=cancer_out,
                category=r.get("category"),
                snippet=r.get("snippet"),
                record=record_out,
                matched_terms=r.get("matched_terms", []),
            )
        )

    filters = {k: v for k, v in {"category": category, "country": country, "source": source, "audience": audience}.items() if v}
    payload = SearchResultsOut(
        query=q,
        filters_applied=filters,
        results=items,
    )

    return StandardResponse(
        data=payload,
        meta=MetaInfo(result_count=len(items)),
    )
