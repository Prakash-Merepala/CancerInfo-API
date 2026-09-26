# CIAPI-L003 Candidate Report: Versioned PostgreSQL Migrations & Controlled Initialization

- **Repository:** `Prakash-Merepala/CancerInfo-API`
- **Review Branch:** `CIAPI-L003-postgresql-migrations-controlled-initialization`
- **Base Commit:** `7ae049310198b62d0b1812cad453471d403c65d3` (`origin/main`)
- **Implementation Commit:** `d5ed5caedeeeef76af28c8de1eb6c2c4d03b84f4`
- **Status:** **Ready for Review (Candidate Refined)**

---

## 1. Executive Summary & Objective Realization

CIAPI-L003 implements versioned database migrations (Alembic) and strict, controlled baseline initialization for the CancerInfo API. The service guarantees that production startup **never** silently creates tables, migrates schemas, seeds content, overwrites data, or falls back to SQLite.

### Key Governance Guarantees
1. **Zero Production Startup Mutation:** In `ENVIRONMENT=production`, FastAPI lifespan verifies that the database schema is at migration head (`0001_initial_schema`) without executing DDL, DML, or seeding. If unmigrated or unreachable, it fails fast.
2. **Deterministic Manifest Validation:** A two-start validation protocol inspects all 11 current-model tables (PKs, FKs, aliases, citations, content hashes, version numbers, created/updated timestamps, consensus facts, and consensus source relationships) and computes a deterministic SHA-256 digest. Across consecutive production startups, this digest is bit-for-bit identical.
3. **Foreign-Key Integrity Verification:** `verify_foreign_key_integrity` explicitly verifies that 0 orphaned foreign-key records exist across all relationships in the current model.
4. **Legacy Preservation (`cancer_content`):** The 5,628-row legacy table is explicitly excluded from Alembic schema management (`alembic/env.py:include_object`) and protected against mutations. Cryptographic legacy audit verifies 22 column specs, index definitions, and a deterministic content digest across all 22 columns of all 5,628 rows. Executable CLI `scripts/audit_legacy_table.py` enables automated verification and comparison.
5. **Pre-Alembic Fail-Closed Schema Adoption:** For existing unversioned PostgreSQL environments containing all 11 tables without an `alembic_version` tracker, `scripts/adopt_existing_schema.py` and `app/database/adoption.py` validate 100% schema parity (types, bidirectional nullability, extra/missing columns, PKs, ordered FK mappings, unique constraints, and index uniqueness) against SQLAlchemy `Base.metadata` and stamp the pinned `0001_initial_schema` baseline without destructive DDL. Databases with any drift or already-managed versions fail closed.
6. **Safe Credential & URL Handling:** Alembic configuration safely handles percent-encoded credentials (`set_alembic_url_safe` escaping `%` as `%%`) preventing ConfigParser interpolation syntax errors, while unmasked credentials are used internally without logging secrets.
7. **Single-Transaction Controlled Bootstrap:** Seeding occurs solely via explicit CLI invocation (`python scripts/bootstrap.py`). The `--force` flag has been removed; bootstrap safely refuses to run on any populated database.

---

## 2. Review Corrections Implemented

| # | Review Requirement | Implementation & Verification Status |
|---|---|---|
| **1** | Complete fail-closed schema adoption with comprehensive parity check | **Fixed**: `verify_schema_parity` checks all 11 tables across column presence, unexpected extra columns, type affinity, bidirectional nullability (NOT NULL vs NULLABLE), primary keys, exact ordered foreign-key mappings, unique constraints, and index uniqueness. Refuses and does not stamp if drift is detected or if `alembic_version` already exists. Added `test_adoption_negative_drift_cases` covering missing table, extra column, missing column, type mismatch, and nullability mismatch. |
| **2** | Safe URL handling for percent-encoded credentials | **Fixed**: Added `set_alembic_url_safe` in `app/database/migration_check.py` and applied across `alembic/env.py` and `app/database/adoption.py` to escape `%` as `%%`, eliminating ConfigParser `InterpolationSyntaxError`. Added regression test `test_percent_encoded_credentials_url_handling` validating passwords containing `@`, `%`, `#`. |
| **3** | Populated baseline, failing CLI result, transactional rollback & true backup recovery | **Fixed**: `test_migration_failure_and_recovery` upgraded to populate 191 baseline rows, capture baseline manifest, create pre-migration backup, execute upgrade via CLI subprocess with isolated faulty revision to prove nonzero exit code, prove transactional rollback to `0001_initial_schema`, restore pre-migration backup, and prove bit-for-bit manifest match with zero data loss. |
| **4** | 22-column legacy table cryptographic audit & dedicated audit CLI | **Fixed**: `audit_legacy_cancer_content` computes a deterministic SHA-256 digest across all 22 columns of all 5,628 rows. Created `scripts/audit_legacy_table.py` CLI supporting audit extraction and bit-for-bit baseline comparison. Clarified earlier 4-field Neon audit as historical context. |
| **5** | Isolate PostgreSQL test fixtures from bootstrap CLI smoke DB | **Fixed**: In `.github/workflows/ci.yml`, created a dedicated `cancerinfo_pytest` database for pytest execution, leaving `cancerinfo_test` pristine for the bootstrap CLI smoke tests. Added `assert_safe_test_database` safeguards blocking destructive resets on remote/cloud hosts. |
| **6** | Precise classification of verified vs. pending external acceptance checks | **Fixed**: Explicitly separated completed local/CI validations from pending owner-run Neon acceptance checks, providing exact copy-paste commands and verification steps using environment variables without hardcoded secrets. |

---

## 3. Test Summary: SQLite, PostgreSQL CI, & External Neon Validation

### A. Local Developer Suite (SQLite)
- **Engine:** In-memory & temporary SQLite files (`sqlite://`).
- **Command:** `PYTHONPATH=. .venv/bin/pytest`
- **Result:** `56 passed, 1 warning in 2.41s`
- **Coverage:**
  - `tests/test_migrations.py` (13 tests):
    1. Alembic baseline upgrade to head (`0001_initial_schema`).
    2. Alembic downgrade to base.
    3. Production lifespan verification at head.
    4. Production lifespan refusal if database unmigrated.
    5. Production lifespan refusal if SQLite configured in production.
    6. Legacy table exclusion from autogenerated migrations.
    7. Model-to-migration metadata drift check.
    8. Pre-Alembic schema adoption on unversioned database.
    9. Pre-Alembic schema adoption refusal on already-versioned database (fail closed).
    10. Pre-Alembic schema adoption negative drift tests (missing table, extra col, missing col, type mismatch, nullability mismatch).
    11. Percent-encoded credentials URL handling regression test.
    12. Controlled migration failure, CLI exit code, transactional rollback, and backup recovery test.
    13. Clean database lifespan failure when tables missing.
  - `tests/test_bootstrap.py` (9 tests):
    1. Baseline bootstrap execution (191 rows across 11 tables).
    2. Bootstrap idempotency and refusal on populated database.
    3. Dry-run validation mode without writes.
    4. Mid-write failure and complete transaction rollback.
    5. Safe database protection assert (blocks cloud/remote execution).
    6. Two-start production restart ordered manifest bit-for-bit comparison.
    7. Foreign-key integrity check across all 11 tables (0 orphans).
    8. Missing dependency failure handling.
    9. Custom bootstrap logging and masking verification.
  - Core API & consensus tests: 34 tests validating endpoints, normalization, taxonomy, and search.

### B. Automated PostgreSQL CI Matrix
- **Configuration:** Defined in `.github/workflows/ci.yml` using `postgres:15` service container.
- **Dedicated Test DB Isolation:**
  - `cancerinfo_pytest`: Isolated database created at job start for pytest execution (`POSTGRES_TEST_URL`).
  - `cancerinfo_test`: Pristine database reserved strictly for the bootstrap CLI smoke test (`DATABASE_URL`).
- **Workflow Steps:**
  1. Service startup & health probe check.
  2. Setup Python 3.11 from `.python-version`.
  3. Install dependencies from committed reproducible lock.
  4. Dependency graph check (`pip check`).
  5. Pytest suite against SQLite (`56 passed`).
  6. Dedicated database creation: `CREATE DATABASE cancerinfo_pytest;`.
  7. Pytest migration & bootstrap suite against live PostgreSQL (`cancerinfo_pytest`).
  8. OpenAPI schema smoke test.
  9. PostgreSQL migration, drift check (`alembic check`), and bootstrap CLI lifecycle against `cancerinfo_test`.
  10. Docker container portability & durability validation (`scripts/validate_container.sh`).

### C. Live Neon PostgreSQL Validation Status
- **Historical Baseline Inspection (Disposable Clone):**
  - Database: `neondb`, schema: `public`, table: `cancer_content` (5,628 rows, 22 columns).
  - Previously confirmed: Alembic baseline migration created 11 tables; legacy table remained intact; bootstrap populated 191 rows; production lifespan two-start manifest matched identically.
- **Current Refined Audit Tooling:**
  - `scripts/audit_legacy_table.py` now implements the complete 22-column cryptographic digest.

---

## 4. Explicitly Pending External Neon Operations (Owner Runbook)

The following acceptance checks require owner access to Neon branches / credentials and remain explicitly pending external execution:

### Check 1: Clean Database Migration & Serving (`L003_CLEAN_DATABASE_URL`)
On a disposable empty branch created without parent data:
```bash
# 1. Upgrade schema to head
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${CLEAN_BRANCH_HOST}/neondb?sslmode=require" alembic upgrade head

# 2. Apply baseline bootstrap
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${CLEAN_BRANCH_HOST}/neondb?sslmode=require" python scripts/bootstrap.py

# 3. Verify repeated bootstrap refusal
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${CLEAN_BRANCH_HOST}/neondb?sslmode=require" python scripts/bootstrap.py
# (Expected: Exits with code 1, refusal message)

# 4. Verify API boots and serves in production mode
ENVIRONMENT=production DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${CLEAN_BRANCH_HOST}/neondb?sslmode=require" uvicorn app.main:app --port 8000 &
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/cancers
kill %1
```

### Check 2: Custom-Format Dump & Restore Verification (`L003_RESTORE_TEST_DATABASE_URL`)
```bash
# 1. Take custom-format backup from migrated branch
pg_dump -Fc -d "postgresql://${NEON_USER}:${NEON_PASSWORD}@${MIGRATED_BRANCH_HOST}/neondb?sslmode=require" -f ciapi_l003_backup.dump

# 2. Restore into clean test branch
pg_restore --clean --no-owner --no-acl -d "postgresql://${NEON_USER}:${NEON_PASSWORD}@${RESTORE_BRANCH_HOST}/neondb?sslmode=require" ciapi_l003_backup.dump

# 3. Verify restored revision
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${RESTORE_BRANCH_HOST}/neondb?sslmode=require" alembic current

# 4. Verify legacy and current manifests on restored database
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${RESTORE_BRANCH_HOST}/neondb?sslmode=require" python scripts/audit_legacy_table.py
```

### Check 3: Dedicated Pre-Alembic Schema Adoption on Unversioned DB
On a disposable test database containing the 11 tables populated without `alembic_version`:
```bash
# 1. Validate parity only (dry-run)
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${UNVERSIONED_HOST}/neondb?sslmode=require" python scripts/adopt_existing_schema.py --validate-only
# (Expected: PARITY_VERIFIED_DRY_RUN, 11 tables verified)

# 2. Apply adoption (stamps head)
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${UNVERSIONED_HOST}/neondb?sslmode=require" python scripts/adopt_existing_schema.py
# (Expected: SUCCESSFULLY_ADOPTED, stamped to 0001_initial_schema)

# 3. Verify subsequent run safely refuses (fail closed)
DATABASE_URL="postgresql+psycopg2://${NEON_USER}:${NEON_PASSWORD}@${UNVERSIONED_HOST}/neondb?sslmode=require" python scripts/adopt_existing_schema.py
# (Expected: Exits with code 1, SchemaParityError: already managed)
```

---

## 5. Precise File-Change Summary (27 Files)

| File | Change Description |
|---|---|
| `alembic.ini` | Root Alembic configuration pointing to `alembic/` migration tree. |
| `alembic/README` | Alembic documentation placeholder. |
| `alembic/script.py.mako` | Migration template. |
| `alembic/env.py` | Migration runner; configures online/offline migrations, dialect conversion, safe `%` URL escaping, and excludes `cancer_content` (`include_object`). |
| `alembic/versions/0001_initial_schema.py` | Baseline migration creating all 11 current-model tables with indexes and foreign keys in a single transaction. |
| `app/api/v1/endpoints/admin.py` | Disables `/seed` endpoint in production (HTTP 403). |
| `app/core/config.py` | Normalizes database URLs (`postgresql+psycopg2`), strictly forbids SQLite in production, redacts secrets from exception strings. |
| `app/database/adoption.py` | Pre-Alembic schema adoption engine; pins `0001_initial_schema`, checks types/bidirectional nullability/PKs/ordered FKs/unique constraints/indexes, fails closed on versioned DBs, preserves unmasked credentials internally with safe URL escaping. |
| `app/database/bootstrap.py` | Controlled single-transaction bootstrap; removed `--force`, safely refuses execution if data exists. |
| `app/database/legacy_audit.py` | Legacy `cancer_content` auditor; hashes all 22 columns across all rows, compares column specs and indexes. |
| `app/database/manifest.py` | Current-model manifest engine; captures exact ordered manifests for all 11 tables, computes SHA-256 digest, verifies FK integrity (0 orphans). |
| `app/database/migration_check.py` | Inspects database schema against Alembic head revision without executing mutations; includes `set_alembic_url_safe`. |
| `app/database/session.py` | Preserves `cancerinfo.db` fallback for local dev, respects `DATABASE_URL`. |
| `app/ingestion/seed.py` | Updated `seed_database` to accept `commit=False` for caller transaction control. |
| `app/main.py` | FastAPI lifespan startup check enforcing schema verification at Alembic head in production. |
| `candidate_report_CIAPI-L003.md` | Formal candidate report documenting architecture, verification, test matrix, and pending owner checks. |
| `docs/MIGRATIONS_AND_INITIALIZATION.md` | Complete architectural documentation, schema design, and operational procedures. |
| `docs/VALIDATION_GUIDE.md` | Step-by-step runbook for all 11 validation operations. |
| `scripts/adopt_existing_schema.py` | CLI tool for safe pre-Alembic schema adoption (`--validate-only` dry run). |
| `scripts/audit_legacy_table.py` | CLI tool for legacy `cancer_content` cryptographic integrity audit and comparison. |
| `scripts/bootstrap.py` | CLI tool for controlled baseline bootstrap (`--validate-only` dry run). |
| `scripts/validate_container.sh` | Container validation script testing production mode, non-root user, and durability. |
| `tests/test_bootstrap.py` | 9 bootstrap tests; includes safe DB assertions, mid-write rollback test, unmasked credentials in two-start restart, and FK integrity check. |
| `tests/test_migrations.py` | 13 migration tests; includes safe DB assertions, unversioned adoption path with fail-closed check, 5 negative drift cases, URL escaping regression test, and CLI migration failure/backup recovery test. |
| `.github/workflows/ci.yml` | CI matrix with PostgreSQL 15 service; isolates `cancerinfo_pytest` from `cancerinfo_test`, tests migrations, drift, adoption, and test suite. |
| `Dockerfile` | Multi-stage production container configuration. |
| `README.md` | Updated developer quickstart and migration commands. |

---

## 6. GitHub Review & PR Link

- **Review Branch:** [`CIAPI-L003-postgresql-migrations-controlled-initialization`](https://github.com/Prakash-Merepala/CancerInfo-API/tree/CIAPI-L003-postgresql-migrations-controlled-initialization)
- **PR Compare URL:** [Compare `main`...`CIAPI-L003-postgresql-migrations-controlled-initialization`](https://github.com/Prakash-Merepala/CancerInfo-API/compare/main...CIAPI-L003-postgresql-migrations-controlled-initialization?expand=1)
