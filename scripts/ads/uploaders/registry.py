"""Platform → uploader lookup."""

from __future__ import annotations

from typing import Dict, Type

from .base import AdUploader

_REGISTRY: Dict[str, Type[AdUploader]] = {}


def register(platform: str):
    """Decorator: register an AdUploader subclass under a platform key."""
    def _wrap(cls: Type[AdUploader]) -> Type[AdUploader]:
        _REGISTRY[platform] = cls
        cls.platform = platform
        return cls
    return _wrap


def get_uploader(platform: str) -> AdUploader:
    # Import for side-effects so @register decorators run.
    from . import meta, tiktok, google, linkedin  # noqa: F401

    key = platform.lower()
    if key not in _REGISTRY:
        raise KeyError(
            f"Unknown platform {platform!r}. Available: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[key]()


def list_platforms() -> list[str]:
    from . import meta, tiktok, google, linkedin  # noqa: F401
    return sorted(_REGISTRY.keys())
