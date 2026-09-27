"""
CIAPI-L004 Document Reuse Rights and Quarantine Resolution Test Suite

Tests:
1. Current seed inventory resolves all 32 distinct launch-candidate URLs.
2. Existing 20 normal source documents remain represented.
3. The 12 consensus-only URLs also obtain document-level records.
4. Every ContentSource used by the current seed resolves to a SourceDocument.
5. Every ConsensusFactSource resolves to a SourceDocument.
6. Consensus source URL, quote snippet and attribution are preserved.
7. Repeated citations to the same exact document do not create duplicate SourceDocument rows.
8. A new/unreviewed document is not publication eligible by default (fail-closed).
9. Source-level APPROVED does not automatically make a SourceDocument eligible.
10. Missing required evidence/reviewer information prevents an eligible decision.
11. WHO unresolved material remains non-eligible unless exact permission/license evidence exists.
12. Cancer Australia unresolved material remains non-eligible unless exact permission/license evidence exists.
13. CDC current item remains review-required unless exact item evidence exists.
14. Rights inventory includes consensus citation URLs, quotes and attribution.
15. Quarantine/publication decisions are machine-queryable for use by a future publication gate.
16. Document-level attribution/redistribution information maps into consumer provenance schema.
17. The new Alembic migration upgrades successfully from the L003 revision.
18. The L004 migration downgrade works for the L004 delta.
19. Existing L003 migration/bootstrap behavior remains intact.
20. Existing application tests continue to pass.
"""
from datetime import datetime
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.database.session import get_db

from app.core.constants import LicenseStatus, PublicationStatus, ThirdPartyPermissionStatus, TrustTier
from app.core.rights_validation import (
    PublicationEligibilityError,
    assert_publication_eligible,
    evaluate_publication_eligibility,
    verify_source_cannot_grant_eligibility,
)
from app.database.bootstrap import execute_bootstrap
from app.database.migration_check import get_alembic_config, get_current_revision, set_alembic_url_safe
from app.ingestion.rights_inventory import (
    RIGHTS_INVENTORY,
    audit_candidate_acceptance,
    export_rights_audit_report,
    extract_candidate_urls_from_markdown,
    get_rights_inventory_entry,
    list_rights_inventory,
    record_owner_rights_review,
)
from app.ingestion.seed import seed_database
from app.main import app
from app.models import (
    Cancer,
    ConsensusFact,
    ConsensusFactSource,
    ContentRecord,
    ContentSource,
    Source,
    SourceDocument,
)


@pytest.fixture
def test_db_session(tmp_path):
    """Provides a fully migrated and bootstrapped test session."""
    db_file = tmp_path / "l004_test.db"
    db_url = f"sqlite:///{db_file}"
    cfg = get_alembic_config()
    set_alembic_url_safe(cfg, db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    execute_bootstrap(engine, dry_run=False)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_inventory_resolves_all_32_distinct_candidate_urls():
    """Requirement 1: Current seed inventory resolves all 32 distinct launch-candidate URLs."""
    inventory_urls = set(RIGHTS_INVENTORY.keys())
    assert len(inventory_urls) == 32, f"Expected 32 distinct URLs, found {len(inventory_urls)}"

    # Check breakdown by source
    by_source = {}
    for d in list_rights_inventory():
        by_source.setdefault(d.source_id, []).append(d.url)

    assert len(by_source["nci-us"]) == 14
    assert len(by_source["nhs-uk"]) == 9
    assert len(by_source["who-global"]) == 4
    assert len(by_source["cancer-australia"]) == 4
    assert len(by_source["cdc-us"]) == 1
    assert sum(len(urls) for urls in by_source.values()) == 32


def test_seeded_database_has_32_source_documents(test_db_session):
    """Requirement 2 & 3: 20 normal content URLs and 12 consensus-only URLs are all represented in SourceDocument."""
    docs = test_db_session.query(SourceDocument).all()
    assert len(docs) == 32

    urls_in_db = {d.original_url for d in docs}
    assert urls_in_db == set(RIGHTS_INVENTORY.keys())

    # Check normal content URLs (20 distinct)
    cs_urls = {cs.source_url for cs in test_db_session.query(ContentSource).all()}
    assert len(cs_urls) == 20

    # Check consensus citation URLs (20 distinct)
    cfs_urls = {cfs.source_url for cfs in test_db_session.query(ConsensusFactSource).all()}
    assert len(cfs_urls) == 20

    # Check overlap (8) and consensus-only (12)
    overlap = cs_urls.intersection(cfs_urls)
    assert len(overlap) == 8

    consensus_only = cfs_urls - cs_urls
    assert len(consensus_only) == 12

    # Verify each consensus-only URL has a SourceDocument row
    for u in consensus_only:
        doc = test_db_session.query(SourceDocument).filter(SourceDocument.original_url == u).first()
        assert doc is not None, f"Consensus-only URL {u} lacks a SourceDocument!"


def test_all_content_and_consensus_sources_resolve_to_source_document(test_db_session):
    """Requirement 4 & 5: Every ContentSource and ConsensusFactSource links to an exact SourceDocument."""
    content_sources = test_db_session.query(ContentSource).all()
    assert len(content_sources) == 21
    for cs in content_sources:
        assert cs.source_document_id is not None
        assert cs.source_document is not None
        assert cs.source_document.original_url == cs.source_url

    consensus_sources = test_db_session.query(ConsensusFactSource).all()
    assert len(consensus_sources) == 48
    for cfs in consensus_sources:
        assert cfs.source_document_id is not None
        assert cfs.source_document is not None
        assert cfs.source_document.original_url == cfs.source_url


def test_consensus_citation_fields_preserved(test_db_session):
    """Requirement 6: Consensus citation metadata (quote snippet, attribution, URL, country) is preserved."""
    consensus_sources = test_db_session.query(ConsensusFactSource).all()
    for cfs in consensus_sources:
        assert cfs.source_url.startswith("https://")
        assert cfs.quote_snippet is not None and len(cfs.quote_snippet) > 0
        assert cfs.attribution_text is not None and len(cfs.attribution_text) > 0
        assert cfs.country_code in {"US", "GB", "AU", "GLOBAL"}


def test_repeated_citations_do_not_create_duplicate_documents(test_db_session):
    """Requirement 7: Repeated citations to the same exact document share a single SourceDocument row."""
    # "https://www.cancer.gov/types/breast/symptoms" is cited by 3 consensus facts and 1 normal record
    breast_sym_url = "https://www.cancer.gov/types/breast/symptoms"
    docs = test_db_session.query(SourceDocument).filter(SourceDocument.original_url == breast_sym_url).all()
    assert len(docs) == 1, f"Expected exactly 1 SourceDocument for {breast_sym_url}, found {len(docs)}"

    doc = docs[0]
    # Check that multiple consensus citations point to this exact document
    cfs_links = test_db_session.query(ConsensusFactSource).filter(
        ConsensusFactSource.source_document_id == doc.id
    ).all()
    assert len(cfs_links) == 3

    # Check that the normal content record also points to this exact document
    cs_links = test_db_session.query(ContentSource).filter(
        ContentSource.source_document_id == doc.id
    ).all()
    assert len(cs_links) == 1


def test_new_or_unreviewed_document_not_eligible_by_default():
    """Requirement 8: Newly discovered or unreviewed documents default fail-closed to non-eligible."""
    new_doc = SourceDocument(
        id="test-new-doc",
        source_id="nci-us",
        original_url="https://www.cancer.gov/types/new-cancer",
        title="New Cancer Overview",
        country_code="US",
        content_hash="abc123hash",
    )
    # Default is REVIEW_REQUIRED
    assert new_doc.publication_status == PublicationStatus.REVIEW_REQUIRED.value
    assert new_doc.is_publication_eligible() is False

    with pytest.raises(PublicationEligibilityError) as exc_info:
        new_doc.assert_publication_eligible()
    assert "NOT publication eligible" in str(exc_info.value)


def test_source_level_approved_does_not_clear_source_document():
    """Requirement 9: Parent Source being APPROVED, Tier 1, or active does NOT confer eligibility."""
    approved_source = Source(
        id="mock-gov",
        organization_name="Mock Government Health Org",
        source_name="Mock Health Info",
        base_url="https://mockhealth.gov",
        country_code="US",
        source_type="government_agency",
        trust_tier=TrustTier.TIER_1.value,
        authority_type="National Health Authority",
        license_type="Public Domain",
        license_status=LicenseStatus.APPROVED.value,
        active=True,
    )
    doc = SourceDocument(
        id="doc-001",
        source_id="mock-gov",
        original_url="https://mockhealth.gov/info",
        title="Mock Doc",
        country_code="US",
        content_hash="hash123",
        publication_status=PublicationStatus.REVIEW_REQUIRED.value,
    )
    is_eligible, reasons = evaluate_publication_eligibility(doc, source=approved_source)
    assert is_eligible is False
    assert any("must be 'ELIGIBLE'" in r for r in reasons)
    verify_source_cannot_grant_eligibility(doc, approved_source)


def test_missing_required_evidence_prevents_eligible_decision():
    """Requirement 10: Missing required evidence or reviewer fields prevents eligibility."""
    # Start with a doc marked ELIGIBLE but missing required review fields
    doc = SourceDocument(
        id="test-doc",
        source_id="nci-us",
        original_url="https://example.gov/page",
        title="Example",
        country_code="US",
        content_hash="hash",
        publication_status=PublicationStatus.ELIGIBLE.value,
        # Missing rights_evidence_url, rights_reviewed_at, rights_reviewer, etc.
    )
    is_eligible, reasons = evaluate_publication_eligibility(doc)
    assert is_eligible is False
    assert any("Missing required rights evidence URL" in r for r in reasons)
    assert any("Missing required rights review timestamp" in r for r in reasons)
    assert any("Missing required rights reviewer" in r for r in reasons)
    assert any("redistribution is not allowed" in r for r in reasons)

    # Supply evidence fields but keep quarantine reason
    doc.rights_evidence_url = "https://example.gov/policy"
    doc.rights_reviewed_at = datetime.utcnow()
    doc.rights_reviewer = "Reviewer Name"
    doc.redistribution_allowed = True
    doc.commercial_redistribution_allowed = True
    doc.quarantine_reason = "Pending third-party media clearance"
    assert doc.is_publication_eligible() is False

    # Clear quarantine reason -> now eligible
    doc.quarantine_reason = None
    doc.third_party_permission_status = "NOT_APPLICABLE"
    assert doc.is_publication_eligible() is True


def test_who_unresolved_material_is_quarantined_or_permission_pending(test_db_session):
    """Requirement 11: WHO documents remain non-publication-eligible due to commercial/API restriction."""
    who_docs = test_db_session.query(SourceDocument).filter(SourceDocument.source_id == "who-global").all()
    assert len(who_docs) == 4
    for doc in who_docs:
        assert doc.publication_status == PublicationStatus.PERMISSION_PENDING.value
        assert doc.is_publication_eligible() is False
        assert doc.commercial_redistribution_allowed is False
        assert "CC BY-NC-SA 3.0 IGO" in doc.quarantine_reason
        assert doc.third_party_permission_status == ThirdPartyPermissionStatus.REQUIRED_NOT_SUBMITTED.value
        assert "no request has yet been submitted" in doc.third_party_permission_notes.lower() or "not yet been submitted" in doc.third_party_permission_notes.lower()


def test_cancer_australia_unresolved_material_is_review_required(test_db_session):
    """Requirement 12: Cancer Australia documents remain non-publication-eligible awaiting item audit."""
    au_docs = test_db_session.query(SourceDocument).filter(SourceDocument.source_id == "cancer-australia").all()
    assert len(au_docs) == 4
    for doc in au_docs:
        assert doc.publication_status == PublicationStatus.REVIEW_REQUIRED.value
        assert doc.is_publication_eligible() is False
        assert doc.commercial_redistribution_allowed is False
        assert "Crown copyright" in doc.quarantine_reason or "CC BY 4.0" in doc.quarantine_reason


def test_cdc_current_item_is_review_required(test_db_session):
    """Requirement 13: CDC document remains non-publication-eligible awaiting third-party audit."""
    cdc_docs = test_db_session.query(SourceDocument).filter(SourceDocument.source_id == "cdc-us").all()
    assert len(cdc_docs) == 1
    doc = cdc_docs[0]
    assert doc.publication_status == PublicationStatus.REVIEW_REQUIRED.value
    assert doc.is_publication_eligible() is False
    assert doc.commercial_redistribution_allowed is False
    assert "third-party" in doc.quarantine_reason.lower()


def test_rights_inventory_includes_consensus_citations_and_quotes(test_db_session):
    """Requirement 14 & 15: Rights audit export includes consensus citations, quotes, and attributions."""
    report = export_rights_audit_report(test_db_session)
    assert len(report) == 32

    # Check a document with consensus citations
    breast_sym_entry = next(e for e in report if e["url"] == "https://www.cancer.gov/types/breast/symptoms")
    assert len(breast_sym_entry["linked_consensus_citations"]) == 3
    for cit in breast_sym_entry["linked_consensus_citations"]:
        assert "fact_key" in cit
        assert "quote_snippet" in cit
        assert len(cit["quote_snippet"]) > 0
        assert "attribution_text" in cit


def test_consumer_provenance_schema_mapping(test_db_session):
    """Requirement 16: Document-level attribution and rights metadata maps into API responses."""
    app.dependency_overrides[get_db] = lambda: test_db_session
    try:
        client = TestClient(app)
        response = client.get("/v1/cancers/breast-cancer/symptoms")
        assert response.status_code == 200
        data = response.json()["data"]

        # Verify consensus item corroborating source has document-level rights fields
        items = data.get("items")
        assert items and len(items) > 0
        first_item = items[0]
        corrob_sources = first_item.get("corroborated_by", [])
        assert len(corrob_sources) > 0
        first_corrob = corrob_sources[0]
        assert "document_title" in first_corrob
        assert "publication_status" in first_corrob
        assert "reuse_conditions" in first_corrob
        assert "commercial_redistribution_allowed" in first_corrob
        assert "rights_evidence_url" in first_corrob

        # Verify raw records provenance source has document-level rights fields
        records = data.get("records")
        assert records and len(records) > 0
        first_rec = records[0]
        sources = first_rec.get("sources", [])
        assert len(sources) > 0
        first_src = sources[0]
        assert "document_title" in first_src
        assert "publication_status" in first_src
        assert "reuse_conditions" in first_src
        assert "commercial_redistribution_allowed" in first_src
        assert "rights_evidence_url" in first_src
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_l004_migration_upgrade_and_downgrade(tmp_path):
    """Requirement 17 & 18: Alembic migration upgrades from L003 and downgrades cleanly for L004 delta."""
    db_file = tmp_path / "migration_delta.db"
    db_url = f"sqlite:///{db_file}"
    cfg = get_alembic_config()
    set_alembic_url_safe(cfg, db_url)

    # 1. Upgrade to L003 initial schema
    command.upgrade(cfg, "0001_initial_schema")
    engine = create_engine(db_url)
    assert get_current_revision(engine) == "0001_initial_schema"

    # Insert baseline L003 SourceDocument using raw SQL (pre-L004 schema)
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO sources (id, organization_name, source_name, base_url, country_code, "
            "source_type, trust_tier, authority_type, license_type, license_status, active) "
            "VALUES ('test-src', 'Test Org', 'Test', 'https://example.org', 'US', 'government', "
            "'Tier 1', 'Authority', 'Public Domain', 'APPROVED', 1)"
        ))
        conn.execute(text(
            "INSERT INTO source_documents (id, source_id, original_url, title, language, "
            "country_code, jurisdiction_scope, retrieved_at, last_verified_at, content_hash, "
            "parser_version, processing_status, license_status) "
            "VALUES ('doc-pre-l004', 'test-src', 'https://example.org/test', 'Pre-L004 Doc', "
            "'en', 'US', 'COUNTRY', '2026-09-27 00:00:00', '2026-09-27 00:00:00', 'pre_hash', "
            "'1.0.0', 'PROCESSED', 'REVIEW_REQUIRED')"
        ))
        conn.commit()

    # 2. Upgrade to L004 head (0002_document_rights_and_consensus_linkage)
    command.upgrade(cfg, "head")
    assert get_current_revision(engine) == "0002_document_rights_and_consensus_linkage"

    # Verify existing document received fail-closed server_default 'REVIEW_REQUIRED'
    with sessionmaker(bind=engine)() as s:
        migrated_doc = s.query(SourceDocument).filter_by(id="doc-pre-l004").one()
        assert migrated_doc.publication_status == "REVIEW_REQUIRED"
        assert migrated_doc.is_publication_eligible() is False

    # 3. Downgrade back to L003
    command.downgrade(cfg, "0001_initial_schema")
    assert get_current_revision(engine) == "0001_initial_schema"

    # Verify L004 columns were removed
    inspector = inspect(engine)
    sd_cols = {c["name"] for c in inspector.get_columns("source_documents")}
    assert "publication_status" not in sd_cols
    assert "rights_evidence_url" not in sd_cols
    cfs_cols = {c["name"] for c in inspector.get_columns("consensus_fact_sources")}
    assert "source_document_id" not in cfs_cols

    # 4. Re-upgrade to head
    command.upgrade(cfg, "head")
    assert get_current_revision(engine) == "0002_document_rights_and_consensus_linkage"
    inspector = inspect(engine)
    sd_cols = {c["name"] for c in inspector.get_columns("source_documents")}
    assert "publication_status" in sd_cols
    engine.dispose()


def test_documented_candidate_urls_match_registry_and_seed(test_db_session):
    """
    Mithra acceptance correction: Handoff and candidate report URL sets
    must not diverge from the registry or seeded candidate set.
    Asserts: set(documented_candidate_urls) == set(RIGHTS_INVENTORY.keys()) == set(seed_candidate_urls)
    """
    inv_urls = set(RIGHTS_INVENTORY.keys())
    seed_urls = {d.original_url for d in test_db_session.query(SourceDocument).all()}

    with open("docs/HANDOFF_TO_MITHRA.md") as f:
        handoff_urls = extract_candidate_urls_from_markdown(f.read())

    with open("candidate_report_CIAPI-L004.md") as f:
        report_urls = extract_candidate_urls_from_markdown(f.read())

    assert len(inv_urls) == 32
    assert len(seed_urls) == 32
    assert len(handoff_urls) == 32
    assert len(report_urls) == 32

    assert handoff_urls == inv_urls
    assert report_urls == inv_urls
    assert seed_urls == inv_urls


def test_acceptance_validation_reports_missing_owner_review_as_blocker(test_db_session):
    """
    Mithra acceptance correction: Acceptance validation must truthfully report
    missing rights_reviewed_at and rights_reviewer as OPEN blockers.
    """
    report = audit_candidate_acceptance(db=test_db_session)

    assert report["total_candidate_documents"] == 32
    assert report["with_rights_evidence"] == 32
    assert report["with_permissible_use"] == 32
    assert report["with_attribution_decision"] == 32
    assert report["with_publication_decision"] == 32

    # Truthful check: Owner review has NOT yet occurred
    assert report["with_review_date"] == 0
    assert report["with_decision_owner"] == 0
    assert report["owner_review_completed"] is False
    assert report["l004_acceptance_satisfied"] is False

    # Blockers must be explicitly reported
    assert len(report["blockers"]) >= 2
    assert any("missing formal owner review timestamp" in b.lower() for b in report["blockers"])
    assert any("missing formal owner decision reviewer" in b.lower() for b in report["blockers"])
    assert any("who candidate documents" in b.lower() for b in report["blockers"])

    assert len(report["documents_missing_review_date"]) == 32
    assert len(report["documents_missing_decision_owner"]) == 32


def test_third_party_permission_state_distinguishes_not_requested_from_submitted():
    """
    Mithra acceptance correction: Third-party permission state must distinguish
    'not requested' (REQUIRED_NOT_SUBMITTED) from 'submitted and awaiting response'.
    """
    doc = SourceDocument(
        id="test-doc-tp",
        source_id="who-global",
        original_url="https://example.org/who",
        title="WHO Test",
        country_code="GLOBAL",
        content_hash="hash",
        publication_status=PublicationStatus.PERMISSION_PENDING.value,
        rights_evidence_url="https://example.org/rights",
        rights_reviewed_at=datetime.utcnow(),
        rights_reviewer="Auditor",
        redistribution_allowed=True,
        commercial_redistribution_allowed=True,
        third_party_permission_status=ThirdPartyPermissionStatus.REQUIRED_NOT_SUBMITTED.value,
    )
    is_eligible, reasons = evaluate_publication_eligibility(doc)
    assert is_eligible is False
    assert any("REQUIRED_NOT_SUBMITTED" in r for r in reasons)

    # Change to REQUESTED_AWAITING_RESPONSE -> still not eligible while response pending
    doc.third_party_permission_status = ThirdPartyPermissionStatus.REQUESTED_AWAITING_RESPONSE.value
    is_eligible, reasons = evaluate_publication_eligibility(doc)
    assert is_eligible is False
    assert any("REQUESTED_AWAITING_RESPONSE" in r for r in reasons)

    # Change to GRANTED and clear publication status to ELIGIBLE -> now eligible
    doc.third_party_permission_status = ThirdPartyPermissionStatus.GRANTED.value
    doc.publication_status = PublicationStatus.ELIGIBLE.value
    is_eligible, reasons = evaluate_publication_eligibility(doc)
    assert is_eligible is True


def test_owner_review_workflow_truthful_recording(test_db_session):
    """
    Verifies that the owner review workflow API record_owner_rights_review
    truthfully records review date and reviewer without fabricating data.
    """
    with pytest.raises(ValueError):
        record_owner_rights_review(
            "https://www.cancer.gov/types/breast",
            reviewer="",
            db=test_db_session,
        )

    res = record_owner_rights_review(
        "https://www.cancer.gov/types/breast",
        reviewer="Jaya Prakash Merepala",
        reviewed_at=datetime.utcnow(),
        db=test_db_session,
    )
    assert res["status"] == "RECORDED"
    assert res["rights_reviewer"] == "Jaya Prakash Merepala"

    # Verify updated in database
    doc = test_db_session.query(SourceDocument).filter_by(
        original_url="https://www.cancer.gov/types/breast"
    ).one()
    assert doc.rights_reviewer == "Jaya Prakash Merepala"
    assert doc.rights_reviewed_at is not None

