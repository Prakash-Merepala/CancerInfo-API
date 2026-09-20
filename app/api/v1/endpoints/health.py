"""
Health and Status Endpoint
"""
import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.models import Cancer, Source
from app.schemas.search import HealthResponseOut

router = APIRouter(tags=["Health"])

START_TIME = time.time()


@router.get("/health", response_model=HealthResponseOut)
def get_health(db: Session = Depends(get_db)):
    """
    Returns API health status, database connectivity, uptime, and summary registry metrics.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1")).scalar()
    except Exception as e:
        db_status = f"error: {str(e)}"

    source_count = db.query(Source).count()
    cancer_count = db.query(Cancer).count()

    return HealthResponseOut(
        status="healthy" if db_status == "connected" else "degraded",
        api_name=settings.APP_NAME,
        api_version=settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime_seconds=round(time.time() - START_TIME, 2),
        environment=settings.ENVIRONMENT,
        source_registry_count=source_count,
        approved_cancers_count=cancer_count,
    )
