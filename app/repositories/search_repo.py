"""
Search Repository
"""
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from app.core.constants import CANONICAL_CATEGORIES, CATEGORY_ALIASES
from app.models import Cancer, CancerAlias, ContentRecord, ContentSource, Source


class SearchRepository:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        query_str: str,
        category: Optional[str] = None,
        country: Optional[str] = None,
        source_id: Optional[str] = None,
        audience: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        query_clean = query_str.strip()
        tokens = [t.lower() for t in query_clean.split() if t]
        results: List[Dict[str, Any]] = []

        # 1. Check if any token matches a canonical category
        detected_category = category
        if not detected_category:
            for t in tokens:
                if t in CANONICAL_CATEGORIES:
                    detected_category = t
                    break
                elif t in CATEGORY_ALIASES:
                    detected_category = CATEGORY_ALIASES[t]
                    break

        # 2. Direct Cancer entity matching (canonical name & aliases)
        # e.g. "bowel cancer", "CRC", "breast", "pancreatic"
        cancer_query = self.db.query(Cancer).options(joinedload(Cancer.aliases))
        search_filter = or_(
            func.lower(Cancer.canonical_name).contains(query_clean.lower()),
            func.lower(Cancer.slug).contains(query_clean.lower()),
        )
        for t in tokens:
            search_filter = or_(
                search_filter,
                func.lower(Cancer.canonical_name).contains(t),
            )

        matched_cancers = cancer_query.filter(search_filter).all()

        # Also search aliases table
        alias_matches = (
            self.db.query(CancerAlias)
            .filter(
                or_(
                    func.lower(CancerAlias.alias).contains(query_clean.lower()),
                    *[func.lower(CancerAlias.alias).contains(t) for t in tokens]
                )
            )
            .all()
        )
        for am in alias_matches:
            c = self.db.query(Cancer).filter(Cancer.id == am.cancer_id).first()
            if c and c not in matched_cancers:
                matched_cancers.append(c)

        for c in matched_cancers:
            # Calculate match score
            score = 1.0
            if query_clean.lower() == c.canonical_name.lower() or query_clean.lower() == c.slug.lower():
                score = 3.0
            elif any(query_clean.lower() == a.alias.lower() for a in c.aliases):
                score = 2.5
            elif c.canonical_name.lower().startswith(query_clean.lower()):
                score = 2.0

            results.append({
                "match_type": "cancer",
                "score": score,
                "cancer": c,
                "category": None,
                "snippet": c.description,
                "record": None,
                "matched_terms": [t for t in tokens if t in c.canonical_name.lower() or any(t in a.alias.lower() for a in c.aliases)],
            })

        # 3. Content record search
        content_query = (
            self.db.query(ContentRecord)
            .options(
                joinedload(ContentRecord.cancer),
                joinedload(ContentRecord.sources).joinedload(ContentSource.source)
            )
            .filter(ContentRecord.active == True)
        )

        if detected_category:
            content_query = content_query.filter(ContentRecord.category == detected_category)

        if country:
            country_clean = country.strip().upper()
            content_query = content_query.filter(
                (ContentRecord.country_code == country_clean) | (ContentRecord.country_code == "GLOBAL")
            )

        if audience:
            content_query = content_query.filter(ContentRecord.audience == audience.strip().lower())

        if source_id:
            content_query = content_query.join(ContentRecord.sources).filter(ContentSource.source_id == source_id)

        # Content keyword filter
        for t in tokens:
            # Avoid filtering content strictly by words that were already used as category tokens
            if t != detected_category and t not in CATEGORY_ALIASES:
                content_query = content_query.filter(func.lower(ContentRecord.content).contains(t))

        content_matches = content_query.limit(limit).all()

        for rec in content_matches:
            # Create snippet
            snippet = rec.content
            if len(snippet) > 280:
                snippet = snippet[:280].rsplit(" ", 1)[0] + "..."

            results.append({
                "match_type": "content_record",
                "score": 1.5,
                "cancer": rec.cancer,
                "category": rec.category,
                "snippet": snippet,
                "record": rec,
                "matched_terms": [t for t in tokens if t in rec.content.lower()],
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
