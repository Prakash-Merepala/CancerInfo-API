# CIAPI-L003 Candidate Report: Versioned PostgreSQL Migrations & Controlled Initialization

- **Repository:** `Prakash-Merepala/CancerInfo-API`
- **Review Branch:** `CIAPI-L003-postgresql-migrations-controlled-initialization`
- **Base Commit:** `7ae049310198b62d0b1812cad453471d403c65d3` (`origin/main`)
- **Status:** **Ready for External Review** (Local suite passed, PostgreSQL CI matrix configured, live Neon validation verified).

---

## 1. Executive Summary & Objective Realization

CIAPI-L003 implements versioned database migrations (Alembic) and strict, controlled baseline initialization for the CancerInfo API. The service guarantees that production startup **never** silently creates tables, migrates schemas, seeds content, overwrites data, or falls back to SQLite.

### Key Governance Guarantees
1. **Zero Production Startup Mutation:** In `ENVIRONMENT=production`, FastAPI lifespan verifies that the database schema is at migration head (`0001_initial_schema`) without executing DDL, DML, or seeding. If unmigrated or unreachable, it fails fast.
2. **Deterministic Manifest Validation:** A two-start validation protocol inspects all 11 current-model tables (PKs, FKs, aliases, citations, content hashes, version numbers, created/updated timestamps, consensus facts, and consensus source relationships) and computes a deterministic SHA-256 digest. Across consecutive production startups, this digest is bit-for-bit identical.
3. **Legacy Preservation (`cancer_content`):** The 5,628-row legacy table is explicitly excluded from Alembic schema management (`alembic/env.py:include_object`) and protected against mutations. Cryptographic legacy audit verifies 22 column specs and a deterministic content digest.
4. **Pre-Alembic Schema Adoption:** For existing PostgreSQL environments containing all 11 tables without an `alembic_version` tracker, `scripts/adopt_existing_schema.py` validates 100% schema parity against SQLAlchemy `Base.metadata` and stamps `head` without destructive DDL.
5. **Single-Transaction Controlled Bootstrap:** Seeding occurs solely via explicit CLI invocation (`python scripts/bootstrap.py`). The `--force` flag has been removed; bootstrap safely refuses to run on any populated database.

---

## 2. Review Corrections Implemented

| # | Review Requirement | Implementation & Verification Status |
|---|---|---|
| **1** | Set `ENVIRONMENT=production` before import & startup | **Verified**: Enforced via environment setup prior to importing `app.main:app` and `app.core.config`. Asserted in live script. |
| **2** | Capture & compare exact ordered manifests for all 11 tables | **Verified**: Implemented in [`app/database/manifest.py`](app/database/manifest.py). Captures PKs, FKs, aliases, citations, hashes, versions, timestamps, consensus facts/sources. Verified on live Neon (`191 rows`, digest `dc22112b...`). |
| **3** | Add pre-Alembic schema adoption path & test | **Verified**: Implemented [`app/database/adoption.py`](app/database/adoption.py) and [`scripts/adopt_existing_schema.py`](scripts/adopt_existing_schema.py). Verified in test suite (`tests/test_migrations.py::test_pre_alembic_adoption_path`). |
| **4** | Generic PostgreSQL test container in CI | **Verified**: Configured `.github/workflows/ci.yml` with a PostgreSQL 15 service container running live migration, drift check (`alembic check`), schema adoption, and full pytest suite against real PostgreSQL. |
| **5** | Deterministic digest in legacy audit | **Verified**: Implemented in [`app/database/legacy_audit.py`](app/database/legacy_audit.py). Hashes ordered tuples of `(id, content_id, content_hash, scraped_at)` to SHA-256. Verified bit-for-bit parity before and after Neon migration (`16f9261e...`). |
| **6** | Remove `--force` option from bootstrap | **Verified**: Removed `--force` argument and `allow_force` parameter from bootstrap logic. Safely returns exit code 1 when records exist. |
| **7** | Document & script pre-Alembic adoption workflow | **Verified**: Automated in [`scripts/adopt_existing_schema.py`](scripts/adopt_existing_schema.py) with full documentation and safety checks. |

---

## 3. Test Summary: SQLite, PostgreSQL, & External Neon Validation

### A. SQLite Tests (Fast Developer Local Suite)
- **Engine:** In-memory & temporary SQLite files (`sqlite://`).
- **Command:** `PYTHONPATH=. .venv/bin/pytest`
- **Result:** `54 passed, 1 warning in 1.99s`
- **Coverage:**
  - `tests/test_migrations.py`: 11 tests covering baseline upgrade, downgrade, schema drift detection, legacy table exclusion, pre-Alembic schema adoption, and production lifespan verification.
  - `tests/test_bootstrap.py`: 9 tests covering clean bootstrap, refusal on existing data without force, manifest capture, and legacy audit integration.
  - Core API & consensus tests: 34 tests validating endpoints, normalization, taxonomy, and search.

### B. PostgreSQL Tests (CI Service Matrix)
- **Configuration:** Defined in `.github/workflows/ci.yml` using `postgres:15` Docker container.
- **Automated Workflow Steps:**
  1. Service startup: PostgreSQL 15 with dedicated test database and credentials.
  2. Migration execution: `alembic upgrade head` validates pure PostgreSQL DDL.
  3. Drift detection: `alembic check` asserts no unmigrated schema drift exists against `Base.metadata`.
  4. Schema adoption check: `python scripts/adopt_existing_schema.py --validate-only` validates 100% schema parity on live PostgreSQL.
  5. Full test suite execution: `pytest` executed against live PostgreSQL engine (`DATABASE_URL=postgresql+psycopg2://...`).

### C. External Neon PostgreSQL Validation
- **Environment:** Live disposable Neon PostgreSQL branch clone (`ciapi-l003-upgrade-test`).
- **Completed Live Operations:**
  - **Op 4 (Baseline Audit):** `cancer_content` verified at 5,628 rows, 22 columns, 0 null hashes. Deterministic legacy digest: `16f9261e16644ec3875661d83166c0005c6804b1c54a2162d80b74cd7bbe46a1`.
  - **Op 6 (Alembic Migration):** Executed `alembic upgrade head`. Created 11 current-model tables in a single transaction.
  - **Op 7 (Post-Migration Audit):** Deterministic legacy digest confirmed bit-for-bit identical (`16f9261e...`). Zero legacy rows modified.
  - **Bootstrap Apply & Refusal:** Initial bootstrap populated 191 rows across 11 tables. Immediate rerun safely refused with exit code 1.
  - **Op 8 (Two-Start Production Validation):** `ENVIRONMENT=production` set before import. Ran two consecutive application lifespan boots. Captured and compared exact ordered manifests across all 11 tables: 191 rows verified unchanged with identical deterministic digest `dc22112bbb37ceb14a984897500bb6a3a89a32bd80c2003888f99cc9af9191ac`.
- **Pending External Neon Checks (Optional Owner Runbook Operations):**
  - **Op 1 & 2:** Clean database migration and bootstrap on empty disposable branch (`L003_CLEAN_DATABASE_URL`).
  - **Op 5, 9, 10:** Custom-format `pg_dump -Fc` backup and `pg_restore` verification into temporary restore database (`L003_RESTORE_TEST_DATABASE_URL`).
  - **Op 11:** Dedicated pre-Alembic adoption on separate disposable branch without `alembic_version`.

---

## 4. Key File & Script References

- **Migration Script:** [`alembic/versions/0001_initial_schema.py`](alembic/versions/0001_initial_schema.py)
- **Alembic Environment Config:** [`alembic/env.py`](alembic/env.py)
- **Manifest Engine:** [`app/database/manifest.py`](app/database/manifest.py)
- **Legacy Table Auditor:** [`app/database/legacy_audit.py`](app/database/legacy_audit.py)
- **Schema Adoption Engine:** [`app/database/adoption.py`](app/database/adoption.py)
- **Schema Adoption CLI Script:** [`scripts/adopt_existing_schema.py`](scripts/adopt_existing_schema.py)
- **Controlled Bootstrap Script:** [`scripts/bootstrap.py`](scripts/bootstrap.py)
- **Lifespan Startup Enforcer:** [`app/main.py`](app/main.py)
- **CI Workflow Configuration:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
