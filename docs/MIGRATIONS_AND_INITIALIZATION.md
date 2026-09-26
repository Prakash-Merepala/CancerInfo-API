# Database Migrations, Controlled Initialization & Production Operations Guide (CIAPI-L003)

This document establishes the authoritative operational runbook for database migrations, baseline bootstrap, and schema lifecycle management across Neon PostgreSQL and Render hosting.

---

## 1. Architectural Principles

1. **Explicit, Controlled Schema Evolution**:
   - Production startup **never** silently creates tables, runs migrations, or seeds records.
   - All schema changes must be versioned through reviewed Alembic migration scripts in `alembic/versions/`.
   - FastAPI application startup validates that the database is at Alembic head revision and aborts startup immediately if unmigrated or outdated.

2. **Strict Legacy Preservation**:
   - The production database contains a legacy `cancer_content` table (5,628 rows, 22 columns).
   - Migration `0001_initial_schema` creates the 11 current-model tables alongside `cancer_content`.
   - Alembic autogenerate explicitly excludes `cancer_content` (`include_object` filter in `alembic/env.py`).
   - Legacy data is never dropped, truncated, altered, or silently rewritten.

3. **Controlled, Transactional Bootstrap**:
   - Automatic seeding is replaced by `scripts/bootstrap.py`.
   - Bootstrap requires deliberate execution, refuses already-populated current-model databases by default, runs in a single atomic transaction, and rolls back completely on any failure.
   - Non-mutating validation is supported via `python scripts/bootstrap.py --validate-only`.

4. **Production Configuration Requirements**:
   - `ENVIRONMENT=production` strictly enforces:
     - `DATABASE_URL` must be a valid PostgreSQL connection string (`postgresql://` or `postgresql+psycopg2://`).
     - SQLite is strictly rejected (`ValueError` on startup).
     - Missing or empty `DATABASE_URL` is strictly rejected.
     - Administrative seed endpoint (`POST /v1/admin/seed`) is disabled with HTTP 403 Forbidden.

5. **Connection Pooling Architecture (Neon)**:
   - **Direct Connection** (`ep-xyz.eastus2.azure.neon.tech`): Used for migrations (`alembic upgrade head`), backups (`pg_dump`), and restores (`pg_restore`). Direct connections bypass transaction-mode pooling to support DDL locking and long-running utility operations.
   - **Pooled Connection** (`ep-xyz-pooler.eastus2.azure.neon.tech`): Used for normal API runtime traffic (`DATABASE_URL`). Managed by Neon's PgBouncer in transaction pooling mode.
   - Connection pool sizing in `app/core/config.py` defaults to conservative limits (`DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`, `pool_pre_ping=True`, `pool_recycle=1800`) to prevent connection pool exhaustion across multiple web workers.

---

## 2. Owner Manual Validation Runbook (Neon Disposable Targets)

The owner has prepared four isolated, disposable Neon connection strings stored securely as environment variables:
- `L003_CLEAN_DATABASE_URL`: Completely empty database (0 public tables).
- `L003_DEV_DATABASE_URL`: Development and staging database.
- `L003_UPGRADE_TEST_DATABASE_URL`: Contains verified legacy `cancer_content` table (5,628 rows).
- `L003_RESTORE_TEST_DATABASE_URL`: Clean database reserved for backup restore verification.

> [!CAUTION]
> Never print or log connection strings. Ensure commands execute without echoing sensitive credentials to terminal logs or shell history.

### Operation 1: Migrate Clean Database to Alembic Head
```bash
# Verify clean database starts with zero tables
DATABASE_URL="$L003_CLEAN_DATABASE_URL" python -c "
from sqlalchemy import create_engine, inspect
import os
tables = inspect(create_engine(os.environ['DATABASE_URL'])).get_table_names()
print(f'Initial tables count: {len(tables)}')
assert len(tables) == 0, f'Expected 0 tables, found {tables}'
"

# Execute Alembic migration to head revision
DATABASE_URL="$L003_CLEAN_DATABASE_URL" alembic upgrade head
```

### Operation 2: Verify Current-Model Tables & Alembic Revision
```bash
DATABASE_URL="$L003_CLEAN_DATABASE_URL" python -c "
from sqlalchemy import create_engine, inspect
from app.database.migration_check import verify_database_schema_at_head
import os

engine = create_engine(os.environ['DATABASE_URL'])
head_rev = verify_database_schema_at_head(engine)
print(f'Verified schema revision at head: {head_rev}')

tables = set(inspect(engine).get_table_names())
expected = {
    'sources', 'source_health', 'cancers', 'cancer_aliases',
    'source_documents', 'content_records', 'content_sources',
    'content_versions', 'ingestion_jobs', 'consensus_facts',
    'consensus_fact_sources', 'alembic_version'
}
assert expected.issubset(tables), f'Missing: {expected - tables}'
print(f'All {len(expected)} expected tables present in clean database.')
"
```

### Operation 3: Execute Controlled Bootstrap Against Clean Database
```bash
# First test validate-only dry-run mode (no records created)
DATABASE_URL="$L003_CLEAN_DATABASE_URL" python scripts/bootstrap.py --validate-only

# Execute transactional bootstrap
DATABASE_URL="$L003_CLEAN_DATABASE_URL" python scripts/bootstrap.py

# Verify safety refusal on repeated invocation (must fail with exit code 1)
if DATABASE_URL="$L003_CLEAN_DATABASE_URL" python scripts/bootstrap.py; then
    echo 'FAILED: Repeated bootstrap should have refused!'
    exit 1
else
    echo 'PASSED: Repeated bootstrap refused safely.'
fi
```

### Operation 4: Capture Non-Content Baseline Manifest from Upgrade-Test Database
```bash
DATABASE_URL="$L003_UPGRADE_TEST_DATABASE_URL" python -c "
from sqlalchemy import create_engine, text
import json, os

engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    row_count = conn.execute(text('SELECT COUNT(*) FROM cancer_content')).scalar()
    distinct_ids = conn.execute(text('SELECT COUNT(DISTINCT content_id) FROM cancer_content')).scalar()
    distinct_hashes = conn.execute(text('SELECT COUNT(DISTINCT content_hash) FROM cancer_content')).scalar()
    earliest_scrape = conn.execute(text('SELECT MIN(scraped_at) FROM cancer_content')).scalar()
    latest_scrape = conn.execute(text('SELECT MAX(scraped_at) FROM cancer_content')).scalar()

manifest = {
    'table_name': 'cancer_content',
    'row_count': row_count,
    'distinct_content_ids': distinct_ids,
    'distinct_content_hashes': distinct_hashes,
    'earliest_scrape': str(earliest_scrape),
    'latest_scrape': str(latest_scrape),
}

with open('/tmp/upgrade_test_baseline_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print('Baseline manifest captured successfully:')
print(json.dumps(manifest, indent=2))
"
```

### Operation 5: Create Custom-Format PostgreSQL Backup of Upgrade-Test Database
```bash
# Capture custom compressed archive backup using pg_dump
pg_dump --format=custom --no-owner --no-acl "$L003_UPGRADE_TEST_DATABASE_URL" > /tmp/upgrade_test_backup.dump

echo "Backup size: $(wc -c < /tmp/upgrade_test_backup.dump) bytes"
```

### Operation 6: Run Migrations Against Upgrade-Test Without Altering Legacy Table
```bash
DATABASE_URL="$L003_UPGRADE_TEST_DATABASE_URL" alembic upgrade head
```

### Operation 7: Compare Pre-Migration and Post-Migration Legacy Manifests
```bash
DATABASE_URL="$L003_UPGRADE_TEST_DATABASE_URL" python -c "
from sqlalchemy import create_engine, text
import json, os

engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    row_count = conn.execute(text('SELECT COUNT(*) FROM cancer_content')).scalar()
    distinct_ids = conn.execute(text('SELECT COUNT(DISTINCT content_id) FROM cancer_content')).scalar()
    distinct_hashes = conn.execute(text('SELECT COUNT(DISTINCT content_hash) FROM cancer_content')).scalar()
    earliest_scrape = conn.execute(text('SELECT MIN(scraped_at) FROM cancer_content')).scalar()
    latest_scrape = conn.execute(text('SELECT MAX(scraped_at) FROM cancer_content')).scalar()

post_manifest = {
    'table_name': 'cancer_content',
    'row_count': row_count,
    'distinct_content_ids': distinct_ids,
    'distinct_content_hashes': distinct_hashes,
    'earliest_scrape': str(earliest_scrape),
    'latest_scrape': str(latest_scrape),
}

with open('/tmp/upgrade_test_baseline_manifest.json') as f:
    pre_manifest = json.load(f)

assert pre_manifest == post_manifest, f'Manifest mismatch! Pre: {pre_manifest} vs Post: {post_manifest}'
print('PASSED: Legacy cancer_content manifest is 100% identical post-migration.')
"
```

### Operation 8: Start API Twice in Production Mode & Prove Zero Mutation
```bash
DATABASE_URL="$L003_CLEAN_DATABASE_URL" python -c "
from sqlalchemy import create_engine
from app.database.bootstrap import inspect_database_state
import os, asyncio

engine = create_engine(os.environ['DATABASE_URL'])
pre_state = inspect_database_state(engine)

from app.main import lifespan, app

async def boot_app():
    async with lifespan(app):
        pass

# Run startup 1
asyncio.run(boot_app())

# Run startup 2
asyncio.run(boot_app())

post_state = inspect_database_state(engine)
assert pre_state['current_model_counts'] == post_state['current_model_counts']
print('PASSED: Starting API twice produced zero database mutations.')
"
```

### Operation 9: Restore Backup into Restore-Test Database
```bash
# Restore custom dump into clean restore-test database
pg_restore --clean --if-exists --no-owner --no-acl -d "$L003_RESTORE_TEST_DATABASE_URL" /tmp/upgrade_test_backup.dump
```

### Operation 10: Compare Restored Legacy Manifest with Original
```bash
DATABASE_URL="$L003_RESTORE_TEST_DATABASE_URL" python -c "
from sqlalchemy import create_engine, text
import json, os

engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    row_count = conn.execute(text('SELECT COUNT(*) FROM cancer_content')).scalar()
    distinct_ids = conn.execute(text('SELECT COUNT(DISTINCT content_id) FROM cancer_content')).scalar()
    distinct_hashes = conn.execute(text('SELECT COUNT(DISTINCT content_hash) FROM cancer_content')).scalar()
    earliest_scrape = conn.execute(text('SELECT MIN(scraped_at) FROM cancer_content')).scalar()
    latest_scrape = conn.execute(text('SELECT MAX(scraped_at) FROM cancer_content')).scalar()

restored_manifest = {
    'table_name': 'cancer_content',
    'row_count': row_count,
    'distinct_content_ids': distinct_ids,
    'distinct_content_hashes': distinct_hashes,
    'earliest_scrape': str(earliest_scrape),
    'latest_scrape': str(latest_scrape),
}

with open('/tmp/upgrade_test_baseline_manifest.json') as f:
    pre_manifest = json.load(f)

assert pre_manifest == restored_manifest, f'Restored manifest mismatch! Pre: {pre_manifest} vs Restored: {restored_manifest}'
print('PASSED: Restored database matches original pre-migration manifest perfectly.')
"
```

### Operation 11: Exercise Representative API & Ingestion Against Migrated PostgreSQL
```bash
# Run bootstrap on upgrade-test current-model tables
DATABASE_URL="$L003_UPGRADE_TEST_DATABASE_URL" python scripts/bootstrap.py

# Query representative consensus facts and canonical cancers
DATABASE_URL="$L003_UPGRADE_TEST_DATABASE_URL" python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Cancer, ConsensusFact
import os

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
session = Session()

cancers = session.query(Cancer).all()
print(f'Canonical Cancers in PostgreSQL: {len(cancers)}')
assert len(cancers) == 7

facts = session.query(ConsensusFact).all()
print(f'Consensus Facts in PostgreSQL: {len(facts)}')
assert len(facts) == 21

session.close()
print('PASSED: Current model tables verified operational against hosted PostgreSQL.')
"
```

### Operation 12: Recovering from an Intentionally Failed Disposable Migration
```bash
# If a migration fails mid-way, Alembic transactions in PostgreSQL will roll back the DDL transaction.
# Check current database revision:
DATABASE_URL="$L003_DEV_DATABASE_URL" alembic current

# If database is at intermediate revision, downgrade to known-good revision:
DATABASE_URL="$L003_DEV_DATABASE_URL" alembic downgrade base

# Re-apply clean migration:
DATABASE_URL="$L003_DEV_DATABASE_URL" alembic upgrade head
```

---

## 3. Render Deployment & Production Operations

### Environment Variables on Render
Set the following environment variables in the Render Dashboard:
- `ENVIRONMENT`: `production`
- `DATABASE_URL`: `postgresql+psycopg2://user:password@ep-xyz-pooler.eastus2.azure.neon.tech/neondb` (Use Neon **Pooled** connection string)
- `MIGRATION_DATABASE_URL`: `postgresql+psycopg2://user:password@ep-xyz.eastus2.azure.neon.tech/neondb` (Use Neon **Direct** connection string)
- `PORT`: `3000`
- `ADMIN_API_KEY`: `<securely-generated-uuid4-key>`

### Render Build & Pre-Deploy Configuration
1. **Build Command**:
   ```bash
   pip install --no-cache-dir --require-hashes -r requirements.txt
   ```
2. **Pre-Deploy Command** (Available on Render Starter plans and above):
   ```bash
   DATABASE_URL="$MIGRATION_DATABASE_URL" alembic upgrade head
   ```
   > [!NOTE]
   > Render executes Pre-Deploy commands using the service's build image prior to spinning up new web containers. If the pre-deploy migration command fails, Render automatically cancels the deployment, keeping the existing healthy revision live.

3. **Fallback When Pre-Deploy Commands Are Unavailable**:
   On Render Free plans where pre-deploy hooks are not supported, execute migrations manually from a secure local terminal before deploying:
   ```bash
   DATABASE_URL="<NEON_DIRECT_CONNECTION_STRING>" alembic upgrade head
   ```

4. **Web Service Start Command**:
   ```bash
   exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3000}
   ```
   The web start command starts **only** the API. It never executes `alembic` or `scripts/bootstrap.py`.
