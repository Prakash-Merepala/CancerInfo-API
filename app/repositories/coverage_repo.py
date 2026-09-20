"""
Coverage Repository (Section 39)
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Cancer, ContentRecord, ContentSource, Source, SourceDocument


class CoverageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_coverage(self, cancer_slug: Optional[str] = None) -> Dict[str, Any]:
        cancers_query = self.db.query(Cancer)
        if cancer_slug:
            cancers_query = cancers_query.filter(Cancer.slug == cancer_slug.strip().lower())

        cancers = cancers_query.all()

        total_sources = self.db.query(func.count(Source.id)).filter(Source.active == True).scalar() or 0
        total_documents = self.db.query(func.count(SourceDocument.id)).scalar() or 0

        # Trust tiers breakdown
        tier_counts = (
            self.db.query(Source.trust_tier, func.count(Source.id))
            .filter(Source.active == True)
            .group_by(Source.trust_tier)
            .all()
        )
        sources_by_tier = {tier: count for tier, count in tier_counts}

        # Global countries represented
        countries = [
            r[0] for r in self.db.query(ContentRecord.country_code).filter(ContentRecord.active == True).distinct().all()
        ]

        # Available categories
        categories = [
            r[0] for r in self.db.query(ContentRecord.category).filter(ContentRecord.active == True).distinct().all()
        ]

        cancers_coverage_list = []
        total_content_records = 0

        for cancer in cancers:
            records = (
                self.db.query(ContentRecord)
                .filter(ContentRecord.canonical_cancer_id == cancer.id, ContentRecord.active == True)
                .all()
            )
            total_content_records += len(records)

            cancer_categories = list(set(r.category for r in records))
            cancer_countries = list(set(r.country_code for r in records))

            # Supporting sources for this cancer
            source_names = [
                s.source_name for s in (
                    self.db.query(Source)
                    .join(ContentSource, ContentSource.source_id == Source.id)
                    .join(ContentRecord, ContentRecord.id == ContentSource.content_record_id)
                    .filter(ContentRecord.canonical_cancer_id == cancer.id)
                    .distinct()
                    .all()
                )
            ]

            last_verified = (
                self.db.query(func.max(ContentSource.last_verified_at))
                .join(ContentRecord, ContentRecord.id == ContentSource.content_record_id)
                .filter(ContentRecord.canonical_cancer_id == cancer.id)
                .scalar()
            )

            cancers_coverage_list.append({
                "slug": cancer.slug,
                "canonical_name": cancer.canonical_name,
                "total_records": len(records),
                "categories_covered": cancer_categories,
                "countries": cancer_countries,
                "supporting_sources": source_names,
                "last_verified_at": last_verified.isoformat() + "Z" if last_verified else None,
            })

        return {
            "total_cancers": len(cancers),
            "total_sources": total_sources,
            "total_content_records": total_content_records,
            "total_source_documents": total_documents,
            "countries_represented": countries,
            "categories_available": categories,
            "sources_by_trust_tier": sources_by_tier,
            "cancers": cancers_coverage_list,
        }
