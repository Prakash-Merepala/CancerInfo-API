"""
Alembic Migrations & Schema Verification Test Suite (CIAPI-L003)

Tests:
1. Empty database upgrades cleanly to Alembic head.
2. All 11 current model tables, indexes, and foreign keys are created.
3. Database revision equals Alembic head.
4. Repeated migration execution is an idempotent no-op.
5. Legacy 'cancer_content' table (22 columns) is 100% preserved and untouched.
6. Migration revisions contain no destructive operations targeting 'cancer_content'.
7. Production configuration rejects SQLite and missing DATABASE_URL.
8. Production startup fails fast if database is unmigrated.
9. Admin /seed endpoint is disabled (HTTP 403) in production.
"""
import ast
import os
from datetime import datetime
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
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
from app.database.migration_check import (
    get_alembic_config,
    get_current_revision,
    get_head_revision,
    verify_database_schema_at_head,
)


@pytest.fixture
def clean_db_path(tmp_path):
    """Provides a fresh, temporary SQLite database URL for migration testing."""
    db_file = tmp_path / "migration_test.db"
    return f"sqlite:///{db_file}"


@pytest.fixture
def alembic_cfg(clean_db_path):
    """Provides an Alembic Config pointing to clean temporary database."""
    cfg = get_alembic_config()
    cfg.set_main_option("sqlalchemy.url", clean_db_path)
    return cfg


def test_empty_database_upgrades_to_head_and_creates_all_tables(clean_db_path, alembic_cfg):
    """Test 1 & 2: Empty database upgrades to Alembic head and creates all 11 current-model tables."""
    engine = create_engine(clean_db_path)

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
    assert any(fk["referred_table"] == "sources" for fk in cfs_fks)

    # 4. Verify Indexes
    cancers_indexes = {ix["name"] for ix in inspector.get_indexes("cancers")}
    assert "ix_cancers_slug" in cancers_indexes
    assert "ix_cancers_canonical_name" in cancers_indexes

    aliases_indexes = {ix["name"] for ix in inspector.get_indexes("cancer_aliases")}
    assert "ix_alias_lookup" in aliases_indexes


def test_alembic_revision_equals_head(clean_db_path, alembic_cfg):
    """Test 3: After migration, database revision equals Alembic head revision."""
    engine = create_engine(clean_db_path)
    command.upgrade(alembic_cfg, "head")

    head_rev = get_head_revision()
    current_rev = get_current_revision(engine)

    assert head_rev is not None
    assert current_rev == head_rev
    assert current_rev == "0001_initial_schema"


def test_repeated_migration_is_idempotent_no_op(clean_db_path, alembic_cfg):
    """Test 9: Running upgrade head multiple times causes no errors or duplicate schema modifications."""
    engine = create_engine(clean_db_path)

    # First upgrade
    command.upgrade(alembic_cfg, "head")
    rev1 = get_current_revision(engine)
    tables1 = inspect(engine).get_table_names()

    # Second upgrade
    command.upgrade(alembic_cfg, "head")
    rev2 = get_current_revision(engine)
    tables2 = inspect(engine).get_table_names()

    assert rev1 == rev2
    assert tables1 == tables2


def test_legacy_cancer_content_table_is_preserved_untouched(clean_db_path, alembic_cfg):
    """
    Test 4 & 16: Upgrading a database containing legacy 'cancer_content' table (22 columns)
    creates current-model tables without altering the legacy table definition, row count,
    IDs, content hashes, or timestamps.
    """
    engine = create_engine(clean_db_path)
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

    # Populate legacy records
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

    # Record baseline state of legacy table
    with engine.connect() as conn:
        pre_count = conn.execute(text("SELECT COUNT(*) FROM cancer_content")).scalar()
        pre_hashes = conn.execute(text("SELECT id, content_id, content_hash, scraped_at FROM cancer_content ORDER BY id")).fetchall()

    assert pre_count == 2

    # Run Alembic upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Verify legacy table post-migration
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "cancer_content" in tables, "Legacy table 'cancer_content' was dropped or lost!"
    assert "cancers" in tables, "New current-model table 'cancers' was not created!"

    legacy_cols = {c["name"] for c in inspector.get_columns("cancer_content")}
    assert len(legacy_cols) == 22, f"Expected 22 columns, got {len(legacy_cols)}"

    with engine.connect() as conn:
        post_count = conn.execute(text("SELECT COUNT(*) FROM cancer_content")).scalar()
        post_hashes = conn.execute(text("SELECT id, content_id, content_hash, scraped_at FROM cancer_content ORDER BY id")).fetchall()

    assert post_count == pre_count
    assert post_hashes == pre_hashes, "Legacy row data or timestamps were altered!"


def test_no_migration_revision_targets_cancer_content():
    """Test 17: Migration revision files contain no destructive operations targeting 'cancer_content'."""
    project_root = Path(__file__).resolve().parent.parent
    versions_dir = project_root / "alembic" / "versions"

    for py_file in versions_dir.glob("*.py"):
        content = py_file.read_text()
        assert "drop_table('cancer_content')" not in content
        assert 'drop_table("cancer_content")' not in content
        assert "drop_column('cancer_content'" not in content
        assert 'drop_column("cancer_content"' not in content


def test_production_configuration_rejections():
    """Test 13: Production configuration strictly requires PostgreSQL and rejects SQLite or empty URL."""
    # 1. Reject default SQLite in production
    with pytest.raises(ValueError, match="SQLite is strictly forbidden in production"):
        Settings(ENVIRONMENT="production", DATABASE_URL="sqlite:///./cancerinfo.db")

    # 2. Reject explicit SQLite path in production
    with pytest.raises(ValueError, match="SQLite is strictly forbidden in production"):
        Settings(ENVIRONMENT="production", DATABASE_URL="sqlite:////app/data/cancerinfo.db")

    # 3. Reject empty URL in production
    with pytest.raises(ValueError, match="DATABASE_URL must be explicitly supplied"):
        Settings(ENVIRONMENT="production", DATABASE_URL="")

    # 4. Accept valid PostgreSQL URL
    prod_settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgres://cancer_admin:secret@ep-neon-123.eastus2.azure.neon.tech/neondb",
    )
    assert prod_settings.is_production is True
    assert prod_settings.is_sqlite is False
    assert prod_settings.is_postgres is True
    assert "postgresql+psycopg2://" in prod_settings.DATABASE_URL


def test_production_startup_fails_if_unmigrated(clean_db_path):
    """Test 15: Application startup fails fast if database revision is not at Alembic head."""
    engine = create_engine(clean_db_path)

    # Database is unmigrated (no alembic_version table)
    with pytest.raises(RuntimeError, match="Database schema validation failed: Database is uninitialized or unmigrated"):
        verify_database_schema_at_head(engine)


def test_admin_seed_endpoint_disabled_in_production(clean_db_path):
    """Test: Administrative seed endpoint returns HTTP 403 Forbidden in production."""
    from app.api.v1.endpoints.admin import trigger_seed
    from app.core.config import settings

    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "production"

    engine = create_engine(clean_db_path)
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
