# CIAPI-L004 Candidate Report & Handoff to Mithra: Resolve Document Reuse Rights & Quarantine Unresolved Material

> **Working-Tree Candidate & Formal Handoff Document**  
> Prepared for **Mithra** (Reviewer / Evaluator) & **Prakash** (Repository Owner).  
> **New Branch:** `CIAPI-L004-resolve-document-reuse-rights-and-quarantine` (branched from `CIAPI-L003-postgresql-migrations-controlled-initialization`)  
> In accordance with `CONTRIBUTING.md:67`: *"Include requirements, changed files, schema/data impact, exact tests/results and unresolved risks in each handoff."*  
> **Status:** All code, migration, seed, API schema, and test requirements implemented and verified (88/88 tests passing). Ready for commit and review.

---

## 1. Executive Summary & Objective Realization

CIAPI-L004 resolves the critical architectural flaw where source-level clearance flags (`license_status="APPROVED"`, `trust_tier="Tier 1"`, or government agency status) were erroneously assumed to clear all underlying content published by that entity.

### Core Governance Guarantees Implemented:
1. **Document-Level Fail-Closed Clearance**: Publication eligibility is strictly evaluated per individual document record. Source-level metadata never confers publication eligibility to any document.
2. **Comprehensive URL Inventory (32 URLs)**: Every candidate document (20 normal content URLs + 20 consensus URLs = 32 distinct URLs) has a dedicated `SourceDocument` record with explicit rights metadata.
3. **Quarantine of Unresolved Material**:
   - **0 of 32 documents are marked `ELIGIBLE`**.
   - **4 WHO documents** are quarantined under `PERMISSION_PENDING` due to CC BY-NC-SA 3.0 IGO non-commercial restrictions incompatible with public/commercial API distribution without explicit written agreement.
   - **28 documents** (14 NCI, 9 NHS, 4 Cancer Australia, 1 CDC) are held under `REVIEW_REQUIRED` fail-closed pending page-by-page audit for embedded third-party illustrations, photography releases, Crown copyright terms, or clinical consortium tables.
4. **Relational Consensus Citation Linkage**: Every `ConsensusFactSource` record now possesses an explicit foreign key (`source_document_id`) linking directly to its backing `SourceDocument`. Quotation snippets (50–250 characters) and direct attributions are strictly preserved.
5. **Linear Reversible Migration**: Alembic migration `0002_document_rights_and_consensus_linkage` builds cleanly on top of L003's `0001_initial_schema` with verified upgrade, downgrade, and re-upgrade paths.
6. **Consumer API Provenance**: Downstream consumers receive document-level provenance, publication status, reuse conditions, and commercial redistribution permissions in `/v1/cancers/{slug}/{topic}` and `/v1/search` payloads.

---

## 2. Candidate URL Inventory & Exact Decision Matrix (32 URLs)

| # | Source ID | Candidate URL | `publication_status` | Assigned Quarantine Reason |
|---|---|---|---|---|
| 1 | `nci-us` | `https://www.cancer.gov/types/breast` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded illustrations, photography, and third-party clinical media. |
| 2 | `nci-us` | `https://www.cancer.gov/types/breast/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded illustrations and third-party clinical media. |
| 3 | `nci-us` | `https://www.cancer.gov/types/breast/treatment` | `REVIEW_REQUIRED` | Awaiting exact-document verification of clinical study tables and proprietary drug references. |
| 4 | `nci-us` | `https://www.cancer.gov/types/cervical/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded anatomical diagrams. |
| 5 | `nci-us` | `https://www.cancer.gov/types/cervical/screening` | `REVIEW_REQUIRED` | Awaiting item-level rights audit; screening guidelines may reference joint proprietary consensus tables. |
| 6 | `nci-us` | `https://www.cancer.gov/types/colorectal` | `REVIEW_REQUIRED` | Awaiting exact-document audit for medical diagrams and patient photography releases. |
| 7 | `nci-us` | `https://www.cancer.gov/types/colorectal/screening` | `REVIEW_REQUIRED` | Colorectal screening recommendations may cite proprietary USPSTF or clinical consortium evidence tables. |
| 8 | `nci-us` | `https://www.cancer.gov/types/lung` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded clinical illustrations and third-party infographics. |
| 9 | `nci-us` | `https://www.cancer.gov/types/lung/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for symptom presentation diagrams. |
| 10 | `nci-us` | `https://www.cancer.gov/types/skin` | `REVIEW_REQUIRED` | Awaiting exact-document verification for clinical dermatological photography and ABCDE guide illustrations. |
| 11 | `nci-us` | `https://www.cancer.gov/types/prostate` | `REVIEW_REQUIRED` | Consensus citation; awaiting item-level audit of prostate overview and anatomical diagrams. |
| 12 | `nci-us` | `https://www.cancer.gov/types/prostate/symptoms` | `REVIEW_REQUIRED` | Consensus citation; awaiting item-level audit of urinary symptom guides. |
| 13 | `nci-us` | `https://www.cancer.gov/types/prostate/screening` | `REVIEW_REQUIRED` | Consensus citation; PSA screening guideline may incorporate copyrighted clinical decision algorithms. |
| 14 | `nci-us` | `https://www.cancer.gov/types/skin/symptoms` | `REVIEW_REQUIRED` | Consensus citation; melanoma clinical pictures must be confirmed public domain vs licensed medical photography. |
| 15 | `nhs-uk` | `https://www.nhs.uk/conditions/breast-cancer/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 text vs third-party images and trust photography. |
| 16 | `nhs-uk` | `https://www.nhs.uk/conditions/breast-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 terms and confirmation that medical diagrams are excluded. |
| 17 | `nhs-uk` | `https://www.nhs.uk/conditions/bowel-cancer/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 coverage on patient staging descriptions. |
| 18 | `nhs-uk` | `https://www.nhs.uk/conditions/bowel-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 compliance for symptom text. |
| 19 | `nhs-uk` | `https://www.nhs.uk/conditions/lung-cancer/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 terms and removal of NHS trust-specific media. |
| 20 | `nhs-uk` | `https://www.nhs.uk/conditions/lung-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 text terms and attribution requirements. |
| 21 | `nhs-uk` | `https://www.nhs.uk/conditions/cervical-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation; awaiting exact-document confirmation of OGL v3.0 compliance. |
| 22 | `nhs-uk` | `https://www.nhs.uk/conditions/cervical-screening/` | `REVIEW_REQUIRED` | Consensus citation; cervical screening guidelines require verification of NHS OGL v3.0 coverage. |
| 23 | `nhs-uk` | `https://www.nhs.uk/conditions/prostate-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation; awaiting exact-document confirmation of OGL v3.0 compliance. |
| 24 | `who-global` | `https://www.who.int/news-room/fact-sheets/detail/breast-cancer` | `PERMISSION_PENDING` | WHO CC BY-NC-SA 3.0 IGO non-commercial restriction and redistribution conditions are unresolved for public/commercial API consumption. A free API cannot be presumed non-commercial. Written permission or commercial waiver required. |
| 25 | `who-global` | `https://www.who.int/news-room/fact-sheets/detail/cancer` | `PERMISSION_PENDING` | Consensus citation; WHO CC BY-NC-SA 3.0 IGO non-commercial license restriction prevents public/commercial API redistribution without written permission. |
| 26 | `who-global` | `https://www.who.int/news-room/fact-sheets/detail/cervical-cancer` | `PERMISSION_PENDING` | Consensus citation; WHO CC BY-NC-SA 3.0 IGO non-commercial license restriction prevents public/commercial API redistribution without written permission. |
| 27 | `who-global` | `https://www.who.int/news-room/fact-sheets/detail/lung-cancer` | `PERMISSION_PENDING` | WHO CC BY-NC-SA 3.0 IGO non-commercial restriction prevents public/commercial API redistribution without written permission. |
| 28 | `cancer-australia` | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/bowel-cancer/symptoms` | `REVIEW_REQUIRED` | Source-level CC BY 4.0 label cannot be used as automatic blanket clearance. Exact documents remain non-publication-eligible until individual page review verifies absence of third-party restrictions or Crown copyright carve-outs. |
| 29 | `cancer-australia` | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/lung-cancer/symptoms` | `REVIEW_REQUIRED` | Consensus citation; source-level CC BY 4.0 is unverified for this exact document. Item-level audit required under Crown copyright. |
| 30 | `cancer-australia` | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/melanoma/symptoms` | `REVIEW_REQUIRED` | Consensus citation; high probability of third-party clinical copyright on dermatological symptoms and illustrations under Commonwealth Crown copyright and CC BY 4.0 conditions. |
| 31 | `cancer-australia` | `https://www.canceraustralia.gov.au/cancer-types/breast-cancer/screening` | `REVIEW_REQUIRED` | Awaiting exact-document verification of multi-jurisdictional program recommendations under Commonwealth Crown copyright and CC BY 4.0 terms. |
| 32 | `cdc-us` | `https://www.cdc.gov/cancer/colorectal/basic_info/screening/` | `REVIEW_REQUIRED` | CDC public domain policy specifically excludes third-party materials, campaign partner assets, and copyrighted photos. Exact page must be audited. |

---

## 3. Schema & Data Impact

### Database Changes:
- **Migration**: `0002_document_rights_and_consensus_linkage.py`
- **Columns Added to `source_documents`**:
  `publication_status` (server_default='REVIEW_REQUIRED', nullable=False, indexed), `rights_evidence_url`, `rights_reviewed_at`, `rights_reviewer`, `permissible_use`, `commercial_redistribution_allowed`, `redistribution_allowed`, `full_text_storage_allowed`, `derived_summary_allowed`, `attribution_required`, `attribution_text`, `reuse_restrictions`, `quarantine_reason`, `third_party_permission_status`, `third_party_permission_notes`.
- **Columns Added to `consensus_fact_sources`**:
  `source_document_id` (ForeignKey to `source_documents.id`, indexed, nullable=True).
- **Baseline Seed Population**:
  - Total rows: increased from **191 to 203 rows** to reflect the 12 consensus-only `SourceDocument` rows.
  - Table breakdown: Sources: 5, SourceHealth: 5, Cancers: 7, CancerAliases: 22, SourceDocuments: 32 (20 content + 12 consensus), ContentRecords: 21, ContentSources: 21, ContentVersions: 21, ConsensusFacts: 21, ConsensusFactSources: 48. Total = 203.

---

## 4. Current Validation Summary & Test Evidence

### Full Pytest Suite Result:
```text
============================= test session starts ==============================
platform darwin -- Python 3.11.16, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/prakash/VS Code/CancerInfo-API
plugins: asyncio-1.4.0, anyio-4.15.1
collected 88 items

tests/test_admin_and_pipeline.py ....                                    [  4%]
tests/test_bootstrap.py ..........                                       [ 15%]
tests/test_cancers.py .......                                            [ 23%]
tests/test_consensus_facts.py ......                                     [ 30%]
tests/test_document_rights.py ..............                             [ 46%]
tests/test_health.py ...                                                 [ 50%]
tests/test_migrations.py .......................                         [ 76%]
tests/test_neon_clean_guard.py .......                                   [ 84%]
tests/test_search.py ....                                                [ 88%]
tests/test_sources.py .....                                              [ 94%]
tests/test_taxonomy_and_normalization.py .....                           [100%]

======================== 88 passed, 1 warning in 4.77s =========================
```

- **Document Rights Test Suite (`tests/test_document_rights.py`)**: 14 tests covering all 20 acceptance requirements (100% pass).
- **Bootstrap Suite (`tests/test_bootstrap.py`)**: 10 tests verifying 203 planned baseline rows, rollback safety, and idempotency (100% pass).
- **Migration Suite (`tests/test_migrations.py`)**: 23 tests verifying clean upgrade/downgrade, zero drift, and adoption parity (100% pass).

---

## 5. Precise File-Change Summary

| File | Status | Description |
|---|---|---|
| `alembic/versions/0002_document_rights_and_consensus_linkage.py` | Untracked (New) | Alembic migration adding document rights columns to `source_documents` and `source_document_id` FK to `consensus_fact_sources`. |
| `app/core/constants.py` | Modified | Added `PublicationStatus` enum (`ELIGIBLE`, `REVIEW_REQUIRED`, `QUARANTINED`, `PERMISSION_PENDING`, `REJECTED`). |
| `app/core/rights_validation.py` | Untracked (New) | Core rights validation engine, eligibility evaluator, and assertion errors. |
| `app/ingestion/rights_inventory.py` | Untracked (New) | Canonical machine-readable inventory of all 32 candidate URLs and audit export tool. |
| `app/models/__init__.py` | Modified | Added rights fields, fail-closed `__init__`, `is_publication_eligible()`, and reciprocal consensus relationships. |
| `app/ingestion/seed.py` | Modified | Seeding logic applying document rights from inventory and linking consensus citations to exact `SourceDocument` rows. |
| `app/ingestion/pipeline.py` | Modified | Removed source-to-document license inheritance; new documents default fail-closed to `REVIEW_REQUIRED`. |
| `app/schemas/content.py` | Modified | Added document rights fields to `ProvenanceSourceOut` and `CorroboratingSourceOut`. |
| `app/repositories/content_repo.py` | Modified | Eager-loads `source_document` on `ContentSource` and `ConsensusFactSource`. |
| `app/api/v1/endpoints/cancers.py` | Modified | Serializes exact document attribution and redistribution metadata in response models. |
| `app/api/v1/endpoints/search.py` | Modified | Serializes exact document attribution and redistribution metadata in search hit responses. |
| `app/database/bootstrap.py` | Modified | Updated planned baseline count to 203 rows. |
| `app/database/adoption.py` | Modified | Updated baseline adoption target to `0002_document_rights_and_consensus_linkage`. |
| `docs/CONTENT_RIGHTS_AND_ATTRIBUTION.md` | Untracked (New) | Full 11-section policy, legal, architecture, and operational transition documentation. |
| `candidate_report_CIAPI-L004.md` | Untracked (New) | Formal candidate report and handoff for Bob and Prakash. |
| `tests/test_document_rights.py` | Untracked (New) | Comprehensive test suite for all 20 L004 requirements. |
| `tests/test_bootstrap.py` | Modified | Updated expected baseline row count to 203. |
| `tests/test_migrations.py` | Modified | Updated expected baseline row count to 203. |

---

## 6. Unresolved Risks & Next Steps for Bob

### Unresolved Risks:
1. **Legal Clearance Pending**: 0 of 32 documents are currently cleared for commercial redistribution (`ELIGIBLE`). Until Prakash conducts the manual page-by-page audit, the API operates in quarantine mode where unreviewed materials cannot be syndicated as cleared public content.
2. **WHO Permission Requirement**: The 4 WHO URLs cannot be cleared without a signed written waiver or commercial license from WHO permissions.
3. **Database Drift Safeguard**: Environments running unversioned schemas must use `scripts/adopt_existing_schema.py` or run `alembic upgrade head` before starting the application in production mode.

### Next Steps for Bob:
1. **Review Working Tree Diff**:
   ```bash
   git diff
   git status
   ```
2. **Stage and Commit Changes**:
   ```bash
   git add .
   git commit -m "feat(rights): resolve document reuse rights and quarantine unresolved material (CIAPI-L004)"
   ```
3. **Push to Remote Branch & Trigger CI**:
   ```bash
   git push origin CIAPI-L003-postgresql-migrations-controlled-initialization
   ```
4. **Create Pull Request**:
   - Compare `main` ... `CIAPI-L003-postgresql-migrations-controlled-initialization`
   - Include `candidate_report_CIAPI-L004.md` in the PR description as the evidence base.
