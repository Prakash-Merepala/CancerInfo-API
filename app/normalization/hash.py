"""
Content Hashing Utilities (Section 34)
"""
import hashlib


def compute_content_hash(content: str) -> str:
    """
    Computes SHA-256 hash of normalized content string.
    """
    normalized = " ".join(content.strip().split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
