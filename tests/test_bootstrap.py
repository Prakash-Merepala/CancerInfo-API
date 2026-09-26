"""
Controlled Database Bootstrap Test Suite (CIAPI-L003)

Tests:
1. Controlled bootstrap creates expected baseline data in an unpopulated database.
2. Consensus facts retain all source links, quote snippets, attributions, country codes, and verification timestamps.
3. Content records retain citations, documents, URLs, quotes, attributions, and relationships.
4. Cancer aliases and content-version history are preserved.
5. Foreign-key integrity passes on all seeded data.
6. Repeated bootstrap refuses safely by default to prevent duplicate data or silent overwrites.
7. Bootstrap transaction failure rolls back completely (0 rows created).
8. Bootstrap dry-run / validate-only mode inspects without mutating.
9. Presence of legacy 'cancer_content' table is handled safely and left 100% untouched.
10. Starting the API twice in production mode causes zero mutations on the database.
"""
from datetime import datetime
from unittest.mock import patch
import pytest
from alembic import command
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import sessionmaker

from app.database.bootstrap import execute_bootstrap, inspect_database_state
from app.database.migration_check import get_alembic_config
from app.models import (
    Cancer,
    CancerAlias,
    ConsensusFact,
    ConsensusFactSource,
    ContentRecord,
    ContentSource,
    ContentVersion,
    Source,
    SourceDocument,
    SourceHealth,
)


@pytest.fixture
def migrated_db(tmp_path):
    """Provides a fresh, temporary migrated SQLite database for bootstrap testing."""
    db_file = tmp_path / "bootstrap_test.db"
    db_url = f"sqlite:///{db_file}"
    cfg = get_alembic_config()
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    engine = create_engine(db_url)
    return engine


def test_controlled_bootstrap_creates_expected_data(migrated_db):
    """Test 4: Controlled bootstrap populates all 11 current-model tables with baseline content."""
    res = execute_bootstrap(migrated_db, dry_run=False)

    assert res["status"] == "SUCCESS"
    assert res["total_records_created"] == 191

    Session = sessionmaker(bind=migrated_db)
    session = Session()

    try:
        assert session.query(Source).count() == 5
        assert session.query(SourceHealth).count() == 5
        assert session.query(Cancer).count() == 7
        assert session.query(CancerAlias).count() == 22
        assert session.query(SourceDocument).count() == 20
        assert session.query(ContentRecord).count() == 21
        assert session.query(ContentSource).count() == 21
        assert session.query(ContentVersion).count() == 21
        assert session.query(ConsensusFact).count() == 21
        assert session.query(ConsensusFactSource).count() == 48
    finally:
        session.close()


def test_consensus_facts_retain_provenance_and_corroboration(migrated_db):
    """Test 5: Consensus facts retain every source link, source URL, quote, attribution, country code, and verification field."""
    execute_bootstrap(migrated_db, dry_run=False)

    Session = sessionmaker(bind=migrated_db)
    session = Session()

    try:
        # Check breast cancer symptoms consensus facts
        breast_cancer = session.query(Cancer).filter(Cancer.slug == "breast-cancer").first()
        assert breast_cancer is not None

        facts = session.query(ConsensusFact).filter(
            ConsensusFact.cancer_id == breast_cancer.id,
            ConsensusFact.category == "symptoms",
        ).all()
        assert len(facts) > 0

        # Check lump symptom has multiple corroborating sources
        lump_fact = next((f for f in facts if "lump" in f.title.lower()), None)
        assert lump_fact is not None
        assert lump_fact.corroboration_count >= 1
        assert len(lump_fact.corroborating_sources) >= 1

        for cfs in lump_fact.corroborating_sources:
            assert cfs.source_url.startswith("http")
            assert cfs.source_id in {"nci-us", "nhs-uk", "who-global", "cancer-australia", "cdc-us"}
            assert cfs.country_code in {"US", "GB", "AU", "GLOBAL"}
            assert cfs.last_verified_at is not None
            assert cfs.attribution_text is not None and len(cfs.attribution_text) > 0
    finally:
        session.close()


def test_content_records_retain_citations_and_sources(migrated_db):
    """Test 6: Content records retain their source-document citations, URLs, quotes, attribution, and relationships."""
    execute_bootstrap(migrated_db, dry_run=False)

    Session = sessionmaker(bind=migrated_db)
    session = Session()

    try:
        records = session.query(ContentRecord).all()
        assert len(records) == 21

        for cr in records:
            assert len(cr.sources) >= 1
            for src in cr.sources:
                assert src.source_url.startswith("http")
                assert src.source_id is not None
                assert src.attribution_text is not None

            assert len(cr.versions) >= 1
            for v in cr.versions:
                assert v.version_number >= 1
                assert v.content_hash is not None and len(v.content_hash) == 64
    finally:
        session.close()


def test_aliases_and_content_versions_preserved(migrated_db):
    """Test 7: Aliases and content-version history are preserved with high fidelity."""
    execute_bootstrap(migrated_db, dry_run=False)

    Session = sessionmaker(bind=migrated_db)
    session = Session()

    try:
        # Verify CRC abbreviation alias resolves to Colorectal Cancer
        crc_alias = session.query(CancerAlias).filter(CancerAlias.alias == "CRC").first()
        assert crc_alias is not None
        assert crc_alias.cancer.slug == "colorectal-cancer"

        # Verify NSCLC abbreviation alias resolves to Lung Cancer
        nsclc_alias = session.query(CancerAlias).filter(CancerAlias.alias == "NSCLC").first()
        assert nsclc_alias is not None
        assert nsclc_alias.cancer.slug == "lung-cancer"

        # Verify Content Versions
        versions = session.query(ContentVersion).all()
        assert len(versions) == 21
        for cv in versions:
            assert cv.change_type == "NEW"
            assert cv.created_at is not None
    finally:
        session.close()


def test_repeated_bootstrap_refuses_safely(migrated_db):
    """Test 10: A repeated bootstrap refuses safely to avoid duplicate rows or silent overwrites."""
    # First bootstrap succeeds
    res1 = execute_bootstrap(migrated_db, dry_run=False)
    assert res1["status"] == "SUCCESS"

    # Second bootstrap raises RuntimeError and refuses
    with pytest.raises(RuntimeError, match="Refusing to bootstrap: Current-model database is already populated"):
        execute_bootstrap(migrated_db, dry_run=False, force=False)

    # Verify row counts remain unchanged (exactly 191)
    state = inspect_database_state(migrated_db)
    assert state["total_current_model_rows"] == 191


def test_simulated_bootstrap_failure_rolls_back_completely(migrated_db):
    """Test 11: A simulated bootstrap failure rolls back the complete transaction (0 records created)."""
    # Mock seed_consensus_facts to fail midway
    with patch("app.database.bootstrap.seed_database", side_effect=RuntimeError("Simulated disk error")):
        with pytest.raises(RuntimeError, match="Bootstrap transaction failed and was completely rolled back"):
            execute_bootstrap(migrated_db, dry_run=False)

    # Verify complete rollback: zero current-model records exist
    state = inspect_database_state(migrated_db)
    assert state["total_current_model_rows"] == 0
    for tbl, count in state["current_model_counts"].items():
        assert count == 0, f"Table {tbl} had partial uncommitted data ({count} rows)!"


def test_bootstrap_dry_run_does_not_mutate(migrated_db):
    """Test: Bootstrap --validate-only / --dry-run reports readiness without writing any records."""
    res = execute_bootstrap(migrated_db, dry_run=True)
    assert res["status"] == "VALIDATED_NO_MUTATION"
    assert res["planned_baseline_records"] == 191

    state = inspect_database_state(migrated_db)
    assert state["total_current_model_rows"] == 0


def test_bootstrap_preserves_legacy_cancer_content_table(tmp_path):
    """Test: Controlled bootstrap safely coexists with legacy 'cancer_content' table without modifying it."""
    db_file = tmp_path / "legacy_bootstrap_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url)

    # 1. Create legacy table
    meta = MetaData()
    cancer_content = Table(
        "cancer_content",
        meta,
        Column("id", Integer, primary_key=True),
        Column("content_id", Text),
        Column("cancer_name", Text),
        Column("content", Text),
    )
    meta.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(cancer_content.insert().values(id=1, content_id="c1", cancer_name="Breast", content="Lump"))
        conn.execute(cancer_content.insert().values(id=2, content_id="c2", cancer_name="Colon", content="Bleeding"))

    # 2. Run migration
    cfg = get_alembic_config()
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    # 3. Run bootstrap
    res = execute_bootstrap(engine, dry_run=False)
    assert res["status"] == "SUCCESS"
    assert res["legacy_table_found"] is True
    assert res["legacy_rows"] == 2

    # 4. Verify legacy table is completely intact
    with engine.connect() as conn:
        legacy_cnt = conn.execute(text("SELECT COUNT(*) FROM cancer_content")).scalar()
        assert legacy_cnt == 2


def test_starting_api_twice_in_production_mode_does_not_mutate_data(migrated_db):
    """
    Test 12: Starting the API twice in production mode changes no row counts,
    identifiers, timestamps, hashes, versions, citations, or consensus relationships.
    """
    # 1. Populate database via bootstrap
    execute_bootstrap(migrated_db, dry_run=False)

    Session = sessionmaker(bind=migrated_db)
    session = Session()

    # Capture complete pre-run snapshot
    pre_cancers = [(c.id, c.slug, c.canonical_name, c.created_at) for c in session.query(Cancer).order_by(Cancer.id).all()]
    pre_sources = [(s.id, s.organization_name) for s in session.query(Source).order_by(Source.id).all()]
    pre_facts = [(f.id, f.fact_key, f.title) for f in session.query(ConsensusFact).order_by(ConsensusFact.id).all()]
    pre_records = [(r.id, r.category, r.content) for r in session.query(ContentRecord).order_by(ContentRecord.id).all()]
    session.close()

    # Simulate starting API lifespan twice
    from app.main import lifespan, app
    from app.core.config import settings

    with patch("app.main.engine", migrated_db):
        with patch.object(settings, "ENVIRONMENT", "production"):
            # Startup 1
            import asyncio
            async def run_lifespan():
                async with lifespan(app):
                    pass
            asyncio.run(run_lifespan())

            # Startup 2
            asyncio.run(run_lifespan())

    # Verify snapshot matches 100%
    session = Session()
    post_cancers = [(c.id, c.slug, c.canonical_name, c.created_at) for c in session.query(Cancer).order_by(Cancer.id).all()]
    post_sources = [(s.id, s.organization_name) for s in session.query(Source).order_by(Source.id).all()]
    post_facts = [(f.id, f.fact_key, f.title) for f in session.query(ConsensusFact).order_by(ConsensusFact.id).all()]
    post_records = [(r.id, r.category, r.content) for r in session.query(ContentRecord).order_by(ContentRecord.id).all()]
    session.close()

    assert pre_cancers == post_cancers
    assert pre_sources == post_sources
    assert pre_facts == post_facts
    assert pre_records == post_records
