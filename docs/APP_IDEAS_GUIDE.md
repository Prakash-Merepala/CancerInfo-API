# What You Can Build with CancerInfo API

CancerInfo API was built to serve as the structured, verified knowledge foundation for developers, research labs, patient support groups, and digital health startups.

Here are 5 impactful application architectures developers can build using this API:

---

## 1. Global Cancer Screening Age & Guideline Navigator

### The Problem:
Screening recommendations vary significantly across borders. For example, bowel cancer screening begins at age 45 in the US (USPSTF), age 50-54 in the UK (NHS bowel screening), and age 50 in Australia (National Bowel Cancer Screening Program). Patients and expats frequently struggle to find their jurisdiction's rules.

### How to Build It:
- **UI**: A patient enters their age, biological sex, country of residence, and family history.
- **API Integration**:
  - Calls `GET /v1/cancers/{cancer}/screening?country={COUNTRY_CODE}`
  - Parses the normalized screening records and returns the jurisdiction's specific age thresholds and modality (FIT kit, colonoscopy, mammography).
- **Key Feature**: Side-by-side comparison tab comparing screening guidelines between the US, UK, Australia, and WHO standards with clickable primary source links.

---

## 2. Provenance-Grounded AI Oncology Copilot (RAG Architecture)

### The Problem:
Generic Large Language Models frequently hallucinate medical facts, cite outdated guidelines, or fail to state where advice originated.

### How to Build It:
- **Workflow**:
  1. User asks: *"What are the early red-flag signs of colorectal cancer and what tests should I ask my doctor about?"*
  2. Embed the query and call `GET /v1/search?q=colorectal+cancer+signs` & `GET /v1/cancers/colorectal-cancer/symptoms`.
  3. Feed the retrieved, normalized records as immutable ground-truth context into an LLM prompt:
     `"Answer using ONLY the provided verified facts below. Always cite the exact source organization and URL."`
  4. The generated response contains zero hallucinations, accompanied by verifiable citations from NCI, WHO, and NHS.

---

## 3. Patient Advocacy & Caregiver Symptom Journal

### The Problem:
Newly diagnosed patients and their caregivers are overwhelmed by conflicting internet forum posts and unverified advice.

### How to Build It:
- **Features**:
  - **Symptom Tracker**: Patients log daily fatigue, pain, or treatment side effects.
  - **Verified Clinical Context**: When logging a symptom, the app displays the authoritative clinical context from `GET /v1/cancers/{cancer}/symptoms` and `GET /v1/cancers/{cancer}/treatment`, helping patients frame concise questions for their next oncology appointment.
  - **Export to PDF**: Compiles patient symptoms and authoritative reference links for their oncologist.

---

## 4. Multi-Jurisdiction Clinical Trials Eligibility Pre-Screener

### How to Build It:
- Matches patient cancer stage and biomarker status against standardized terminology from `GET /v1/cancers/{cancer}` and `GET /v1/cancers/{cancer}/genetics`.
- Cross-references with ClinicalTrials.gov and EU Clinical Trials Register.

---

## 5. Community Health Center Multilingual Screening Kiosk

### How to Build It:
- An offline-capable tablet app placed in community clinics and public libraries.
- Consumes `GET /v1/cancers` and `GET /v1/cancers/{cancer}/risk_factors` to display risk factor checklists and lifestyle prevention tips.
- Displays full legal and clinical disclaimers, encouraging patients to consult clinic physicians on-site.
