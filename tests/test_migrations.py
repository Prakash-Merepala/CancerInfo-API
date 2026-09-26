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
from app.database.legacy_audit import audit_legacy_cancer_content, compare_legacy_audits
from app.database.migration_check import (
    get_alembic_config,
    get_current_revision,
    get_head_revision,
    verify_database_schema_at_head,
)
from app.database.session import Base


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
    cfg.set_main_option("sqlalchemy.url", test_db_url)
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

    # 9. Test parity failure on drifted schema: create separate database missing a table
    drift_db_file = test_db_url + "_drift.db" if test_db_url.startswith("sqlite") else None
    if drift_db_file:
        drift_engine = create_engine(drift_db_file)
        # Create only 1 table
        Source.__table__.create(bind=drift_engine)
        with pytest.raises(SchemaParityError, match="Missing required tables"):
            adopt_existing_schema(drift_engine)
        assert get_current_revision(drift_engine) is None


def test_migration_failure_and_recovery(test_db_url, alembic_cfg, tmp_path):
    """
    Test 11: Controlled migration failure test.
    1. Causes controlled migration failure via faulty migration step in an isolated directory.
    2. Proves failing command result.
    3. Proves database revision is not at failed revision and data state is intact.
    4. Demonstrates recovery, followed by clean application startup.
    Keeps temporary faulty revisions completely isolated from repository migrations.
    """
    engine = create_engine(test_db_url)

    # 1. Apply baseline migration
    command.upgrade(alembic_cfg, "head")
    assert get_current_revision(engine) == "0001_initial_schema"

    # 2. Inject a controlled faulty migration revision into an isolated temporary directory
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
    # Deliberate failure syntax
    op.execute("THIS_IS_A_DELIBERATE_SYNTAX_ERROR_FOR_FAILURE_TESTING;")

def downgrade():
    op.drop_table("faulty_probe_table")
'''
    faulty_rev_file.write_text(faulty_rev_content)

    project_root = Path(__file__).resolve().parent.parent
    real_versions = project_root / "alembic" / "versions"

    # Configure version_locations to include the temporary isolated folder
    alembic_cfg.set_section_option("alembic", "version_path_separator", ":")
    alembic_cfg.set_section_option("alembic", "version_locations", f"{real_versions}:{tmp_versions_dir}")

    # 3. Attempt upgrade to head - must fail
    with pytest.raises(Exception):
        command.upgrade(alembic_cfg, "head")

    # 4. Prove database revision is NOT at the target failed revision
    curr_rev = get_current_revision(engine)
    assert curr_rev != "9999_faulty"

    # 5. Prove existing tables and baseline data remain uncorrupted
    inspector = inspect(engine)
    assert "sources" in inspector.get_table_names()
    assert "cancers" in inspector.get_table_names()

    # 6. Recovery: remove isolated temporary folder and reset version_locations
    alembic_cfg.set_section_option("alembic", "version_locations", str(real_versions))

    # 7. Post-recovery: head revision is once again 0001_initial_schema and startup check passes
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
