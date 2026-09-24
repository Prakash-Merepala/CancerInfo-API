# RapidAPI Publisher Guide for CancerInfo API

## Current guidance, September 22, 2026

This guide applies to Python refactor `1199f735e3d77b5c1ada35e6451c7a5b4e36d063`. Current guidance below supersedes the prior draft retained at the end.

### RapidAPI rollout and publication timing

Owner target: public launch October 4, 2026. To preserve at least one full week, complete the accepted candidate and submit through RapidAPI by September 27. September 28 remains the owner’s adjustable readiness fallback, but is six days before launch. The buffer is a project planning requirement, not a verified platform approval SLA.

Prepare account ownership, listing metadata and a private draft now. Import only the reviewed public contract after fixing the 8-path static file; runtime generation includes admin routes, which must be excluded from the public export. Use the actual tested HTTPS origin, not the example hostname embedded in the current file. Confirm quotas, origin/gateway controls, admin exclusion and consumer subscription behavior in the real account.

Official listing documentation describes visibility and publication controls; it does not establish a guaranteed approval duration for this account. Account access, import, review submission and external consumer tests were not performed in this assessment. Keep September 28 through October 3 for platform feedback, monitoring and defect recovery; do not make an incomplete service public to meet the calendar.

[RapidAPI listing controls](https://docs.rapidapi.com/docs/hub-listing-general-tab). Account-specific publication steps must be checked in the owner’s account.


### API specification status

FastAPI generates OpenAPI 3.1.0 with 15 paths: 13 public GET and 2 admin POST. The static rapidapi/rapidapi-openapi.json remains at 8 paths and includes an unverified example production hostname. It must not be imported as a complete release contract.

Generate a public-only artifact from the chosen candidate, removing admin operations and checking response/error schemas, query bounds, headers, server URL and examples against HTTP tests. Keep the full internal contract distinct. A successful app.openapi() call only proves generation, not marketplace compatibility or complete schema validation.

The Python CI now generates a schema but does not compare it against the committed marketplace file. Add a drift gate under CIAPI-014/013. The Postman collection also needs parity verification against the accepted contract before external sharing.

### Launch scope and non goals

The launch product is the Python API. The archived React Explorer is a potential follow-up demonstration and is excluded from API deployment and acceptance. FastAPI’s developer documentation is part of the API experience.

Proposed initial scope is a limited, explicitly reviewed subset of the existing content, with source rights, citations, dates and country context validated. Current seed coverage is five cancers; the final publishable count may be smaller after review. Seven taxonomy entries and 37 defined categories must not be marketed as fully populated coverage.

Exclude personalized clinical recommendations, screening eligibility calculation, trial matching, generated medical answers, multilingual claims, broad crawling and UI expansion from the launch. Keep public search/category/registry/coverage/history behavior only where its acceptance is met. The owner has not yet approved a final reviewed corpus.

### Seed coverage verified locally

| Cancer | Records | Populated categories |
| :--- | :--- | :--- |
| breast-cancer | 9 | overview, risk_factors, screening, symptoms, treatment |
| colorectal-cancer | 5 | overview, screening, symptoms |
| lung-cancer | 3 | overview, risk_factors, symptoms |
| prostate-cancer | 2 | overview, symptoms |
| pancreatic-cancer | 2 | overview, symptoms |
| cervical-cancer | 0 | none |
| melanoma | 0 | none |


### Launch acceptance checklist

Release remains NOT READY. All gates require evidence on the final candidate, not on this documentation branch alone.

1. One Python serving entry point and an agreed public contract, including deliberate changes from the removed Node API.
2. Green CI for the candidate; image build, isolated boot, port, shutdown and dependency reproducibility checks.
3. Durable database, versioned migration, controlled seed behavior, restart persistence and successful restore.
4. Correct source/document/section identity, atomic citation updates, honest timestamps, accurate ingestion failure states and coherent history.
5. Document-level rights and content review for every published record, enforced across every public output path.
6. Production secrets, admin isolation, trusted proxy/rate behavior and consistent error/safety headers.
7. Complete public OpenAPI and working consumer examples with no unverified readiness or clinical guarantees.
8. Staging/live readiness, monitoring, gateway checks and independent RapidAPI consumer acceptance.

The 28 passing local tests satisfy a regression baseline only. Reproduced publication, ingestion, category and 429-header defects keep the relevant acceptance gates open.

## Historical draft, not current instructions or verified claims

The following original draft is retained to preserve review history. It may contain obsolete commands, unsupported numbers, clinical examples and unverified readiness claims. Do not execute or publish those claims without replacing them with the current accepted implementation and evidence.

## RapidAPI Publisher Guide for CancerInfo API

This guide provides step-by-step instructions for listing **CancerInfo API** on [RapidAPI Hub](https://rapidapi.com/hub) (and similar API marketplaces like Postman Public API Network, APILayer, and ProgrammableWeb) to serve the global developer and healthcare community 100% free of charge.

---

### 1. Prerequisites

1. A free publisher account at [RapidAPI.com](https://rapidapi.com/).
2. A deployed production URL for CancerInfo API (see `docs/FREE_HOSTING_DEPLOYMENT.md` for Render, Railway, Fly.io, or Cloud Run setup).
3. The prepared schema in `rapidapi/rapidapi-openapi.json` and collection in `rapidapi/postman_collection.json`.

---

### 2. Step-by-Step RapidAPI Hub Listing

#### Step 1: Add New API in RapidAPI Provider Dashboard
1. Log in to [RapidAPI Studio / Provider Dashboard](https://rapidapi.com/provider).
2. Click **"Add New API"** in the top right.
3. Complete the API Identity details:
   - **API Name**: `CancerInfo API`
   - **Short Description**: `Free, global, source-transparent cancer knowledge REST API with fact-level provenance from NCI, WHO, NHS, and Cancer Australia.`
   - **Category**: `Health and Fitness`
   - **Specify using**: Select **OpenAPI / Swagger Document**.
   - **Upload File**: Select `rapidapi/rapidapi-openapi.json` from this repository.
4. Click **Add API**. RapidAPI will automatically parse all paths, query parameters, descriptions, and schemas.

---

#### Step 2: Configure Base Target URL
1. Navigate to the **Hub Listing > Target URLs** tab in RapidAPI Studio.
2. Enter your deployed server address as the default target URL:
   - Example: `https://cancerinfo-api.onrender.com`
   - Test connection by clicking **Ping Target**.

---

#### Step 3: Configure 100% Free Community Pricing Plan
Our core mission is to empower researchers, developers, students, and patients free of charge.
1. Navigate to **Monetization > Plans & Pricing**.
2. Under the **Basic Plan** (Free):
   - **Plan Price**: `$0 / month`
   - **Requests Quota**: Set to **Unlimited** or generous community rate (e.g. `100,000 requests/month`).
   - **Rate Limit**: `120 requests/minute` (matches CancerInfo API's internal rate-limiter).
   - **Overage Fee**: `$0.00`.
3. Disable all paid tiers (Pro, Ultra, Mega) or mark them as hidden, ensuring developers never hit surprise paywalls.

---

#### Step 4: RapidAPI Hub Listing Enrichment
In the **Hub Listing > Overview** tab, enrich the presentation:

- **Logo**: Upload the CancerInfo badge icon (`/public/icon.png` or ribbon emblem).
- **Long Description**:
  ```markdown
  ### CancerInfo API — Global Cancer Knowledge with Provenance

  CancerInfo API is a free, structured public REST API delivering verified clinical cancer knowledge from world-leading public health organizations.

  #### Why Developers Use CancerInfo API:
  - 🔍 **Fact-Level Provenance**: Every symptom, screening guideline, and treatment record includes exact source URLs, retrieval dates, and legal attributions.
  - 🌐 **International Jurisdictions**: Compare health guidance between the US (NCI), UK (NHS), Australia (Cancer Australia), and WHO (Global).
  - 🧬 **Taxonomy Normalization**: Resolves acronyms (e.g., CRC -> Colorectal Cancer) and maps aliases across 37 standardized cancer categories.
  - 🛡️ **100% Free & Open**: Dedicated in honor of cancer fighters and their families.
  ```
- **Website Link**: Your GitHub repository URL.
- **Terms of Service**: Open Source (MIT) with standard clinical disclaimer: *"CancerInfo API provides informational data only and does not provide medical diagnosis or personal treatment advice."*

---

#### Step 5: Test and Publish
1. Go to the **Endpoints** tab and click **Test Endpoint** on `/v1/health` and `/v1/cancers`.
2. Confirm the response status is `200 OK` and returns verified JSON.
3. Toggle the API status from **Draft** to **Public**.
4. CancerInfo API will immediately be live and searchable by over 4,000,000 developers worldwide!

---

### 3. Alternative Free API Directories to Submit To

To maximize reach, submit CancerInfo API to these high-traffic public API directories:

1. **GitHub `public-apis/public-apis` Repository**:
   - Submit a Pull Request to the popular [public-apis](https://github.com/public-apis/public-apis) repository under the **Health** category.
   - Entry format:
     `| CancerInfo | Free, source-transparent cancer knowledge with fact-level provenance | No | HTTPS | Yes |`
2. **Postman Public API Network**:
   - In Postman, import `rapidapi/postman_collection.json`, click **Share Collection > Via Public API Network**.
3. **APIs.guru Directory**:
   - Submit `rapidapi/rapidapi-openapi.json` to the Wikipedia of Web APIs.
