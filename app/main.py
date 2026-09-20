"""
CancerInfo API - Master Application Entry Point
"""
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.constants import MEDICAL_DISCLAIMER
from app.core.errors import APIError, api_error_handler, generic_exception_handler
from app.core.security import rate_limiter
from app.database.session import Base, SessionLocal, engine
from app.ingestion.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database tables
    Base.metadata.create_all(bind=engine)

    # 2. Seed initial taxonomy, source registry, and verified baseline records
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        f"{settings.APP_DESCRIPTION}\n\n"
        f"**Medical Disclaimer:** {MEDICAL_DISCLAIMER}"
    ),
    version=settings.APP_VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.middleware("http")
async def request_metrics_and_rate_limit(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Client IP identification
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"

    # Bypass rate limiter for internal docs, openapi, and health
    path = request.url.path
    if not (path.startswith("/docs") or path.startswith("/redoc") or path == "/openapi.json" or path == "/v1/health"):
        allowed, limit, remaining, reset = rate_limiter.check(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please wait before retrying.",
                        "details": {"retry_after_seconds": reset},
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset),
                },
            )
    else:
        limit, remaining, reset = settings.RATE_LIMIT_PER_MINUTE, settings.RATE_LIMIT_PER_MINUTE, 60

    response: Response = await call_next(request)

    # Response headers
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = f"{process_time:.2f}"
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    response.headers["X-Disclaimer"] = "Informational API only. Not medical advice."

    return response


# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root(request: Request):
    """
    Developer root endpoint.
    Returns developer portal documentation and quick links.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CancerInfo API - Developer Portal</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; background-color: #f9fafb; margin: 0; padding: 40px 20px; }}
    .container {{ max-width: 880px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb; }}
    h1 {{ color: #111827; font-size: 2rem; margin-top: 0; }}
    .badge {{ display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.875rem; margin-bottom: 16px; }}
    .btn {{ display: inline-block; background: #0284c7; color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 500; margin-right: 12px; }}
    .btn:hover {{ background: #0369a1; }}
    .btn-secondary {{ background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }}
    .btn-secondary:hover {{ background: #e5e7eb; }}
    pre {{ background: #1f2937; color: #f9fafb; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 0.9rem; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0; }}
    .disclaimer {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; color: #991b1b; font-size: 0.9rem; margin-top: 24px; border-radius: 0 6px 6px 0; }}
  </style>
</head>
<body>
  <div class="container">
    <span class="badge">CancerInfo API v1.0.0</span>
    <h1>CancerInfo API</h1>
    <p>A free, structured, global, source-transparent public REST API aggregating normalized cancer knowledge with fact-level provenance from authoritative health organizations (NCI, WHO, NHS, Cancer Australia).</p>
    
    <div style="margin: 24px 0;">
      <a class="btn" href="/docs">Interactive Swagger Docs (/docs)</a>
      <a class="btn btn-secondary" href="/redoc">ReDoc Documentation (/redoc)</a>
      <a class="btn btn-secondary" href="/v1/health">System Health (/v1/health)</a>
    </div>

    <h3>Quick Start: Call the API</h3>
    <pre><code># 1. Search for a cancer or symptom
curl http://localhost:3000/v1/search?q=breast+cancer

# 2. Get symptoms with fact-level provenance (US jurisdiction)
curl http://localhost:3000/v1/cancers/breast-cancer/symptoms?country=US

# 3. View screening guidelines with jurisdictional comparison
curl http://localhost:3000/v1/cancers/colorectal-cancer/screening

# 4. Inspect Source Registry & Transparency
curl http://localhost:3000/v1/sources
curl http://localhost:3000/v1/coverage</code></pre>

    <div class="card">
      <h4 style="margin-top:0;">Key Platform Features:</h4>
      <ul>
        <li><strong>Fact-Level Provenance:</strong> Every record is traced to official source URL, retrieved timestamp, verification date, and legal attribution.</li>
        <li><strong>Canonical Taxonomy & Aliases:</strong> Supports canonical names and aliases (e.g. <code>CRC</code>, <code>Bowel Cancer</code> &rarr; <code>colorectal-cancer</code>).</li>
        <li><strong>Jurisdictional Awareness:</strong> Transparent handling of country-specific guidelines (US, UK, AU, Global).</li>
        <li><strong>Strict Neutrality:</strong> No AI-generated clinical text. Verifiable public health information only.</li>
      </ul>
    </div>

    <div class="disclaimer">
      <strong>Medical Disclaimer:</strong> {MEDICAL_DISCLAIMER}
    </div>
  </div>
</body>
</html>
"""
        return HTMLResponse(content=html_content)

    return {
        "name": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/v1/health",
        "disclaimer": MEDICAL_DISCLAIMER,
    }
