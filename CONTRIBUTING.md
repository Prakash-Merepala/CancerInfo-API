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

## Development Setup

```bash
# 1. Clone repository
git clone https://github.com/cancerinfo-api/cancerinfo-api.git
cd cancerinfo-api

# 2. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install Node.js dependencies
npm install

# 4. Run tests
python3 -m pytest tests/

# 5. Start dev server
npm run dev
```

---

## Code Quality Standards

- All new endpoints must include corresponding `pytest` tests under `tests/`.
- Ensure responses pass type validation in Pydantic schemas under `app/schemas/`.
- Every added medical fact **must** include its primary source URL and organization attribution.
- Respect our [Code of Conduct](CODE_OF_CONDUCT.md).
