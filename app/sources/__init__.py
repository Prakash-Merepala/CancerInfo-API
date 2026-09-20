"""
Sources module
"""
from app.sources.base import BaseSourceAdapter, NormalizedDocument, NormalizedSection
from app.sources.registry import get_adapter, get_all_adapters, list_registered_source_ids

__all__ = [
    "BaseSourceAdapter",
    "NormalizedDocument",
    "NormalizedSection",
    "get_adapter",
    "get_all_adapters",
    "list_registered_source_ids",
]
