# CIAPI-L004 Candidate Report & Handoff to Mithra: Resolve Document Reuse Rights & Quarantine Unresolved Material

> **Repository-Level Candidate Report & Review Document**  
> Prepared for **Mithra** (Reviewer / Evaluator) & **Prakash** (Repository Owner).  
> In accordance with `CONTRIBUTING.md:67`: *"Include requirements, changed files, schema/data impact, exact tests/results and unresolved risks in each handoff."*  
> **Current Branch:** `CIAPI-L004-resolve-document-reuse-rights-and-quarantine`  
> **Reviewed Commit SHA:** `a8f50395eaed22db49193d2dad249ade17ec5b9d`  
> **Actual Remote L003 Merge Base:** `00356293d28a3cdb99320db5dbcd7e13b2766fd1`  

---

## 1. Executive Summary & Status Separation

CIAPI-L004 resolves the critical architectural flaw where source-level clearance flags (`license_status="APPROVED"`, `trust_tier="Tier 1"`, or government agency status) were erroneously assumed to clear all underlying content published by that entity.

Following Mithra's review, project status is strictly divided into two distinct dimensions:

### A. Engineering Implementation Status: COMPLETE
1. **Document-Level Fail-Closed Clearance**: Publication eligibility is strictly evaluated per individual document record. Source-level metadata never confers publication eligibility to any document.
2. **Comprehensive URL Inventory (32 URLs)**: Every candidate document (20 normal content URLs + 20 consensus URLs = 32 distinct URLs) has a dedicated `SourceDocument` record with explicit rights metadata.
3. **Quarantine of Unresolved Material**:
   - **0 of 32 documents are marked `ELIGIBLE`**.
   - **4 WHO documents** are quarantined under `PERMISSION_PENDING` due to CC BY-NC-SA 3.0 IGO non-commercial restrictions incompatible with public/commercial API distribution without explicit written agreement.
   - **28 documents** (14 NCI, 9 NHS, 4 Cancer Australia, 1 CDC) are held under `REVIEW_REQUIRED` fail-closed pending page-by-page audit for embedded third-party illustrations, photography releases, Crown copyright terms, or clinical consortium tables.
4. **Relational Consensus Citation Linkage**: Every `ConsensusFactSource` record now possesses an explicit foreign key (`source_document_id`) linking directly to its backing `SourceDocument`. Quotation snippets (50–250 characters) and direct attributions are strictly preserved.
5. **Linear Reversible Migration**: Alembic migration `0002_document_rights` (revision ID <= 32 chars for PostgreSQL compatibility) builds cleanly on top of L003's `0001_initial_schema` with verified upgrade, downgrade, and re-upgrade paths.
6. **Consumer API Provenance**: Downstream consumers receive document-level provenance, publication status, reuse conditions, and commercial redistribution permissions in `/v1/cancers/{slug}/{topic}` and `/v1/search` payloads.
7. **Consumer Marketplace & Directory Listing Rules**: Documented in `docs/CONTENT_RIGHTS_AND_ATTRIBUTION.md` Section 12.

### B. L004 Acceptance Status: BLOCKED ON OWNER REVIEW (OPEN)
- **Rights Evidence Collected**: 32 / 32 candidate documents have authoritative policy/license evidence URLs.
- **Owner Review Dates**: 0 / 32 documents have formal review dates (`rights_reviewed_at is null`).
- **Decision Owners**: 0 / 32 documents have formal decision owners (`rights_reviewer is null`).
- **Third-Party Permissions**: 0 requests submitted; 4 WHO fact sheets have permissions `REQUIRED_NOT_SUBMITTED`.
- **Truthful Acceptance Reporting**: The missing owner review is reported as an open acceptance blocker until repository owner (Prakash) executes his manual review. No dates or owner approvals have been fabricated.

---

## 2. Reconciled 32-Document Candidate Inventory & Decision Matrix

Deterministically generated from `app/ingestion/rights_inventory.py` and matching database seed records:

| # | Source ID | Publishing Body | URL | Status | Assigned Quarantine Reason |
|---|---|---|---|---|---|
| 1 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast` | `REVIEW_REQUIRED` | Awaiting exact-document audit for third-party medical illustrations, copyrighted summaries, or external guideline inclusions. Source-level public domain status does not confer automatic per-document clearance. |
| 2 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast/screening` | `REVIEW_REQUIRED` | Awaiting item-level verification of external guideline text and third-party recommendations. |
| 3 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded illustrations and third-party clinical media. |
| 4 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast/treatment` | `REVIEW_REQUIRED` | Awaiting exact-document verification of clinical study tables and proprietary drug references. |
| 5 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/cervical/symptoms` | `REVIEW_REQUIRED` | Consensus-only citation awaiting exact-page review for third-party media and external citations. |
| 6 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/colorectal` | `REVIEW_REQUIRED` | Awaiting exact-document audit for anatomical graphics and proprietary statistics. |
| 7 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/colorectal/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded illustrations and third-party media. |
| 8 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/lung` | `REVIEW_REQUIRED` | Awaiting exact-document audit for histological images and medical media. |
| 9 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/lung/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for diagnostic flowchart diagrams and external citations. |
| 10 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/pancreatic` | `REVIEW_REQUIRED` | Awaiting exact-document audit for medical diagrams and clinical text provenance. |
| 11 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/pancreatic/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for third-party clinical contributions. |
| 12 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/prostate` | `REVIEW_REQUIRED` | Awaiting exact-document audit for anatomical illustrations and grading diagrams. |
| 13 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/prostate/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for clinical symptom text and media. |
| 14 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/skin/symptoms` | `REVIEW_REQUIRED` | Consensus citation; high risk of third-party clinical photograph copyright in dermatological ABCDE guides. |
| 15 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/bowel-cancer-screening/` | `REVIEW_REQUIRED` | Awaiting exact-document verification under OGL v3.0 to confirm absence of proprietary screening kit imagery or third-party guidelines. |
| 16 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/bowel-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document audit for third-party licensed patient photography and clinical graphics. |
| 17 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/breast-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document audit for clinical symptom media and proprietary partner contributions. |
| 18 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/breast-screening-mammogram/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of clinical equipment photos and guideline references. |
| 19 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/cervical-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation awaiting exact-page review for third-party media under OGL v3.0. |
| 20 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/lung-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation awaiting exact-page review for third-party imagery. |
| 21 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/melanoma-skin-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation; high probability of third-party clinical dermatological copyright on ABCDE images. |
| 22 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/pancreatic-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation awaiting exact-page review for third-party media under OGL v3.0. |
| 23 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/prostate-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation awaiting exact-page review for third-party media under OGL v3.0. |
| 24 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/breast-cancer` | `PERMISSION_PENDING` | WHO CC BY-NC-SA 3.0 IGO non-commercial restriction and redistribution conditions are unresolved for public/commercial API consumption. A free API cannot be presumed non-commercial. Written permission or commercial waiver required. |
| 25 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/cancer` | `PERMISSION_PENDING` | Consensus citation; WHO CC BY-NC-SA 3.0 IGO non-commercial license restriction prevents public/commercial API redistribution without written permission. |
| 26 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/cervical-cancer` | `PERMISSION_PENDING` | Consensus citation; WHO CC BY-NC-SA 3.0 IGO non-commercial license restriction prevents public/commercial API redistribution without written permission. |
| 27 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/lung-cancer` | `PERMISSION_PENDING` | WHO CC BY-NC-SA 3.0 IGO non-commercial restriction prevents public/commercial API redistribution without written permission. |
| 28 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/bowel-cancer/symptoms` | `REVIEW_REQUIRED` | Source-level CC BY 4.0 label cannot be used as automatic blanket clearance. Exact documents remain non-publication-eligible until individual page review verifies absence of third-party restrictions or Crown copyright carve-outs. |
| 29 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/lung-cancer/symptoms` | `REVIEW_REQUIRED` | Consensus citation; source-level CC BY 4.0 is unverified for this exact document. Item-level audit required under Crown copyright. |
| 30 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/melanoma/symptoms` | `REVIEW_REQUIRED` | Consensus citation; high probability of third-party clinical copyright on dermatological symptoms and illustrations under Commonwealth Crown copyright and CC BY 4.0 conditions. |
| 31 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/cancer-types/breast-cancer/screening` | `REVIEW_REQUIRED` | Awaiting exact-document verification of multi-jurisdictional program recommendations under Commonwealth Crown copyright and CC BY 4.0 terms. |
| 32 | `cdc-us` | Centers for Disease Control and Prevention | `https://www.cdc.gov/cancer/colorectal/basic_info/screening/` | `REVIEW_REQUIRED` | Item-level review unresolved. CDC specifically identifies third-party and copyrighted material exceptions on its pages. Without item-level evidence confirming the page contains only public domain text, publication remains fail-closed. |

---

## 3. Schema & Data Impact

### Database Changes:
- **Migration**: `alembic/versions/0002_document_rights.py` (Revision ID: `0002_document_rights`, length 20 <= 32 chars).
- **Columns Added to `source_documents`**:
  `publication_status` (server_default='REVIEW_REQUIRED', nullable=False, indexed), `rights_evidence_url`, `rights_reviewed_at`, `rights_reviewer`, `permissible_use`, `commercial_redistribution_allowed`, `redistribution_allowed`, `full_text_storage_allowed`, `derived_summary_allowed`, `attribution_required`, `attribution_text`, `reuse_restrictions`, `quarantine_reason`, `third_party_permission_status`, `third_party_permission_notes`.
- **Columns Added to `consensus_fact_sources`**:
  `source_document_id` (ForeignKey to `source_documents.id`, indexed, nullable=True).
- **Baseline Seed Population**:
  - Total rows: increased from **191 to 203 rows** to reflect the 12 consensus-only `SourceDocument` rows.
  - Table breakdown: Sources: 5, SourceHealth: 5, Cancers: 7, CancerAliases: 22, SourceDocuments: 32 (20 content + 12 consensus), ContentRecords: 21, ContentSources: 21, ContentVersions: 21, ConsensusFacts: 21, ConsensusFactSources: 48. Total = 203.
- **Populated Environment Transition**:
  - Upgrades existing populated L003 databases via `python scripts/transition_l004.py` without reseeding or overwriting existing content, quotes, or attributions.

---

## 4. Current Validation Summary & Test Evidence

### Full Pytest Suite Result (97 / 97 Tests Passing):
```text
============================= test session starts ==============================
platform darwin -- Python 3.11.16, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/prakash/VS Code/CancerInfo-API
collected 97 items

tests/test_admin_and_pipeline.py ....                                    [  4%]
tests/test_bootstrap.py ..........                                       [ 14%]
tests/test_cancers.py .......                                            [ 21%]
tests/test_consensus_facts.py ......                                     [ 27%]
tests/test_document_rights.py ......................                     [ 50%]
tests/test_health.py ...                                                 [ 53%]
tests/test_migrations.py ........................                        [ 78%]
tests/test_neon_clean_guard.py .......                                   [ 85%]
tests/test_search.py ....                                                [ 89%]
tests/test_sources.py .....                                              [ 94%]
tests/test_taxonomy_and_normalization.py .....                           [100%]

======================== 97 passed, 1 warning in 5.11s =========================
```

### Environment Breakdown & Resolved Issues:
1. **Local SQLite Execution**:
   - 97 of 97 automated tests pass cleanly across the entire repository.
   - Comprehensive test suite in `tests/test_document_rights.py` (22 tests) and `tests/test_migrations.py` (24 tests).
2. **PostgreSQL CI Run 36301697756 Resolution**:
   - **Root Cause**: PostgreSQL's `alembic_version` table defines `version_num VARCHAR(32)`. The original revision ID `0002_document_rights_and_consensus_linkage` (43 characters) caused PostgreSQL to fail with a string truncation error.
   - **Resolution**: Shortened to `0002_document_rights` (20 characters).
   - **Backward Compatibility**: Transparent alias remapping ensures any local SQLite databases stamped with the old revision ID are automatically migrated and recognized.
3. **Skipped Checks**:
   - Production Neon DB access was not performed (forbidden per project safety guidelines).
   - Live clinical verification deferred to medical reviewers.
   - Universal publication gate deferred to CIAPI-L008.

---

## 5. Precise File-Change Summary

| File | Status | Description |
|---|---|---|
| `alembic/versions/0002_document_rights.py` | Added / Renamed | Linear Alembic migration adding document rights fields and consensus linkage (rev id `0002_document_rights` <= 32 chars). |
| `app/core/constants.py` | Modified | Added `PublicationStatus` and `ThirdPartyPermissionStatus` enums. |
| `app/core/rights_validation.py` | Added | Consolidated fail-closed publication validation, eligibility evaluator, and evidence consistency checks. |
| `app/ingestion/rights_inventory.py` | Added | Canonical 32-URL registry, acceptance audit engine, durable owner-review API, and table generator. |
| `app/database/transition.py` | Added | Controlled, transactional, repeat-safe transition engine for populated L003 databases. |
| `scripts/transition_l004.py` | Added | CLI tool for executing dry-run validation and atomic L004 transition without reseeding. |
| `app/models/__init__.py` | Modified | Added rights columns, fail-closed `__init__`, consolidated `is_publication_eligible()`, and reciprocal relationships. |
| `app/ingestion/seed.py` | Modified | Seed engine applying rights from inventory and establishing consensus `SourceDocument` linkage. |
| `app/ingestion/pipeline.py` | Modified | Default newly discovered documents strictly to `REVIEW_REQUIRED`. |
| `app/schemas/content.py` | Modified | Exposed document-level rights fields in API response models. |
| `app/repositories/content_repo.py` | Modified | Eager-loads `source_document` on junctions. |
| `app/api/v1/endpoints/cancers.py` | Modified | Serializes exact document attribution and redistribution metadata in response models. |
| `app/api/v1/endpoints/search.py` | Modified | Serializes exact document attribution and redistribution metadata in search hit responses. |
| `app/database/bootstrap.py` | Modified | Updated planned baseline count to 203 rows. |
| `app/database/adoption.py` | Modified | Updated baseline adoption target to `0002_document_rights`. |
| `app/database/migration_check.py` | Modified | Added transparent alias remapping for legacy long revision identifier. |
| `alembic/env.py` | Modified | Added probe connection to remap legacy long revision before migration run. |
| `docs/CONTENT_RIGHTS_AND_ATTRIBUTION.md` | Added | Comprehensive guide covering rights policy, third-party rules, transition workflow, and marketplace listing rules. |
| `docs/HANDOFF_TO_MITHRA.md` | Added | Dedicated review handoff document for Mithra. |
| `candidate_report_CIAPI-L004.md` | Added | Formal repository candidate report following `CONTRIBUTING.md:67`. |
| `scripts/audit_rights_acceptance.py` | Added | Deterministic CLI audit tool checking L004 acceptance criteria and blockers. |
| `tests/test_document_rights.py` | Added | Comprehensive test suite for all 20 L004 requirements (22 tests including populated transition). |
| `tests/test_migrations.py` | Modified | Updated expected baseline row count to 203 and added legacy revision remapping tests (24 tests). |

---

## 6. Open Acceptance Blockers & Owner Next Steps

### Open Blockers:
1. **Manual Owner Review Pending**: All 32 candidate documents have rights evidence collected, but require formal owner review timestamp (`rights_reviewed_at`) and decision owner signature (`rights_reviewer`) by Prakash.
2. **WHO Commercial Permission**: All 4 WHO documents remain `PERMISSION_PENDING` with permission `REQUIRED_NOT_SUBMITTED`. Formal permission request must be transmitted to WHO permissions committee before commercial API syndication is permitted.

### Action Plan for Prakash to Close Acceptance:
1. Inspect each candidate URL on the live web for third-party clinical illustrations or copyrighted summaries.
2. Use `record_owner_rights_review(url, reviewer='Jaya Prakash Merepala', reviewed_at=datetime.utcnow(), db=session, commit=True, ...)` to record review decisions durably in the database.
3. Transmit permission inquiry to WHO permissions committee for WHO fact sheets.
4. For existing populated databases, execute `python scripts/transition_l004.py` rather than reseeding.
