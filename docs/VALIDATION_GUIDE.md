# CancerInfo API Validation & Quality Assurance Guide

This guide describes how to validate the CancerInfo API codebase, test endpoints, check OpenAPI schemas, and ensure compliance prior to publishing.

---

## 1. Automated Test Suite (pytest)

The codebase includes a comprehensive 26-test suite testing every endpoint, normalizer, and adapter.

### Run all tests:
```bash
python3 -m pytest tests/ -v
```

### Coverage by test module:
- `tests/test_health.py`: Database connectivity, uptime counter, and registry count verification.
- `tests/test_cancers.py`: Canonical cancer retrieval, alias resolution, pagination, section availability.
- `tests/test_search.py`: Term matching, multi-word matching, clinical abbreviation resolution (`CRC` -> `colorectal-cancer`).
- `tests/test_sources.py`: Trust tier verification, license compliance, URL validation.
- `tests/test_taxonomy_and_normalization.py`: 37-category schema validation, HTML stripping, bullet point extraction.
- `tests/test_admin_and_pipeline.py`: Ingestion pipelines and seed scripts.

---

## 2. API Endpoint Health & Smoke Testing

To test the live running server:

```bash
# 1. Health & Database Check
curl -s http://localhost:3000/v1/health | jq .

# 2. Breast Cancer Symptoms (US Provenance)
curl -s "http://localhost:3000/v1/cancers/breast-cancer/symptoms?country=US" | jq .

# 3. Colorectal Cancer Screening (UK NHS Provenance)
curl -s "http://localhost:3000/v1/cancers/colorectal-cancer/screening?country=GB" | jq .

# 4. Search Acronym Resolution
curl -s "http://localhost:3000/v1/search?q=CRC" | jq .

# 5. Global Coverage Transparency
curl -s "http://localhost:3000/v1/coverage" | jq .
```

---

## 3. Response Headers Validation

Confirm that required auditing and safety headers are present on every HTTP response:

```bash
curl -s -I "http://localhost:3000/v1/cancers"
```

Verify these headers:
- `x-request-id`: Unique UUID4 generated per request.
- `x-response-time-ms`: Server execution latency in milliseconds.
- `x-ratelimit-limit` & `x-ratelimit-remaining`: Sliding window rate limit status.
- `x-disclaimer`: Medical safety disclaimer (`Informational API only. Not medical advice.`).

---

## 4. OpenAPI Specification Validation

Validate the OpenAPI schema using standard tools:

```bash
# Verify openapi.json is served with valid JSON
curl -s http://localhost:3000/openapi.json | jq .info.title

# Optional: Validate with openapi-generator or spectral
npx @stoplight/spectral-cli lint rapidapi/rapidapi-openapi.json
```
