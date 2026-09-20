"""
Cancer Repository
"""
from typing import List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from app.models import Cancer, CancerAlias, ContentRecord


class CancerRepository:
    def __init__(self, db: Session):
        self.db = db

    def resolve_cancer(self, identifier: str) -> Optional[Cancer]:
        """
        Resolves a cancer by slug, ID, canonical name, or alias (case-insensitive).
        Supports hyphenated or space-separated variations.
        """
        ident_lower = identifier.strip().lower()
        ident_spaces = ident_lower.replace("-", " ")
        ident_hyphens = ident_lower.replace(" ", "-")

        # 1. Check exact slug or ID
        cancer = self.db.query(Cancer).filter(
            or_(
                func.lower(Cancer.slug) == ident_lower,
                func.lower(Cancer.slug) == ident_hyphens,
                Cancer.id == identifier,
            )
        ).first()
        if cancer:
            return cancer

        # 2. Check canonical name
        cancer = self.db.query(Cancer).filter(
            or_(
                func.lower(Cancer.canonical_name) == ident_lower,
                func.lower(Cancer.canonical_name) == ident_spaces,
            )
        ).first()
        if cancer:
            return cancer

        # 3. Check aliases
        alias_match = self.db.query(CancerAlias).filter(
            or_(
                func.lower(CancerAlias.alias) == ident_lower,
                func.lower(CancerAlias.alias) == ident_spaces,
                func.lower(CancerAlias.alias) == ident_hyphens,
            )
        ).first()
        if alias_match:
            return self.db.query(Cancer).filter(Cancer.id == alias_match.cancer_id).first()

        return None

    def list_cancers(
        self,
        skip: int = 0,
        limit: int = 20,
        site: Optional[str] = None
    ) -> Tuple[List[Cancer], int]:
        query = self.db.query(Cancer).options(joinedload(Cancer.aliases))
        if site:
            query = query.filter(func.lower(Cancer.anatomical_site) == site.lower())

        total = query.count()
        cancers = query.order_by(Cancer.canonical_name.asc()).offset(skip).limit(limit).all()
        return cancers, total

    def get_cancer_sections(self, cancer_id: str) -> List[dict]:
        """
        Returns list of categories that have active content records for this cancer,
        along with record counts and countries represented.
        """
        results = (
            self.db.query(
                ContentRecord.category,
                func.count(ContentRecord.id).label("count"),
            )
            .filter(
                ContentRecord.canonical_cancer_id == cancer_id,
                ContentRecord.active == True
            )
            .group_by(ContentRecord.category)
            .all()
        )

        sections = []
        for cat, count in results:
            countries = [
                r[0] for r in self.db.query(ContentRecord.country_code)
                .filter(
                    ContentRecord.canonical_cancer_id == cancer_id,
                    ContentRecord.category == cat,
                    ContentRecord.active == True
                )
                .distinct().all()
            ]
            sections.append({
                "category": cat,
                "count": count,
                "countries": countries
            })
        return sections
