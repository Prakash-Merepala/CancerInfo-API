<div align="center">

# 🎗️ CancerInfo API
### *A Free, Global, Source-Transparent Cancer Knowledge Platform with Fact-Level Provenance*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white)](/rapidapi/rapidapi-openapi.json)
[![RapidAPI](https://img.shields.io/badge/RapidAPI-100%25_Free-0052CC?style=for-the-badge&logo=rapidapi&logoColor=white)](https://rapidapi.com/hub)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Tests: 28/28 Passing](https://img.shields.io/badge/Tests-28%2F28_Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](#automated-testing)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](docker-compose.yml)

<p align="center">
  <b>Built with code. Powered by love. Serving humanity free of charge.</b><br>
  <i>"Because when someone you love is fighting cancer, finding trustworthy medical knowledge shouldn't be another battle."</i>
</p>

[Quickstart](#-quickstart-in-30-seconds) • [Why This Exists](#-why-this-exists-the-story-behind-the-code) • [API Reference](#-api-endpoints) • [RapidAPI Guide](rapidapi/RAPIDAPI_LISTING_GUIDE.md) • [Architecture](#-architecture) • [App Ideas](docs/APP_IDEAS_GUIDE.md)

---

</div>

## 💜 Why This Exists: The Story Behind the Code

> *"Code cannot cure cancer. But code can destroy the fog of misinformation, dismantle knowledge paywalls, and place verified, life-saving clinical facts directly into the hands of every developer, doctor, caregiver, and child fighting for their family."*

This project was not born out of a hackathon prompt or a venture pitch. 

**It was born in hospital waiting rooms, holding my parents' hands.**

Within a span that felt like an eternity, **both my mother and my father were diagnosed with cancer.** 

If you have ever loved someone walking through that valley, you know the suffocating weight that follows. The diagnosis hits like an earthquake. Then comes the second trauma: navigating the labyrinth of cancer information. 

Late at night, while my parents slept between chemotherapy cycles, I found myself desperately searching online:
- Conflicting forum posts and algorithmic clickbait.
- Contradictory screening ages between different countries.
- Paywalled medical research papers written in opaque jargon.
- No direct way to know: *Where did this fact come from? Is this guideline current? Does this apply in our country?*

I am an engineer. In software, we demand immutability, cryptographic provenance, and single sources of truth. Yet in the fight for our parents' lives, the internet offered guesswork and uncertainty.

I made a silent promise: **I would build the public API I desperately needed on those dark nights.**

**CancerInfo API** is that promise kept:
- **100% Free Forever**: No paywalls, no monetization gates, no commercial exploitation.
- **Fact-Level Provenance**: Every symptom, guideline, and treatment record traces directly back to world-leading public health authorities—the **National Cancer Institute (NCI)**, the **World Health Organization (WHO)**, the **National Health Service (NHS UK)**, and **Cancer Australia**.
- **Structured for Builders**: Clean, normalized JSON with taxonomy resolution, multi-jurisdiction comparisons, and instant search, so developers around the world can build clinical assistants, screening calculators, and AI copilots that **never hallucinate.**

*To my mom and dad: This code is dedicated to your courage, your grace, and every family still fighting.* 🕊️

---

## ⚡ Quickstart in 30 Seconds

### 1. Test via cURL
```bash
# Health check
curl -s http://localhost:3000/v1/health

# Breast cancer symptoms with fact-level US NCI provenance
curl -s "http://localhost:3000/v1/cancers/breast-cancer/symptoms?country=US" | jq .

# Colorectal cancer screening guidelines from the UK National Health Service
curl -s "http://localhost:3000/v1/cancers/colorectal-cancer/screening?country=GB" | jq .

# Search acronyms (CRC -> Colorectal Cancer)
curl -s "http://localhost:3000/v1/search?q=CRC" | jq .
```

### 2. Python
```python
import requests

# Fetch verified symptoms with direct citations
res = requests.get(
    "http://localhost:3000/v1/cancers/breast-cancer/symptoms",
    params={"country": "US"}
).json()

record = res["data"]["records"][0]
print(f"Content: {record['content']}")
print(f"Verified Source: {record['sources'][0]['organization']}")
print(f"Source URL: {record['sources'][0]['url']}")
```

### 3. JavaScript / TypeScript
```typescript
const res = await fetch("http://localhost:3000/v1/cancers/colorectal-cancer/screening?country=GB");
const { data } = await res.json();
console.log(`Guidelines from ${data.records[0].sources[0].organization}:`);
console.log(data.records[0].content);
```

### 4. 1-Command Local Launch via Docker Compose
```bash
git clone https://github.com/cancerinfo-api/cancerinfo-api.git
cd cancerinfo-api
docker compose up -d
```
Visit `http://localhost:3000/docs` to open the interactive Swagger UI.

---

## 🔬 Core Architectural Principle: Fact-Level Provenance

```
                 UNVERIFIED INTERNET                        CANCERINFO API
             ┌─────────────────────────┐               ┌───────────────────────┐
             │ Unverified Health Blogs │               │  National Cancer Inst │
             │ Anonymous Forum Advice  │────► ❌       │  World Health Org     │
             │ AI Generated Guesswork  │               │  NHS UK & Cancer Aus  │
             └─────────────────────────┘               └───────────┬───────────┘
                                                                   │
                                                   Normalized Parsing & Validation
                                                                   │
                                                                   ▼
                                                       ┌───────────────────────┐
                                                       │ CANONICAL DATA RECORD │
                                                       ├───────────────────────┤
                                                       │ • Clean Markdown Fact │
                                                       │ • Direct Source URL   │
                                                       │ • Organization Name   │
                                                       │ • Trust Tier (Tier 1) │
                                                       │ • Legal Attribution   │
                                                       │ • Verification Date   │
                                                       │ • Country / Scope     │
                                                       └───────────────────────┘
```

Every record returned by CancerInfo API adheres to the **Zero Guesswork Guarantee**:
```json
{
  "category": "screening",
  "content": "The NHS bowel cancer screening program checks if you could have bowel cancer. Everyone aged 50 to 74 is automatically sent a home testing kit (FIT kit) every 2 years.",
  "jurisdiction": {
    "scope": "COUNTRY",
    "country": "GB"
  },
  "sources": [
    {
      "source_id": "nhs-uk",
      "organization": "National Health Service (UK)",
      "trust_tier": "Tier 1 - Primary Authoritative",
      "url": "https://www.nhs.uk/conditions/bowel-cancer/screening/",
      "attribution_text": "Contains public sector information licensed under the Open Government Licence v3.0.",
      "retrieved_at": "2026-09-12T06:23:36Z",
      "last_verified_at": "2026-09-12T06:23:36Z"
    }
  ]
}
```

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/health` | System health, database connectivity, uptime, and loaded registry metrics |
| `GET` | `/v1/cancers` | List all canonical cancers with pagination and anatomical site filter |
| `GET` | `/v1/cancers/{cancer}` | Detail view: canonical name, ICD codes, aliases, and available sections |
| `GET` | `/v1/cancers/{cancer}/sections` | Summary of populated categories, record counts, and jurisdictions |
| `GET` | `/v1/cancers/{cancer}/sources` | Active authoritative sources backing this cancer |
| `GET` | `/v1/cancers/{cancer}/versions` | Historical audit trail and version changelog for clinical records |
| `GET` | `/v1/cancers/{cancer}/{category}` | **Core Knowledge**: Normalized facts with citation URLs and country filters |
| `GET` | `/v1/search` | Multi-factor search resolving abbreviations (`CRC`), aliases, and symptoms |
| `GET` | `/v1/sources` | Complete registry of approved sources, trust tiers, and open licenses |
| `GET` | `/v1/sources/{id}` | Detailed profile for an individual health authority |
| `GET` | `/v1/categories` | Catalog of all 37 standardized cancer knowledge categories |
| `GET` | `/v1/countries` | Global jurisdictions represented across the knowledge base |
| `GET` | `/v1/coverage` | Full transparency coverage metrics |
| `GET` | `/docs` | Interactive Swagger UI console |
| `GET` | `/redoc` | High-readability ReDoc API documentation |
| `GET` | `/openapi.json` | OpenAPI 3.1 schema specification |

---

## 🌐 Publish & Deploy Free to the Community

CancerInfo API is 100% ready for publishing on developer portals and marketplaces:

- **[RapidAPI Publishing Guide](rapidapi/RAPIDAPI_LISTING_GUIDE.md)**: Ready-to-import `rapidapi/rapidapi-openapi.json` and `rapidapi/postman_collection.json` with instructions to list under the 100% Free Tier.
- **[Free Cloud Hosting Guide](docs/FREE_HOSTING_DEPLOYMENT.md)**: Deploy for $0/month on Render, Google Cloud Run (2M free calls/month), Railway, or Fly.io.
- **[Validation & Testing Guide](docs/VALIDATION_GUIDE.md)**: Quality assurance runbook for CI/CD and production verification.
- **[App Ideas & Ecosystem Recipes](docs/APP_IDEAS_GUIDE.md)**: Blueprints for building RAG Chatbots, Screening Calculators, and Symptom Navigators.
- **[GitHub Open API Ecosystem Stats](docs/GITHUB_ECOSYSTEM_STATS.md)**: Industry adoption benchmarks, developer demographics, and usage patterns.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite (dev) / PostgreSQL (prod), Uvicorn.
- **Developer Documentation & Portal**: Built directly into FastAPI: Interactive Swagger UI (`/docs`), ReDoc (`/redoc`), OpenAPI 3.1 spec (`/openapi.json`), and Developer Landing (`/`).
- **Auditing & Compliance**: Automatic `X-Request-ID` UUID tracking, millisecond `X-Response-Time-MS` measurement, in-memory sliding-window rate limiting (`X-RateLimit-*`), and mandatory clinical disclaimer headers (`X-Medical-Disclaimer`, `X-Disclaimer`).
- **Automated Testing**: 28 pytest unit and integration tests passing with 100% green coverage.
- **Companion UI**: The standalone React/Vite Developer Portal is archived at git tag `archive/cancerinfo-explorer-ui` and packaged in `cancerinfo-explorer-ui/` ready for separate deployment.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CANCERINFO FASTAPI RUNTIME                      │
├────────────────────────────────────────────────────────────────────────┤
│  Incoming Client (cURL / Python / RapidAPI / Browser / Mobile App)     │
│                                  │                                     │
│                     [FastAPI ASGI Middleware]                          │
│         • Request ID Tracking    • Rate Limiting (120 req/min)         │
│         • Millisecond Timing     • Safety & Disclaimer Headers         │
│         • Root Health Probes     • Automatic CORS Handling             │
│                                  │                                     │
│                    ┌─────────────┴─────────────┐                       │
│                    ▼                           ▼                       │
│         [Core /v1 REST API]            [Documentation Engine]          │
│         • /v1/cancers, /symptoms       • Interactive Swagger (/docs)   │
│         • /v1/search (Acronyms & text) • ReDoc Documentation (/redoc)  │
│         • /v1/sources & /v1/coverage   • OpenAPI 3.1 Schema Spec       │
│         • Jurisdictional Filtering     • Developer Portal (/)          │
│                    │                                                   │
│                    ▼                                                   │
│         [Relational SQLite / Neon PostgreSQL]                          │
│         • Canonical Cancers & Aliases                                  │
│         • Source Registry & Licensing Tiers                            │
│         • Provenance Records & Version History                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Automated Testing

Run the comprehensive 28-test suite:
```bash
python3 -m pytest tests/ -v
```

All 28 tests cover:
- Health and database connectivity (`/v1/health`, `/health`, `/api/health`)
- Canonical cancer slug resolution and pagination
- Clinical abbreviation matching (`CRC` -> `colorectal-cancer`)
- Fact-level provenance schema validation
- Jurisdictional filtering (`country=US`, `country=GB`)
- Multi-source citation tracking
- 37-category taxonomy compliance
- Audit tracking headers and rate-limiting enforcement

---

## ⚠️ Legal & Clinical Disclaimer

> **IMPORTANT:** CancerInfo API provides public informational data aggregated from authoritative health organizations for developers, researchers, caregivers, and public-health products. **It does not provide medical diagnosis, personal treatment recommendations, individualized drug selection or dosage, or replace licensed medical professionals.** Always consult a qualified oncologist or physician for clinical decisions.

---

## 🤝 Contributing

We welcome pull requests from developers, bioinformaticians, oncologists, and patient advocates worldwide!
Please read our **[Contributing Guidelines](CONTRIBUTING.md)** and **[Code of Conduct](CODE_OF_CONDUCT.md)** to get started.

---

<div align="center">

### Dedicated with infinite love to my parents, and to every cancer warrior across the world.

*If this project touches your heart or helps your work, please star the repository on GitHub to help other developers find it.* ⭐

**CancerInfo API — Free knowledge for a cancer-free future.**

</div>
