# 📋 CIAPI-L004: Formal Handoff & Candidate Review for Mithra

**Task:** CIAPI-L004 — Resolve Document Reuse Rights and Quarantine Unresolved Material  
**Repository:** `Prakash-Merepala/CancerInfo-API`  
**New Branch:** `CIAPI-L004-resolve-document-reuse-rights-and-quarantine`  
**Base Branch:** `CIAPI-L003-postgresql-migrations-controlled-initialization`  
**Base Commit SHA:** `eb06f15714cb2f54a85661d914d7a86f76c5b527`  
**Reviewer:** **Mithra**  
**Author / Engineering Assistant:** Antigravity  

---

## 1. Executive Summary for Mithra

CIAPI-L004 transitions CancerInfo API from source-level clearance assumptions to an **authoritative, fail-closed, document-level rights architecture**.

### Why This Work Was Required
Previously, the system treated source-level metadata (such as an organization having `license_status = "APPROVED"` or `trust_tier = "Tier 1"`) as if it cleared every individual webpage, diagram, and fact sheet published by that body. This created significant legal and clinical risk because:
1. Public health portals frequently embed licensed third-party diagrams, photography, and clinical consortium tables under restrictive licenses.
2. Intergovernmental organizations like the World Health Organization publish fact sheets under Creative Commons Non-Commercial (`CC BY-NC-SA 3.0 IGO`) licenses that are legally incompatible with open/commercial API syndication without written agreements.
3. Crown copyright materials (UK NHS, Cancer Australia) explicitly exclude third-party assets and state-level clinical carve-outs.

### Core Guarantees Delivered
- **Fail-Closed Default**: Every newly discovered or seeded document defaults strictly to `publication_status = "REVIEW_REQUIRED"` (`is_publication_eligible() == False`).
- **Zero Unverified Clearances**: **0 of 32 candidate URLs** are marked `ELIGIBLE`. All 32 remain quarantined or in review pending Prakash's manual audit.
- **Relational Consensus Citation Linkage**: Every `ConsensusFactSource` now links via foreign key `source_document_id` to an exact `SourceDocument` row.
- **Controlled Reversible Migration**: Alembic migration `0002_document_rights_and_consensus_linkage` adds 15 rights fields to `source_documents` and the FK to `consensus_fact_sources` with verified SQLite and PostgreSQL compatibility.
- **Zero Runtime Schema Mutation**: Preserved the L003 architecture; no `create_all()` runtime calls exist.

---

## 2. Exact Candidate Document Inventory & Decision Matrix (32 URLs)

The candidate inventory comprises **32 unique URLs** across 5 health authorities:
- **20** normal scraped content URLs
- **20** consensus fact citation URLs
- **8** overlapping URLs
- **12** consensus-only URLs (promoted to dedicated `SourceDocument` records)

### Decision Breakdown
- **`ELIGIBLE`**: **0** documents
- **`PERMISSION_PENDING`**: **4** documents (All WHO fact sheets; quarantined due to CC BY-NC-SA 3.0 IGO non-commercial restrictions)
- **`REVIEW_REQUIRED`**: **28** documents (14 NCI, 9 NHS, 4 Cancer Australia, 1 CDC; fail-closed awaiting manual item-level audit)

### Complete URL Table for Mithra's Audit
| # | Source ID | Publishing Body | URL | Status | Assigned Quarantine Reason |
|---|---|---|---|---|---|
| 1 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded illustrations, photography, and third-party clinical media. |
| 2 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded illustrations and third-party clinical media. |
| 3 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/breast/treatment` | `REVIEW_REQUIRED` | Awaiting exact-document verification of clinical study tables and proprietary drug references. |
| 4 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/cervical/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded anatomical diagrams. |
| 5 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/cervical/screening` | `REVIEW_REQUIRED` | Awaiting item-level rights audit; screening guidelines may reference joint proprietary consensus tables. |
| 6 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/colorectal` | `REVIEW_REQUIRED` | Awaiting exact-document audit for medical diagrams and patient photography releases. |
| 7 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/colorectal/screening` | `REVIEW_REQUIRED` | Colorectal screening recommendations may cite proprietary USPSTF or clinical consortium evidence tables. |
| 8 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/lung` | `REVIEW_REQUIRED` | Awaiting exact-document audit for embedded clinical illustrations and third-party infographics. |
| 9 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/lung/symptoms` | `REVIEW_REQUIRED` | Awaiting exact-document audit for symptom presentation diagrams. |
| 10 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/skin` | `REVIEW_REQUIRED` | Awaiting exact-document verification for clinical dermatological photography and ABCDE guide illustrations. |
| 11 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/prostate` | `REVIEW_REQUIRED` | Consensus citation; awaiting item-level audit of prostate overview and anatomical diagrams. |
| 12 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/prostate/symptoms` | `REVIEW_REQUIRED` | Consensus citation; awaiting item-level audit of urinary symptom guides. |
| 13 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/prostate/screening` | `REVIEW_REQUIRED` | Consensus citation; PSA screening guideline may incorporate copyrighted clinical decision algorithms. |
| 14 | `nci-us` | National Cancer Institute | `https://www.cancer.gov/types/skin/symptoms` | `REVIEW_REQUIRED` | Consensus citation; melanoma clinical pictures must be confirmed public domain vs licensed medical photography. |
| 15 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/breast-cancer/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 text vs third-party images and trust photography. |
| 16 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/breast-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 terms and confirmation that medical diagrams are excluded. |
| 17 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/bowel-cancer/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 coverage on patient staging descriptions. |
| 18 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/bowel-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 compliance for symptom text. |
| 19 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/lung-cancer/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 terms and removal of NHS trust-specific media. |
| 20 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/lung-cancer/symptoms/` | `REVIEW_REQUIRED` | Awaiting exact-document verification of OGL v3.0 text terms and attribution requirements. |
| 21 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/cervical-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation; awaiting exact-document confirmation of OGL v3.0 compliance. |
| 22 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/cervical-screening/` | `REVIEW_REQUIRED` | Consensus citation; cervical screening guidelines require verification of NHS OGL v3.0 coverage. |
| 23 | `nhs-uk` | National Health Service | `https://www.nhs.uk/conditions/prostate-cancer/symptoms/` | `REVIEW_REQUIRED` | Consensus citation; awaiting exact-document confirmation of OGL v3.0 compliance. |
| 24 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/breast-cancer` | `PERMISSION_PENDING` | WHO CC BY-NC-SA 3.0 IGO non-commercial restriction and redistribution conditions are unresolved for public/commercial API consumption. A free API cannot be presumed non-commercial. Written permission or commercial waiver required. |
| 25 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/cancer` | `PERMISSION_PENDING` | Consensus citation; WHO CC BY-NC-SA 3.0 IGO non-commercial license restriction prevents public/commercial API redistribution without written permission. |
| 26 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/cervical-cancer` | `PERMISSION_PENDING` | Consensus citation; WHO CC BY-NC-SA 3.0 IGO non-commercial license restriction prevents public/commercial API redistribution without written permission. |
| 27 | `who-global` | World Health Organization | `https://www.who.int/news-room/fact-sheets/detail/lung-cancer` | `PERMISSION_PENDING` | WHO CC BY-NC-SA 3.0 IGO non-commercial restriction prevents public/commercial API redistribution without written permission. |
| 28 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/bowel-cancer/symptoms` | `REVIEW_REQUIRED` | Source-level CC BY 4.0 label cannot be used as automatic blanket clearance. Exact documents remain non-publication-eligible until individual page review verifies absence of third-party restrictions or Crown copyright carve-outs. |
| 29 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/lung-cancer/symptoms` | `REVIEW_REQUIRED` | Consensus citation; source-level CC BY 4.0 is unverified for this exact document. Item-level audit required under Crown copyright. |
| 30 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/affected-cancer/cancer-types/melanoma/symptoms` | `REVIEW_REQUIRED` | Consensus citation; high probability of third-party clinical copyright on dermatological symptoms and illustrations under Commonwealth Crown copyright and CC BY 4.0 conditions. |
| 31 | `cancer-australia` | Cancer Australia | `https://www.canceraustralia.gov.au/cancer-types/breast-cancer/screening` | `REVIEW_REQUIRED` | Awaiting exact-document verification of multi-jurisdictional program recommendations under Commonwealth Crown copyright and CC BY 4.0 terms. |
| 32 | `cdc-us` | Centers for Disease Control | `https://www.cdc.gov/cancer/colorectal/basic_info/screening/` | `REVIEW_REQUIRED` | CDC public domain policy specifically excludes third-party materials, campaign partner assets, and copyrighted photos. Exact page must be audited. |

---

## 3. Schema & Data Impact

1. **Alembic Migration (`alembic/versions/0002_document_rights_and_consensus_linkage.py`)**:
   - Upstream revision: `0001_initial_schema`.
   - Uses `op.batch_alter_table` for portability across SQLite and PostgreSQL.
   - Added to `source_documents`:
     `publication_status` (server_default='REVIEW_REQUIRED', nullable=False, indexed),
     `rights_evidence_url`, `rights_reviewed_at`, `rights_reviewer`, `permissible_use`,
     `commercial_redistribution_allowed`, `redistribution_allowed`, `full_text_storage_allowed`,
     `derived_summary_allowed`, `attribution_required`, `attribution_text`, `reuse_restrictions`,
     `quarantine_reason`, `third_party_permission_status`, `third_party_permission_notes`.
   - Added to `consensus_fact_sources`:
     `source_document_id` (`String(36)`, ForeignKey to `source_documents.id`, indexed, nullable=True).

2. **Baseline Database Population**:
   - Total rows increased from **191 to 203** to account for the 12 consensus-only `SourceDocument` rows.
   - Table breakdown: Sources: 5, SourceHealth: 5, Cancers: 7, CancerAliases: 22, SourceDocuments: 32 (20 content + 12 consensus), ContentRecords: 21, ContentSources: 21, ContentVersions: 21, ConsensusFacts: 21, ConsensusFactSources: 48. Total = 203.

---

## 4. Verification & Test Evidence

The entire automated test suite has executed with **100% pass rate (88 of 88 passed)**:

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.16, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/prakash/VS Code/CancerInfo-API
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

### Specific Sub-Suites of Note:
- **`tests/test_document_rights.py` (14 passed)**: Verifies all 20 acceptance criteria, including fail-closed defaults, WHO quarantine, Cancer Australia and CDC item-level requirements, consensus citation foreign-key linkage, duplicate citation prevention, quote snippet preservation, consumer schema mapping, and migration upgrade/downgrade delta.
- **`tests/test_bootstrap.py` (10 passed)**: Verifies 203 baseline rows, rollback safety, and idempotency.
- **`tests/test_migrations.py` (23 passed)**: Verifies migration upgrade, downgrade, zero schema drift against `Base.metadata`, and unversioned adoption parity.

---

## 5. Audit & Action Checklist for Mithra

| Check | Item | Status |
|---|---|---|
| 🔍 | Verify no document is marked `ELIGIBLE` without written audit record | Verified: 0/32 are `ELIGIBLE` |
| 🔍 | Verify WHO fact sheets are quarantined for commercial API distribution | Verified: 4/4 WHO are `PERMISSION_PENDING` |
| 🔍 | Verify Cancer Australia & CDC documents require item-level review | Verified: All 5 are `REVIEW_REQUIRED` |
| 🔍 | Verify all consensus fact citations link to exact `SourceDocument` | Verified: 48/48 citations linked via FK |
| 🔍 | Verify quotation snippets (50–250 chars) and attributions preserved | Verified |
| 🔍 | Verify zero `create_all()` runtime database calls | Verified |
| 🔍 | Verify working tree remains uncommitted per task rules | Verified |

---

## 6. Associated Documentation Files

- **Architecture, Policy & Operational Transition**:  
  [`docs/CONTENT_RIGHTS_AND_ATTRIBUTION.md`](file:///Users/prakash/VS%20Code/CancerInfo-API/docs/CONTENT_RIGHTS_AND_ATTRIBUTION.md)
- **Candidate Report**:  
  [`candidate_report_CIAPI-L004.md`](file:///Users/prakash/VS%20Code/CancerInfo-API/candidate_report_CIAPI-L004.md)
- **Machine-Readable Inventory**:  
  [`app/ingestion/rights_inventory.py`](file:///Users/prakash/VS%20Code/CancerInfo-API/app/ingestion/rights_inventory.py)
