"""
Source Adapter Registry & Factory
"""
from typing import Dict, List, Optional, Type
from app.sources.adapters.cancer_australia import CancerAustraliaAdapter
from app.sources.adapters.nci import NCIAdapter
from app.sources.adapters.nhs import NHSAdapter
from app.sources.adapters.who import WHOAdapter
from app.sources.base import BaseSourceAdapter

_ADAPTER_REGISTRY: Dict[str, Type[BaseSourceAdapter]] = {
    "nci-us": NCIAdapter,
    "who-global": WHOAdapter,
    "nhs-uk": NHSAdapter,
    "cancer-australia": CancerAustraliaAdapter,
}


def get_adapter(source_id: str) -> Optional[BaseSourceAdapter]:
    adapter_cls = _ADAPTER_REGISTRY.get(source_id)
    if adapter_cls:
        return adapter_cls()
    return None


def get_all_adapters() -> List[BaseSourceAdapter]:
    return [cls() for cls in _ADAPTER_REGISTRY.values()]


def list_registered_source_ids() -> List[str]:
    return list(_ADAPTER_REGISTRY.keys())
