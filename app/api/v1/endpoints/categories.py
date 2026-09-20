"""
Canonical Categories Catalog Endpoint (Section 11)
"""
from typing import Dict, List
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.constants import CANONICAL_CATEGORIES, CATEGORY_ALIASES
from app.schemas.common import MetaInfo, StandardResponse

router = APIRouter(prefix="/categories", tags=["Taxonomy & Categories"])


class CanonicalCategoryOut(BaseModel):
    category: str
    name: str
    description: str
    recognized_aliases: List[str]


@router.get("", response_model=StandardResponse[List[CanonicalCategoryOut]])
def list_canonical_categories():
    """
    List all 37 canonical knowledge categories supported by CancerInfo API.
    """
    data = []
    # Invert alias map for quick lookup
    alias_map: Dict[str, List[str]] = {}
    for alias, cat in CATEGORY_ALIASES.items():
        alias_map.setdefault(cat, []).append(alias)

    for cat_slug, info in CANONICAL_CATEGORIES.items():
        data.append(
            CanonicalCategoryOut(
                category=cat_slug,
                name=info["name"],
                description=info["description"],
                recognized_aliases=alias_map.get(cat_slug, []),
            )
        )

    return StandardResponse(
        data=data,
        meta=MetaInfo(result_count=len(data)),
    )
