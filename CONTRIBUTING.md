# Contributing to CancerInfo API

Thank you for your interest in contributing to **CancerInfo API**! Every pull request, clinical source citation check, and code contribution helps make cancer information more transparent, reliable, and accessible for everyone in the world.

---

## How You Can Contribute

1. **Suggest or Add New Authoritative Health Sources**:
   - We strictly aggregate from **Tier 1 (Government & Multilateral Public Health Bodies)** and **Tier 2 (Premier Accredited Cancer Centers & Societies)**.
   - We do *not* ingest private sponsored content, unverified forums, or commercial blogs.
2. **Expand Canonical Cancer Mappings & Aliases**:
   - Add international colloquial names, abbreviations (e.g. `NSCLC`, `ALL`, `CML`), or ICD-O-3 codes in `app/pipeline/seed_data.py`.
3. **Enhance Taxonomy & Classification**:
   - Help refine extraction rules across our 37 standardized categories in `app/core/taxonomy.py`.
4. **Develop Client SDKs & Community Templates**:
   - Build client libraries in Python, JavaScript/TypeScript, Go, Swift, Rust, or Kotlin.

---

## Development Setup & Workflow

This repository standardizes on **Python 3.11+** and **FastAPI** for high performance, automatic OpenAPI documentation, and strict schema validation.

```bash
# 1. Clone repository
git clone https://github.com/Prakash-Merepala/CancerInfo-API.git
cd CancerInfo-API

# 2. Set up Python virtual environment & dependencies
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Run the automated test suite
python -m pytest tests/ -v

# 4. Start local development server with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Pre-PR Validation Commands

Before opening a pull request, ensure all CI validation gates pass locally:

1. `python -m pip install -r requirements.txt` — Python dependencies install cleanly.
2. `python -m pytest tests/ -v` — All 28 tests pass green.
3. `python -c "from app.main import app; app.openapi()"` — OpenAPI 3.1 schema generates without error.
4. `curl -f http://localhost:3000/health` — Local server health check returns 200 OK.


---

## Code Quality Standards

- All new endpoints must include corresponding `pytest` tests under `tests/`.
- Ensure responses pass type validation in Pydantic schemas under `app/schemas/`.
- Every added medical fact **must** include its primary source URL and organization attribution.
- Respect our [Code of Conduct](CODE_OF_CONDUCT.md).
