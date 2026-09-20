"""
Countries and Jurisdictions Endpoint (Section 18)
"""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.constants import COUNTRIES
from app.database.session import get_db
from app.models import ContentRecord
from app.schemas.common import MetaInfo, StandardResponse

router = APIRouter(prefix="/countries", tags=["Jurisdictions"])


class CountryInfoOut(BaseModel):
    code: str
    name: str
    region: str
    default_language: str
    has_active_records: bool


@router.get("", response_model=StandardResponse[List[CountryInfoOut]])
def list_countries(db: Session = Depends(get_db)):
    """
    List countries and jurisdictions represented across normalized cancer knowledge records.
    """
    active_country_codes = set(
        r[0] for r in db.query(ContentRecord.country_code).filter(ContentRecord.active == True).distinct().all()
    )

    data = []
    for code, info in COUNTRIES.items():
        data.append(
            CountryInfoOut(
                code=code,
                name=info["name"],
                region=info["region"],
                default_language=info["default_language"],
                has_active_records=code in active_country_codes,
            )
        )

    return StandardResponse(
        data=data,
        meta=MetaInfo(result_count=len(data)),
    )
