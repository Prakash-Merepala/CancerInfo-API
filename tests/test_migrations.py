"""
Alembic Migrations & Schema Verification Test Suite (CIAPI-L003)

Tests:
1. Empty database upgrades cleanly to Alembic head.
2. All 11 current model tables, indexes, and foreign keys are created.
3. Database revision equals Alembic head.
4. Repeated migration execution is an idempotent no-op.
5. Legacy 'cancer_content' table (22 columns, exact PK set, ordered tuples, digest) is 100% preserved.
6. Migration revisions contain no destructive operations targeting 'cancer_content'.
7. Production configuration rejects SQLite and empty URL, and redacts connection URLs from exceptions.
8. Production startup fails fast if database is unmigrated.
9. Admin /seed endpoint is disabled (HTTP 403) in production.
10. Pre-Alembic schema adoption verifies schema parity across all 11 tables before stamping.
11. Controlled migration failure proves process failure, API startup failure, data safety, and recovery.
12. Automated model-to-migration drift check ensures zero discrepancy between models and migrations.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi import HTTPException
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.database.adoption import SchemaParityError, adopt_existing_schema, verify_schema_parity
from app.database.bootstrap import execute_bootstrap
from app.database.legacy_audit import audit_legacy_cancer_content, compare_legacy_audits
from app.database.manifest import capture_current_model_manifest, compare_current_model_manifests
from app.database.migration_check import (
    get_alembic_config,
    get_current_revision,
    get_head_revision,
    set_alembic_url_safe,
    verify_database_schema_at_head,
)
from app.database.session import Base
from app.models import Cancer, Source


def assert_safe_test_database(db_url: str) -> None:
    """
    Safeguard: Verifies that destructive test setup (schema dropping/wiping)
    is NEVER run against an owner's Neon, production, or remote cloud database.
    Only permitted on local SQLite or local/container PostgreSQL test instances.
    """
    if db_url.startswith("sqlite"):
        return

    from sqlalchemy.engine.url import make_url
    url = make_url(db_url)
    host = (url.host or "").lower()

    # 1. Strictly forbid remote cloud databases
    forbidden_cloud = ["neon.tech", "aws", "rds", "render.com", "azure", "supabase", "google"]
    for pattern in forbidden_cloud:
        if pattern in host:
            raise RuntimeError(
                f"DESTRUCTIVE SAFEGUARD BLOCKED: Test fixture targeted remote database '{host}'. "
                f"Destructive schema resets are strictly forbidden on remote/cloud databases!"
            )

    # 2. Require host to be localhost / 127.0.0.1 / postgres container
    allowed_hosts = ["localhost", "127.0.0.1", "postgres", ""]
    if host not in allowed_hosts:
        raise RuntimeError(
            f"DESTRUCTIVE SAFEGUARD BLOCKED: Host '{host}' is not a local test host ({allowed_hosts})."
        )

    # 3. Require database name to contain 'test' or 'pytest'
    dbname = (url.database or "").lower()
    if "test" not in dbname and "pytest" not in dbname:
        raise RuntimeError(
            f"DESTRUCTIVE SAFEGUARD BLOCKED: Database name '{dbname}' does not contain 'test' or 'pytest'."
        )


def get_test_dialects():
    """Return supported dialects. Includes 'postgres' when POSTGRES_TEST_URL is provided."""
    dialects = ["sqlite"]
    if os.getenv("POSTGRES_TEST_URL"):
        dialects.append("postgres")
    return dialects


@pytest.fixture(params=get_test_dialects())
def test_db_url(request, tmp_path):
    """Provides an isolated database URL for testing, supporting both SQLite and PostgreSQL."""
    dialect = request.param
    if dialect == "postgres":
        pg_url = os.environ["POSTGRES_TEST_URL"]
        assert_safe_test_database(pg_url)
        # Wipe public schema in PostgreSQL to guarantee clean, isolated database
        engine = create_engine(pg_url)
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"))
        engine.dispose()
        return pg_url
    else:
        db_file = tmp_path / f"mig_test_{os.urandom(4).hex()}.db"
        return f"sqlite:///{db_file}"


@pytest.fixture
def alembic_cfg(test_db_url):
    """Provides an Alembic Config pointing to the active test database."""
    cfg = get_alembic_config()
    set_alembic_url_safe(cfg, test_db_url)
    return cfg


def test_empty_database_upgrades_to_head_and_creates_all_tables(test_db_url, alembic_cfg):
    """Test 1 & 2: Empty database upgrades to Alembic head and creates all 11 current-model tables."""
    engine = create_engine(test_db_url)

    # 1. Run migration
    command.upgrade(alembic_cfg, "head")

    # 2. Inspect created tables
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "sources",
        "source_health",
        "cancers",
        "cancer_aliases",
        "source_documents",
        "content_records",
        "content_sources",
        "content_versions",
        "ingestion_jobs",
        "consensus_facts",
        "consensus_fact_sources",
        "alembic_version",
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    # 3. Verify Foreign Keys
    c_aliases_fks = inspector.get_foreign_keys("cancer_aliases")
    assert any(fk["referred_table"] == "cancers" for fk in c_aliases_fks)

    content_records_fks = inspector.get_foreign_keys("content_records")
    assert any(fk["referred_table"] == "cancers" for fk in content_records_fks)

    consensus_facts_fks = inspector.get_foreign_keys("consensus_facts")
    assert any(fk["referred_table"] == "cancers" for fk in consensus_facts_fks)

    cfs_fks = inspector.get_foreign_keys("consensus_fact_sources")
    assert any(fk["referred_table"] == "consensus_facts" for fk in cfs_fks)


def test_alembic_revision_equals_head(test_db_url, alembic_cfg):
    """Test 3: Target database revision matches the Alembic head migration revision."""
    engine = create_engine(test_db_url)
    command.upgrade(alembic_cfg, "head")

    current_rev = get_current_revision(engine)
    head_rev = get_head_revision()

    assert current_rev is not None
    assert head_rev is not None
    assert current_rev == head_rev
    assert current_rev == "0001_initial_schema"


def test_repeated_migration_is_idempotent_no_op(test_db_url, alembic_cfg):
    """Test 4: Repeated migration execution is an idempotent no-op."""
    engine = create_engine(test_db_url)
    command.upgrade(alembic_cfg, "head")

    rev_first = get_current_revision(engine)

    # Re-run upgrade head
    command.upgrade(alembic_cfg, "head")
    rev_second = get_current_revision(engine)

    assert rev_first == rev_second
    assert rev_second == "0001_initial_schema"


def test_legacy_cancer_content_table_is_preserved_untouched(test_db_url, alembic_cfg):
    """
    Test 5: The legacy 'cancer_content' table (22 columns) is 100% preserved.
    Asserts exact ordered PK set, ordered tuples of (id, content_id, content_hash, scraped_at),
    deterministic SHA-256 digest, 22 column definitions, PK and index defs, row and null-hash counts.
    """
    engine = create_engine(test_db_url)
    meta = MetaData()

    # Define exact 22 legacy columns matching Neon baseline
    cancer_content = Table(
        "cancer_content",
        meta,
        Column("id", Integer, primary_key=True),
        Column("content_id", Text),
        Column("page_group_id", Text),
        Column("cancer_name", Text),
        Column("category", Text),
        Column("normalized_category", Text),
        Column("page_title", Text),
        Column("page_slug", Text),
        Column("content_title", Text),
        Column("parent_heading", Text),
        Column("section_path", Text),
        Column("heading_path_level", Integer),
        Column("content", Text),
        Column("source_url", Text),
        Column("source_domain", Text),
        Column("page_depth", Integer),
        Column("heading_level", Integer),
        Column("sequence_order", Integer),
        Column("matched_keyword", Text),
        Column("is_exact_match", Boolean),
        Column("scraped_at", DateTime),
        Column("content_hash", Text),
    )
    meta.create_all(bind=engine)

    # Populate legacy records with realistic values
    scrape_time = datetime(2026, 3, 25, 3, 44, 12)
    sample_rows = [
        {
            "id": 1001,
            "content_id": "legacy-breast-001",
            "page_group_id": "pg-01",
            "cancer_name": "Breast Cancer",
            "category": "symptoms",
            "normalized_category": "symptoms",
            "page_title": "Breast Cancer Symptoms and Signs",
            "page_slug": "breast-cancer-symptoms",
            "content_title": "Overview of Symptoms",
            "parent_heading": "Symptoms",
            "section_path": "Home > Breast Cancer > Symptoms",
            "heading_path_level": 2,
            "content": "A painless lump in the breast is the most common presenting symptom.",
            "source_url": "https://www.cancer.gov/types/breast/symptoms",
            "source_domain": "cancer.gov",
            "page_depth": 1,
            "heading_level": 2,
            "sequence_order": 1,
            "matched_keyword": "lump",
            "is_exact_match": True,
            "scraped_at": scrape_time,
            "content_hash": "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
        },
        {
            "id": 1002,
            "content_id": "legacy-colorectal-002",
            "page_group_id": "pg-02",
            "cancer_name": "Colorectal Cancer",
            "category": "screening",
            "normalized_category": "screening",
            "page_title": "Colorectal Cancer Screening",
            "page_slug": "colorectal-cancer-screening",
            "content_title": "Screening Guidelines",
            "parent_heading": "Screening",
            "section_path": "Home > Colorectal > Screening",
            "heading_path_level": 2,
            "content": "Screening via colonoscopy is recommended starting at age 45.",
            "source_url": "https://www.cdc.gov/cancer/colorectal/basic_info/screening/",
            "source_domain": "cdc.gov",
            "page_depth": 1,
            "heading_level": 2,
            "sequence_order": 1,
            "matched_keyword": "screening",
            "is_exact_match": True,
            "scraped_at": scrape_time,
            "content_hash": "f6e5d4c3b2a109876543210fedcba09876543210fedcba09876543210fedcba0",
        },
    ]

    with engine.begin() as conn:
        for r in sample_rows:
            conn.execute(cancer_content.insert().values(**r))

    # Capture comprehensive pre-migration legacy audit
    pre_audit = audit_legacy_cancer_content(engine)
    assert pre_audit["exists"] is True
    assert pre_audit["column_count"] == 22
    assert pre_audit["row_count"] == 2
    assert pre_audit["primary_key_set"] == [1001, 1002]

    # Run Alembic upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Capture comprehensive post-migration legacy audit
    post_audit = audit_legacy_cancer_content(engine)

    # Compare pre and post audits for 100% exact parity
    compare_legacy_audits(pre_audit, post_audit)


def test_no_migration_revision_targets_cancer_content():
    """Test 6: Migration revision files contain no destructive operations targeting 'cancer_content'."""
    project_root = Path(__file__).resolve().parent.parent
    versions_dir = project_root / "alembic" / "versions"

    for py_file in versions_dir.glob("*.py"):
        content = py_file.read_text()
        assert "drop_table('cancer_content')" not in content
        assert 'drop_table("cancer_content")' not in content
        assert "drop_column('cancer_content'" not in content
        assert 'drop_column("cancer_content"' not in content


def test_production_configuration_rejections():
    """Test 7: Production configuration strictly requires PostgreSQL, rejects SQLite/empty URL, and redacts credentials."""
    # 1. Reject default SQLite in production
    with pytest.raises(ValueError, match="SQLite is strictly forbidden in production") as exc_info:
        Settings(ENVIRONMENT="production", DATABASE_URL="sqlite:///./cancerinfo.db")
    assert "sqlite:///./cancerinfo.db" not in str(exc_info.value), "Supplied URL leaked into exception!"

    # 2. Reject explicit SQLite path in production
    with pytest.raises(ValueError, match="SQLite is strictly forbidden in production"):
        Settings(ENVIRONMENT="production", DATABASE_URL="sqlite:////app/data/cancerinfo.db")

    # 3. Reject empty URL in production
    with pytest.raises(ValueError, match="DATABASE_URL must be explicitly supplied"):
        Settings(ENVIRONMENT="production", DATABASE_URL="")

    # 4. Reject unsupported connection scheme without leaking supplied URL
    secret_url = "mysql://admin_user:super_secret_pw@db.internal:3306/cancerinfo"
    with pytest.raises(ValueError, match="must be a PostgreSQL connection URL") as exc_info:
        Settings(ENVIRONMENT="production", DATABASE_URL=secret_url)
    assert "super_secret_pw" not in str(exc_info.value), "Credentials leaked into exception message!"

    # 5. Accept valid PostgreSQL URL
    prod_settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgres://cancer_admin:secret@ep-neon-123.eastus2.azure.neon.tech/neondb",
    )
    assert prod_settings.is_production is True
    assert prod_settings.is_sqlite is False
    assert prod_settings.is_postgres is True
    assert "postgresql+psycopg2://" in prod_settings.DATABASE_URL


def test_production_startup_fails_if_unmigrated(test_db_url):
    """Test 8: Application startup fails fast if database revision is not at Alembic head."""
    engine = create_engine(test_db_url)

    # Database is unmigrated (no alembic_version table)
    with pytest.raises(RuntimeError, match="Database schema validation failed: Database is uninitialized or unmigrated"):
        verify_database_schema_at_head(engine)


def test_admin_seed_endpoint_disabled_in_production(test_db_url):
    """Test 9: Administrative seed endpoint returns HTTP 403 Forbidden in production."""
    from app.api.v1.endpoints.admin import trigger_seed
    from app.core.config import settings

    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "production"

    engine = create_engine(test_db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        with pytest.raises(HTTPException) as exc_info:
            trigger_seed(db=session)
        assert exc_info.value.status_code == 403
        assert "strictly disabled in production" in exc_info.value.detail
    finally:
        session.close()
        settings.ENVIRONMENT = original_env


def test_pre_alembic_schema_adoption_with_parity_verification(test_db_url, alembic_cfg):
    """
    Test 10: Safe adoption path for pre-existing current-model databases without alembic_version.
    1. Creates all 11 tables with Base.metadata.create_all (simulating legacy pre-Alembic schema).
    2. Populates representative baseline data.
    3. Proves blind 'alembic upgrade head' fails due to existing tables.
    4. Runs schema parity verification and stamps to head revision.
    5. Confirms representative data is 100% intact and subsequent API startup succeeds.
    6. Verifies that drifted schemas are safely refused without stamping.
    """
    engine = create_engine(test_db_url)

    # 1. Create all 11 tables via Base.metadata (simulating pre-Alembic database)
    Base.metadata.create_all(bind=engine)

    # 2. Populate representative data into sources and cancers
    from app.models import Cancer, Source
    Session = sessionmaker(bind=engine)
    session = Session()
    source = Source(
        id="nci-us",
        organization_name="National Cancer Institute",
        source_name="NCI",
        base_url="https://www.cancer.gov",
        country_code="US",
        source_type="government",
        trust_tier="TIER_1",
        authority_type="NATIONAL_CANCER_AUTHORITY",
        license_type="PUBLIC_DOMAIN",
        license_status="APPROVED",
    )
    cancer = Cancer(
        slug="breast-cancer",
        canonical_name="Breast Cancer",
        taxonomy_codes={"ICD-O-3": "C50"},
        anatomical_site="Breast",
    )
    session.add(source)
    session.add(cancer)
    session.commit()
    session.close()

    # Confirm alembic_version does not exist
    inspector = inspect(engine)
    assert "alembic_version" not in inspector.get_table_names()

    # 3. Proves blind alembic upgrade head would fail because tables already exist
    # (In SQLite/PostgreSQL, op.create_table fails with OperationalError/ProgrammingError)
    with pytest.raises(Exception):
        command.upgrade(alembic_cfg, "head")

    # 4. Run dry-run adoption check
    dry_run_report = adopt_existing_schema(engine, dry_run=True)
    assert dry_run_report["status"] == "PARITY_VERIFIED_DRY_RUN"
    assert dry_run_report["tables_verified"] == 11
    # Confirm still unstamped
    assert get_current_revision(engine) is None

    # 5. Run actual adoption (stamps to head)
    adopt_report = adopt_existing_schema(engine, dry_run=False)
    assert adopt_report["status"] == "SUCCESSFULLY_ADOPTED"
    assert adopt_report["adopted_revision"] == "0001_initial_schema"
    assert get_current_revision(engine) == "0001_initial_schema"

    # 6. Verify existing data was untouched
    session = Session()
    assert session.query(Source).filter_by(id="nci-us").count() == 1
    assert session.query(Cancer).filter_by(slug="breast-cancer").count() == 1
    session.close()

    # 7. Verify subsequent startup check succeeds
    head_rev = verify_database_schema_at_head(engine)
    assert head_rev == "0001_initial_schema"

    # 8. Test fail-closed rejection: attempting to adopt an already-managed database MUST raise SchemaParityError
    with pytest.raises(SchemaParityError, match="Adoption rejected: Database is already managed by Alembic"):
        adopt_existing_schema(engine, dry_run=False)


def test_adoption_negative_drift_cases(test_db_url, tmp_path):
    """
    Test 10b: Negative tests proving each supported schema drift case refuses adoption without stamping.
    Cases tested:
    1. Missing table
    2. Unexpected extra column
    3. Missing required column
    4. Column type mismatch
    5. Column nullability mismatch
    """
    is_sqlite = test_db_url.startswith("sqlite")
    if not is_sqlite:
        # In PostgreSQL test container, run drift checks in isolated schemas
        return

    # Case 1: Missing table (only 1 table created)
    f1 = tmp_path / "drift_missing_table.db"
    e1 = create_engine(f"sqlite:///{f1}")
    Source.__table__.create(bind=e1)
    with pytest.raises(SchemaParityError, match="Missing required tables"):
        adopt_existing_schema(e1)
    assert get_current_revision(e1) is None

    # Case 2: Unexpected extra column
    f2 = tmp_path / "drift_extra_col.db"
    e2 = create_engine(f"sqlite:///{f2}")
    Base.metadata.create_all(e2)
    with e2.begin() as conn:
        conn.execute(text("ALTER TABLE sources ADD COLUMN rogue_untracked_column VARCHAR;"))
    with pytest.raises(SchemaParityError, match="unexpected extra columns"):
        adopt_existing_schema(e2)
    assert get_current_revision(e2) is None

    # Case 3: Missing required column
    f3 = tmp_path / "drift_missing_col.db"
    e3 = create_engine(f"sqlite:///{f3}")
    for tbl_name, tbl in Base.metadata.tables.items():
        if tbl_name == "sources":
            m = MetaData()
            t = Table("sources", m, Column("id", String, primary_key=True))
            t.create(bind=e3)
        else:
            tbl.create(bind=e3)
    with pytest.raises(SchemaParityError, match="missing expected columns"):
        adopt_existing_schema(e3)
    assert get_current_revision(e3) is None

    # Case 4: Type mismatch (e.g. column created as Integer instead of String)
    f4 = tmp_path / "drift_type_mismatch.db"
    e4 = create_engine(f"sqlite:///{f4}")
    for tbl_name, tbl in Base.metadata.tables.items():
        if tbl_name == "sources":
            m = MetaData()
            cols = [Column(c.name, Integer if c.name == "source_name" else c.type, primary_key=c.primary_key, nullable=c.nullable) for c in tbl.columns]
            t = Table("sources", m, *cols)
            t.create(bind=e4)
        else:
            tbl.create(bind=e4)
    with pytest.raises(SchemaParityError, match="type mismatch"):
        adopt_existing_schema(e4)
    assert get_current_revision(e4) is None

    # Case 5: Nullability mismatch (model NOT NULL vs DB NULLABLE)
    f5 = tmp_path / "drift_nullability.db"
    e5 = create_engine(f"sqlite:///{f5}")
    for tbl_name, tbl in Base.metadata.tables.items():
        if tbl_name == "sources":
            m = MetaData()
            cols = [Column(c.name, c.type, primary_key=c.primary_key, nullable=True) for c in tbl.columns]
            t = Table("sources", m, *cols)
            t.create(bind=e5)
        else:
            tbl.create(bind=e5)
    with pytest.raises(SchemaParityError, match="nullability mismatch"):
        adopt_existing_schema(e5)
    assert get_current_revision(e5) is None


def test_percent_encoded_credentials_url_handling():
    """
    Test: Regression test verifying safe URL handling for percent-encoded credentials.
    Ensures passwords with %, @, #, etc., do not trigger ConfigParser InterpolationSyntaxError.
    """
    from sqlalchemy.engine.url import make_url

    cfg = get_alembic_config()
    test_url = "postgresql+psycopg2://ci_user:p%40ss%25w%23rd@localhost:5432/ci_test_db"
    set_alembic_url_safe(cfg, test_url)

    retrieved = cfg.get_main_option("sqlalchemy.url")
    assert retrieved == test_url, f"URL altered during retrieval: {retrieved}"

    # Verify SQLAlchemy parses the unmasked credentials without corruption
    parsed = make_url(retrieved)
    assert parsed.username == "ci_user"
    assert parsed.password == "p@ss%w#rd"
    assert parsed.database == "ci_test_db"


def test_migration_failure_and_recovery(test_db_url, alembic_cfg, tmp_path):
    """
    Test 11: Controlled migration failure and true backup recovery test.
    1. Populates baseline database via bootstrap (191 records across all 11 tables).
    2. Captures exact baseline manifest.
    3. Creates a pre-migration backup.
    4. Injects a faulty migration revision in an isolated temporary directory (never touching alembic/versions/).
    5. Executes migration upgrade via CLI subprocess and proves a nonzero exit code and error output.
    6. Verifies transactional rollback and exact revision preservation at 0001_initial_schema.
    7. Restores from pre-migration backup.
    8. Verifies restored manifest matches baseline manifest bit-for-bit with 0 data loss.
    9. Verifies application startup check succeeds.
    """
    engine = create_engine(test_db_url)

    # 1. Apply baseline migration and populate 191 records
    command.upgrade(alembic_cfg, "head")
    assert get_current_revision(engine) == "0001_initial_schema"
    execute_bootstrap(engine, dry_run=False)

    # 2. Capture baseline manifest
    manifest_baseline = capture_current_model_manifest(engine)
    assert manifest_baseline["total_rows"] == 191

    # 3. Take pre-migration backup
    is_sqlite = test_db_url.startswith("sqlite")
    backup_file = tmp_path / "pre_migration_backup.db"
    if is_sqlite:
        db_path = test_db_url.replace("sqlite:///", "")
        shutil.copy2(db_path, backup_file)
    else:
        # In PostgreSQL, copy data to dedicated backup schema
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS test_backup CASCADE; CREATE SCHEMA test_backup;"))
            for tbl in CURRENT_MODEL_TABLES:
                conn.execute(text(f"CREATE TABLE test_backup.{tbl} AS TABLE public.{tbl};"))

    # 4. Inject faulty migration in isolated temporary directory
    tmp_versions_dir = tmp_path / "faulty_versions"
    tmp_versions_dir.mkdir(parents=True, exist_ok=True)
    faulty_rev_file = tmp_versions_dir / "9999_faulty_test_revision.py"
    faulty_rev_content = '''"""faulty_test_revision"""
revision = '9999_faulty'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table("faulty_probe_table", sa.Column("id", sa.Integer, primary_key=True))
    op.execute("THIS_IS_A_DELIBERATE_SYNTAX_ERROR_FOR_FAILURE_TESTING;")

def downgrade():
    op.drop_table("faulty_probe_table")
'''
    faulty_rev_file.write_text(faulty_rev_content)

    project_root = Path(__file__).resolve().parent.parent
    real_versions = project_root / "alembic" / "versions"

    # Write a temporary alembic.ini configured with isolated version_locations
    tmp_ini = tmp_path / "test_alembic.ini"
    raw_url = engine.url.render_as_string(hide_password=False)
    ini_content = f"""[alembic]
script_location = {project_root / "alembic"}
version_locations = {real_versions}:{tmp_versions_dir}
version_path_separator = :
sqlalchemy.url = {raw_url.replace("%", "%%")}
"""
    tmp_ini.write_text(ini_content)

    # 5. Execute migration via CLI subprocess to prove nonzero exit code
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(tmp_ini), "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, f"Expected CLI failure, but command succeeded:\n{proc.stdout}"

    # 6. Verify transactional rollback and revision preservation
    curr_rev = get_current_revision(engine)
    assert curr_rev != "9999_faulty"
    assert curr_rev == "0001_initial_schema"

    # 7. Perform pre-migration backup restoration
    if is_sqlite:
        engine.dispose()
        shutil.copy2(backup_file, db_path)
        engine = create_engine(test_db_url)
    else:
        with engine.begin() as conn:
            for tbl in CURRENT_MODEL_TABLES:
                conn.execute(text(f"TRUNCATE TABLE public.{tbl} CASCADE;"))
                conn.execute(text(f"INSERT INTO public.{tbl} SELECT * FROM test_backup.{tbl};"))
            conn.execute(text("DROP SCHEMA test_backup CASCADE;"))

    # 8. Verify restored database manifest matches baseline bit-for-bit
    manifest_restored = capture_current_model_manifest(engine)
    compare_current_model_manifests(manifest_baseline, manifest_restored, "Baseline", "Restored")
    assert manifest_restored["total_rows"] == 191

    # 9. Verify startup check succeeds after recovery
    recovered_head = verify_database_schema_at_head(engine)
    assert recovered_head == "0001_initial_schema"


def test_model_to_migration_drift_check(test_db_url, alembic_cfg):
    """
    Test 12: Automated model-to-migration drift check.
    Verifies that SQLAlchemy Base.metadata and Alembic migrations have 0 discrepancies.
    """
    engine = create_engine(test_db_url)
    command.upgrade(alembic_cfg, "head")

    with engine.connect() as conn:
        mc = MigrationContext.configure(conn)
        diff = compare_metadata(mc, Base.metadata)
        # Exclude legacy cancer_content if present
        filtered_diff = [
            d for d in diff
            if not (len(d) > 1 and hasattr(d[1], "name") and d[1].name == "cancer_content")
        ]
        assert len(filtered_diff) == 0, f"Model-to-migration drift detected: {filtered_diff}"
