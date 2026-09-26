# CIAPI-L003 Candidate Report: Versioned PostgreSQL Migrations & Controlled Initialization

- **Repository:** `Prakash-Merepala/CancerInfo-API`
- **Review Branch:** `CIAPI-L003-postgresql-migrations-controlled-initialization`
- **Base Commit:** `7ae049310198b62d0b1812cad453471d403c65d3` (`origin/main`)
- **Status:** **Ready for Review (Candidate Refined)**

---

## 1. Executive Summary & Objective Realization

CIAPI-L003 implements versioned database migrations (Alembic) and strict, controlled baseline initialization for the CancerInfo API. The service guarantees that production startup **never** silently creates tables, migrates schemas, seeds content, overwrites data, or falls back to SQLite.

### Key Governance Guarantees
1. **Zero Production Startup Mutation:** In `ENVIRONMENT=production`, FastAPI lifespan verifies that the database schema is at migration head (`0001_initial_schema`) without executing DDL, DML, or seeding. If unmigrated or unreachable, it fails fast.
2. **Deterministic Manifest Validation:** A two-start validation protocol inspects all 11 current-model tables (PKs, FKs, aliases, citations, content hashes, version numbers, created/updated timestamps, consensus facts, and consensus source relationships) and computes a deterministic SHA-256 digest. Across consecutive production startups, this digest is bit-for-bit identical.
3. **Legacy Preservation (`cancer_content`):** The 5,628-row legacy table is explicitly excluded from Alembic schema management (`alembic/env.py:include_object`) and protected against mutations. Cryptographic legacy audit verifies 22 column specs, index definitions, and a deterministic content digest across all rows.
4. **Pre-Alembic Schema Adoption:** For existing unversioned PostgreSQL environments containing all 11 tables without an `alembic_version` tracker, `scripts/adopt_existing_schema.py` validates 100% schema parity (types, nullability, PKs, FKs, unique constraints, and indexes) against SQLAlchemy `Base.metadata` and stamps the pinned `0001_initial_schema` baseline without destructive DDL. Already-versioned databases fail closed.
5. **Single-Transaction Controlled Bootstrap:** Seeding occurs solely via explicit CLI invocation (`python scripts/bootstrap.py`). The `--force` flag has been removed; bootstrap safely refuses to run on any populated database.

---

## 2. Review Corrections Implemented

| # | Review Requirement | Implementation & Verification Status |
|---|---|---|
| **1** | Fix credential handling in adoption and production-restart test | **Fixed**: Replaced `str(engine.url)` with `engine.url.render_as_string(hide_password=False)` in `app/database/adoption.py` and `tests/test_bootstrap.py`. Preserves credentials internally without masking them to `***`, eliminating password-authentication failures. Sanitized masked URLs for logging. |
| **2** | Make adoption fail closed with full parity check | **Fixed**: Pinned baseline revision to `0001_initial_schema`. Rejects any database already containing an `alembic_version`. `verify_schema_parity` checks all 11 tables across column presence, type affinity, nullability, defaults, primary keys, foreign keys, and indexes. |
| **3** | Isolate PostgreSQL test fixtures from bootstrap CLI smoke DB | **Fixed**: In `.github/workflows/ci.yml`, created a dedicated `cancerinfo_pytest` database for pytest execution, leaving `cancerinfo_test` pristine for the bootstrap CLI smoke tests. Added `assert_safe_test_database` safeguards blocking destructive resets on remote/cloud hosts. |
| **4** | Strengthen failure tests with mid-write rollback & isolated migrations | **Fixed**: `test_simulated_bootstrap_failure_rolls_back_completely` now performs actual writes into the transaction before simulating an error, proving complete rollback to 0 rows. `test_migration_failure_and_recovery` isolates faulty revisions in a temporary directory via `version_locations`, demonstrating nonzero command failure and clean recovery without touching the repository. |
| **5** | Complete preservation & foreign-key integrity verification | **Fixed**: `audit_legacy_cancer_content` now includes all 22 column values in the deterministic SHA-256 data digest and asserts that legacy index definitions are identical. Added `verify_foreign_key_integrity` to `app/database/manifest.py` to assert zero orphan foreign-key records across all 11 tables. |
| **6** | Precise classification of verified vs. pending external acceptance checks | **Fixed**: Explicitly separated completed validations from pending owner-run Neon acceptance checks, providing exact copy-paste commands and verification steps without misrepresenting required checks as optional. |

---

## 3. Test Summary: SQLite, PostgreSQL CI, & External Neon Validation

### A. Local Developer Suite (SQLite)
- **Engine:** In-memory & temporary SQLite files (`sqlite://`).
- **Command:** `PYTHONPATH=. .venv/bin/pytest`
- **Result:** `54 passed, 1 warning in 2.15s`
- **Coverage:**
  - `tests/test_migrations.py` (11 tests): Alembic baseline upgrade, downgrade, drift detection, legacy exclusion, unversioned pre-Alembic schema adoption with fail-closed rejection, isolated migration failure & recovery, and production lifespan verification.
  - `tests/test_bootstrap.py` (9 tests): Baseline data creation (191 rows), duplicate prevention/refusal without force, mid-write failure rollback, validate-only dry run, two-start production restart manifest comparison, and foreign-key integrity.
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
  5. Pytest suite against SQLite (`54 passed`).
  6. Dedicated database creation: `CREATE DATABASE cancerinfo_pytest;`.
  7. Pytest migration & bootstrap suite against live PostgreSQL (`cancerinfo_pytest`).
  8. OpenAPI schema smoke test.
  9. PostgreSQL migration, drift check (`alembic check`), and bootstrap CLI lifecycle against `cancerinfo_test`.
  10. Docker container portability & durability validation (`scripts/validate_container.sh`).

### C. Live Neon PostgreSQL Validation (Completed on Disposable Clone)
- **Branch:** `ciapi-l003-upgrade-test` (`ep-misty-wildflower-anunh6cx.c-6.us-east-1.aws.neon.tech/neondb`)
- **Completed Live Operations:**
  - **Op 4 (Baseline Audit):** `cancer_content` verified at 5,628 rows, 22 columns, 0 null hashes. Deterministic legacy digest: `16f9261e16644ec3875661d83166c0005c6804b1c54a2162d80b74cd7bbe46a1`.
  - **Op 6 (Alembic Migration):** Executed `alembic upgrade head`. Created 11 current-model tables in a single transaction.
  - **Op 7 (Post-Migration Audit):** Deterministic legacy digest confirmed bit-for-bit identical (`16f9261e...`). Zero legacy rows modified.
  - **Bootstrap Apply & Refusal:** Initial bootstrap populated 191 rows across 11 tables. Immediate rerun safely refused with exit code 1.
  - **Op 8 (Two-Start Production Validation):** `ENVIRONMENT=production` set before import. Ran two consecutive application lifespan boots. Captured and compared exact ordered manifests across all 11 tables: 191 rows verified unchanged with identical deterministic digest `dc22112bbb37ceb14a984897500bb6a3a89a32bd80c2003888f99cc9af9191ac`.
  - **Adoption Refusal on Managed DB:** Running `python scripts/adopt_existing_schema.py` safely refused with `SchemaParityError` because the database was already versioned at `0001_initial_schema`.

---

## 4. Explicitly Pending External Neon Operations (Owner Runbook)

The following acceptance checks require owner access to Neon branches / credentials and remain explicitly pending external execution:

### Check 1: Clean Database Migration & Serving (`L003_CLEAN_DATABASE_URL`)
On a disposable empty branch created without parent data:
```bash
# 1. Upgrade schema
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<clean-branch-host>/neondb?sslmode=require" alembic upgrade head

# 2. Apply baseline bootstrap
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<clean-branch-host>/neondb?sslmode=require" python scripts/bootstrap.py

# 3. Verify repeated bootstrap refusal
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<clean-branch-host>/neondb?sslmode=require" python scripts/bootstrap.py
# (Expected: Exits with code 1, refusal message)

# 4. Verify API boots and serves
ENVIRONMENT=production DATABASE_URL="postgresql+psycopg2://<user>:<password>@<clean-branch-host>/neondb?sslmode=require" uvicorn app.main:app --port 8000 &
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/cancers
kill %1
```

### Check 2: Custom-Format Dump & Restore Verification (`L003_RESTORE_TEST_DATABASE_URL`)
```bash
# 1. Take custom-format backup from migrated branch
pg_dump -Fc -d "postgresql://<user>:<password>@<migrated-branch-host>/neondb?sslmode=require" -f ciapi_l003_backup.dump

# 2. Restore into clean test branch
pg_restore --clean --no-owner --no-acl -d "postgresql://<user>:<password>@<restore-branch-host>/neondb?sslmode=require" ciapi_l003_backup.dump

# 3. Verify restored revision
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<restore-branch-host>/neondb?sslmode=require" alembic current

# 4. Verify legacy and current manifests on restored database
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<restore-branch-host>/neondb?sslmode=require" python scripts/audit_legacy_table.py
```

### Check 3: Dedicated Pre-Alembic Schema Adoption on Unversioned DB
On a disposable test database containing the 11 tables populated without `alembic_version`:
```bash
# 1. Validate parity only (dry-run)
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<unversioned-host>/neondb?sslmode=require" python scripts/adopt_existing_schema.py --validate-only
# (Expected: PARITY_VERIFIED_DRY_RUN, 11 tables verified)

# 2. Apply adoption (stamps head)
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<unversioned-host>/neondb?sslmode=require" python scripts/adopt_existing_schema.py
# (Expected: SUCCESSFULLY_ADOPTED, stamped to 0001_initial_schema)

# 3. Verify subsequent run safely refuses
DATABASE_URL="postgresql+psycopg2://<user>:<password>@<unversioned-host>/neondb?sslmode=require" python scripts/adopt_existing_schema.py
# (Expected: Exits with code 1, SchemaParityError: already managed)
```

---

## 5. Precise File-Change Summary (26 Files)

| File | Change Description |
|---|---|
| `alembic.ini` | Root Alembic configuration pointing to `alembic/` migration tree. |
| `alembic/README` | Alembic documentation placeholder. |
| `alembic/script.py.mako` | Migration template. |
| `alembic/env.py` | Migration runner; configures online/offline migrations, dialect conversion, and excludes `cancer_content` (`include_object`). |
| `alembic/versions/0001_initial_schema.py` | Baseline migration creating all 11 current-model tables with indexes and foreign keys in a single transaction. |
| `app/api/v1/endpoints/admin.py` | Disables `/seed` endpoint in production (HTTP 403). |
| `app/core/config.py` | Normalizes database URLs (`postgresql+psycopg2`), strictly forbids SQLite in production, redacts secrets from exception strings. |
| `app/database/adoption.py` | Pre-Alembic schema adoption engine; pins `0001_initial_schema`, checks types/nullability/PKs/FKs/indexes, fails closed on versioned DBs, preserves unmasked credentials internally. |
| `app/database/bootstrap.py` | Controlled single-transaction bootstrap; removed `--force`, safely refuses execution if data exists. |
| `app/database/legacy_audit.py` | Legacy `cancer_content` auditor; hashes all 22 columns across all rows, compares column specs and indexes. |
| `app/database/manifest.py` | Current-model manifest engine; captures exact ordered manifests for all 11 tables, computes SHA-256 digest, verifies FK integrity. |
| `app/database/migration_check.py` | Inspects database schema against Alembic head revision without executing mutations. |
| `app/database/session.py` | Preserves `cancerinfo.db` fallback for local dev, respects `DATABASE_URL`. |
| `app/ingestion/seed.py` | Updated `seed_database` to accept `commit=False` for caller transaction control. |
| `app/main.py` | FastAPI lifespan startup check enforcing schema verification at Alembic head in production. |
| `candidate_report_CIAPI-L003.md` | Formal candidate report documenting architecture, verification, test matrix, and pending owner checks. |
| `docs/MIGRATIONS_AND_INITIALIZATION.md` | Complete architectural documentation, schema design, and operational procedures. |
| `docs/VALIDATION_GUIDE.md` | Step-by-step runbook for all 11 validation operations. |
| `scripts/adopt_existing_schema.py` | CLI tool for safe pre-Alembic schema adoption (`--validate-only` dry run). |
| `scripts/bootstrap.py` | CLI tool for controlled baseline bootstrap (`--validate-only` dry run). |
| `scripts/validate_container.sh` | Container validation script testing production mode, non-root user, and durability. |
| `tests/test_bootstrap.py` | 9 bootstrap tests; includes safe DB assertions, mid-write rollback test, unmasked credentials in two-start restart, and FK integrity check. |
| `tests/test_migrations.py` | 11 migration tests; includes safe DB assertions, unversioned adoption path with fail-closed check, and isolated migration failure test. |
| `.github/workflows/ci.yml` | CI matrix with PostgreSQL 15 service; isolates `cancerinfo_pytest` from `cancerinfo_test`, tests migrations, drift, adoption, and test suite. |
| `Dockerfile` | Multi-stage production container configuration. |
| `README.md` | Updated developer quickstart and migration commands. |

---

## 6. GitHub Review & PR Link

- **Review Branch:** [`CIAPI-L003-postgresql-migrations-controlled-initialization`](https://github.com/Prakash-Merepala/CancerInfo-API/tree/CIAPI-L003-postgresql-migrations-controlled-initialization)
- **PR Compare URL:** [Compare `main`...`CIAPI-L003-postgresql-migrations-controlled-initialization`](https://github.com/Prakash-Merepala/CancerInfo-API/compare/main...CIAPI-L003-postgresql-migrations-controlled-initialization?expand=1)
