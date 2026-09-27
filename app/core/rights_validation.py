"""
Publication Eligibility and Rights Validation Module (CIAPI-L004)

Enforces strict fail-closed publication gates:
1. Documents without explicit ELIGIBLE status and complete rights audit evidence cannot be published.
2. Source-level registry fields (APPROVED, Tier 1, government status, domain) NEVER confer document clearance.
"""
from typing import List, Optional, Tuple
from app.core.constants import PublicationStatus


class PublicationEligibilityError(ValueError):
    """Raised when an unreviewed, quarantined, or insufficiently evidenced document is evaluated for publication."""
    pass


def evaluate_publication_eligibility(
    doc,
    source=None,
) -> Tuple[bool, List[str]]:
    """
    Evaluates whether a SourceDocument is eligible for public/commercial API publication.
    Returns (is_eligible, deficiency_reasons).

    Rules:
    - Must have publication_status == 'ELIGIBLE'
    - Must have non-empty rights_evidence_url
    - Must have non-null rights_reviewed_at timestamp
    - Must have non-empty rights_reviewer decision owner
    - Must have commercial_redistribution_allowed is True
    - Must have redistribution_allowed is True
    - Must NOT have a quarantine_reason
    - Third-party permission status must not be PENDING, REVIEW_REQUIRED, or UNREVIEWED
    - Source properties (active, APPROVED, Tier 1, government) NEVER satisfy document requirements.
    """
    reasons: List[str] = []

    # 1. Status check
    pub_status = getattr(doc, "publication_status", None)
    if pub_status != PublicationStatus.ELIGIBLE.value:
        reasons.append(
            f"Document publication status is '{pub_status}' (must be '{PublicationStatus.ELIGIBLE.value}')"
        )

    # 2. Rights evidence URL
    evidence_url = getattr(doc, "rights_evidence_url", None)
    if not evidence_url or not str(evidence_url).strip():
        reasons.append("Missing required rights evidence URL")

    # 3. Review timestamp
    reviewed_at = getattr(doc, "rights_reviewed_at", None)
    if reviewed_at is None:
        reasons.append("Missing required rights review timestamp (rights_reviewed_at)")

    # 4. Reviewer / decision owner
    reviewer = getattr(doc, "rights_reviewer", None)
    if not reviewer or not str(reviewer).strip():
        reasons.append("Missing required rights reviewer or decision owner (rights_reviewer)")

    # 5. Redistribution permissions
    if not getattr(doc, "redistribution_allowed", False):
        reasons.append("Document-level redistribution is not allowed (redistribution_allowed=False)")

    if not getattr(doc, "commercial_redistribution_allowed", False):
        reasons.append("Document-level commercial/API redistribution is not allowed (commercial_redistribution_allowed=False)")

    # 6. Quarantine reason
    quarantine_reason = getattr(doc, "quarantine_reason", None)
    if quarantine_reason and str(quarantine_reason).strip():
        reasons.append(f"Document has active quarantine reason: {quarantine_reason}")

    # 7. Third-party permissions
    third_party_status = getattr(doc, "third_party_permission_status", None)
    if third_party_status in {"PENDING", "REVIEW_REQUIRED", "UNREVIEWED", "RESTRICTED"}:
        reasons.append(f"Unresolved third-party permission status: '{third_party_status}'")

    is_eligible = len(reasons) == 0
    return is_eligible, reasons


def assert_publication_eligible(doc, source=None) -> None:
    """
    Raises PublicationEligibilityError if the document cannot be published.
    """
    is_eligible, reasons = evaluate_publication_eligibility(doc, source=source)
    if not is_eligible:
        url = getattr(doc, "original_url", "<unknown-url>")
        raise PublicationEligibilityError(
            f"Document '{url}' is NOT publication eligible: {'; '.join(reasons)}"
        )


def verify_source_cannot_grant_eligibility(doc, source) -> None:
    """
    Verification check: Proves that even if parent source is active, APPROVED, Tier 1,
    and a government agency, an unreviewed document remains ineligible.
    """
    is_eligible, reasons = evaluate_publication_eligibility(doc, source=source)
    if is_eligible:
        raise AssertionError("Document unexpectedly marked eligible without satisfying item-level review criteria!")
