# What You Can Build with CancerInfo API

## Current guidance, September 22, 2026

This guide applies to Python refactor `1199f735e3d77b5c1ada35e6451c7a5b4e36d063`. Current guidance below supersedes the prior draft retained at the end.

### Platform opportunities

The most relevant follow-up is a small API demonstration client that uses the same published API as external consumers. The archived cancerinfo-explorer-ui directory and ZIP provide a starting point, not a certified runnable product. A source import in GoogleDriveSync refers to a missing service and Firebase is absent from its declared dependencies; no UI build was run here.

A future demo should show endpoint, response, record citation, jurisdiction, freshness limitations and empty coverage without its own clinical dataset. Swagger and ReDoc already provide API exploration within FastAPI, so a richer UI is not a launch prerequisite.

Other opportunities remain educational integrations and source-transparent developer tools. No traffic, revenue, adoption or clinical outcome estimate is supported by this repository. Prior ecosystem statistics without cited evidence must not be used in launch claims.

### Enhancement backlog

Keep CIAPI-019 through CIAPI-024 and CIAPI-026 as later work unless a specific acceptance dependency requires otherwise. Full profiles, explicit coverage states, ontology provenance, structured comparisons, breadth expansion and automated tracker reconciliation are not implemented simply because the API has category or coverage routes.

CIAPI-025 is now smaller: Node serving and tracked bytecode are removed, while root package/lock artifacts, environment examples and archived client dependencies need review. Existing source-grounded README corrections are part of this documentation pass; no new clinical capability is being added.

Prioritize defects that can serve wrong, unapproved or falsely current content over new endpoints. A demonstration app can be a distinct follow-up project with its own scope and tests after the API release is accepted.

### Medical safety positioning

CancerInfo API is an informational developer API. It is not a medical device claim, clinical decision engine, personalized treatment tool or substitute for clinicians. The repository’s educational purpose remains, but current content has not received item-by-item clinical verification in this assessment.

The API exposes source text/metadata with jurisdiction and citation fields. Those fields can be incomplete or misleading until ingestion dates, provenance identity and publication controls are fixed. A disclaimer does not correct an incorrect fact, wrong citation or restricted publication.

Launch descriptions must state actual reviewed corpus and limitations. Do not claim zero hallucinations, guaranteed accuracy, comprehensive global guidance or validated screening/trial eligibility. The archived UI and proposed downstream applications do not expand the API’s clinical scope.

### Scope of the retained concepts

The earlier screening navigator, copilot, symptom journal, trial pre-screener and multilingual kiosk are unimplemented ideas. The API has no structured eligibility rules, embeddings, trial-matching integration, personal health storage or verified multilingual corpus. Any dates, ages or medical thresholds in the earlier draft were not revalidated and must not be used as guidance. A RAG prompt cannot guarantee zero hallucinations. Begin with a read-only source/coverage demo using the real API after launch acceptance.

## Historical draft, not current instructions or verified claims

The following original draft is retained to preserve review history. It may contain obsolete commands, unsupported numbers, clinical examples and unverified readiness claims. Do not execute or publish those claims without replacing them with the current accepted implementation and evidence.

## What You Can Build with CancerInfo API

CancerInfo API was built to serve as the structured, verified knowledge foundation for developers, research labs, patient support groups, and digital health startups.

Here are 5 impactful application architectures developers can build using this API:

---

### 1. Global Cancer Screening Age & Guideline Navigator

#### The Problem:
Screening recommendations vary significantly across borders. For example, bowel cancer screening begins at age 45 in the US (USPSTF), age 50-54 in the UK (NHS bowel screening), and age 50 in Australia (National Bowel Cancer Screening Program). Patients and expats frequently struggle to find their jurisdiction's rules.

#### How to Build It:
- **UI**: A patient enters their age, biological sex, country of residence, and family history.
- **API Integration**:
  - Calls `GET /v1/cancers/{cancer}/screening?country={COUNTRY_CODE}`
  - Parses the normalized screening records and returns the jurisdiction's specific age thresholds and modality (FIT kit, colonoscopy, mammography).
- **Key Feature**: Side-by-side comparison tab comparing screening guidelines between the US, UK, Australia, and WHO standards with clickable primary source links.

---

### 2. Provenance-Grounded AI Oncology Copilot (RAG Architecture)

#### The Problem:
Generic Large Language Models frequently hallucinate medical facts, cite outdated guidelines, or fail to state where advice originated.

#### How to Build It:
- **Workflow**:
  1. User asks: *"What are the early red-flag signs of colorectal cancer and what tests should I ask my doctor about?"*
  2. Embed the query and call `GET /v1/search?q=colorectal+cancer+signs` & `GET /v1/cancers/colorectal-cancer/symptoms`.
  3. Feed the retrieved, normalized records as immutable ground-truth context into an LLM prompt:
     `"Answer using ONLY the provided verified facts below. Always cite the exact source organization and URL."`
  4. The generated response contains zero hallucinations, accompanied by verifiable citations from NCI, WHO, and NHS.

---

### 3. Patient Advocacy & Caregiver Symptom Journal

#### The Problem:
Newly diagnosed patients and their caregivers are overwhelmed by conflicting internet forum posts and unverified advice.

#### How to Build It:
- **Features**:
  - **Symptom Tracker**: Patients log daily fatigue, pain, or treatment side effects.
  - **Verified Clinical Context**: When logging a symptom, the app displays the authoritative clinical context from `GET /v1/cancers/{cancer}/symptoms` and `GET /v1/cancers/{cancer}/treatment`, helping patients frame concise questions for their next oncology appointment.
  - **Export to PDF**: Compiles patient symptoms and authoritative reference links for their oncologist.

---

### 4. Multi-Jurisdiction Clinical Trials Eligibility Pre-Screener

#### How to Build It:
- Matches patient cancer stage and biomarker status against standardized terminology from `GET /v1/cancers/{cancer}` and `GET /v1/cancers/{cancer}/genetics`.
- Cross-references with ClinicalTrials.gov and EU Clinical Trials Register.

---

### 5. Community Health Center Multilingual Screening Kiosk

#### How to Build It:
- An offline-capable tablet app placed in community clinics and public libraries.
- Consumes `GET /v1/cancers` and `GET /v1/cancers/{cancer}/risk_factors` to display risk factor checklists and lifestyle prevention tips.
- Displays full legal and clinical disclaimers, encouraging patients to consult clinic physicians on-site.
