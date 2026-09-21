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

## Development Setup & Package Management

This repository standardizes on **npm** as its Node.js package manager, using a committed root `package-lock.json` for deterministic, reproducible installations in local development, Docker, and GitHub Actions CI.

```bash
# 1. Clone repository
git clone https://github.com/Prakash-Merepala/CancerInfo-API.git
cd CancerInfo-API

# 2. Set up Python virtual environment & dependencies
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt

# 3. Install Node.js dependencies (use npm ci for clean reproducible install)
npm ci

# 4. Run tests & validation suite
python -m pytest tests/ -v
npm run lint
npm run build

# 5. Start dev server
npm run dev
```

### Pre-PR Validation Commands

Before opening a pull request, ensure all CI validation gates pass locally:

1. `npm ci` — Clean installation succeeds without lockfile drift.
2. `npm run lint` — TypeScript static type checking (`tsc --noEmit`).
3. `npm run build` — Frontend Vite production build (`dist/index.html`) and backend Node bundle (`dist/server.cjs`).
4. `python -m pip install -r requirements.txt` — Python dependency installation.
5. `python -m pytest tests/ -v` — Full backend test suite (all 26 tests passing).

---

## Code Quality Standards

- All new endpoints must include corresponding `pytest` tests under `tests/`.
- Ensure responses pass type validation in Pydantic schemas under `app/schemas/`.
- Every added medical fact **must** include its primary source URL and organization attribution.
- Respect our [Code of Conduct](CODE_OF_CONDUCT.md).
