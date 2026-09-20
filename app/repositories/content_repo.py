"""
Content Record and Provenance Repository
"""
from typing import List, Optional, Tuple
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from app.models import ContentRecord, ContentSource, ContentVersion, Source


class ContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_records(
        self,
        cancer_id: str,
        category: str,
        country: Optional[str] = None,
        audience: Optional[str] = None,
        source_id: Optional[str] = None,
        language: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ContentRecord], int]:
        query = (
            self.db.query(ContentRecord)
            .filter(
                ContentRecord.canonical_cancer_id == cancer_id,
                ContentRecord.category == category,
                ContentRecord.active == True,
            )
            .options(
                joinedload(ContentRecord.sources).joinedload(ContentSource.source)
            )
        )

        if country:
            country_clean = country.strip().upper()
            # If user filters by US, also return GLOBAL or US
            query = query.filter(
                (ContentRecord.country_code == country_clean) |
                (ContentRecord.country_code == "GLOBAL")
            )

        if audience:
            query = query.filter(ContentRecord.audience == audience.strip().lower())

        if language:
            query = query.filter(ContentRecord.language == language.strip().lower())

        if source_id:
            query = query.join(ContentRecord.sources).filter(ContentSource.source_id == source_id)

        total = query.count()
        records = (
            query.order_by(
                desc(ContentRecord.jurisdiction_scope == "GLOBAL"),  # Country-specific first if present
                ContentRecord.created_at.asc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return records, total

    def get_sources_for_cancer(self, cancer_id: str) -> List[Source]:
        """Returns all distinct sources that have provided content for this cancer"""
        return (
            self.db.query(Source)
            .join(ContentSource, ContentSource.source_id == Source.id)
            .join(ContentRecord, ContentRecord.id == ContentSource.content_record_id)
            .filter(
                ContentRecord.canonical_cancer_id == cancer_id,
                ContentRecord.active == True
            )
            .distinct()
            .all()
        )

    def get_content_versions(self, cancer_id: str, limit: int = 50) -> List[ContentVersion]:
        """Returns version audit log for content of this cancer"""
        return (
            self.db.query(ContentVersion)
            .join(ContentRecord, ContentRecord.id == ContentVersion.content_record_id)
            .filter(ContentRecord.canonical_cancer_id == cancer_id)
            .order_by(ContentVersion.created_at.desc())
            .limit(limit)
            .all()
        )
