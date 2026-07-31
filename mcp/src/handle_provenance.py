"""Persistent provenance for reconstructible BioSTEAM/QSDsan result handles.

Only JSON-safe build recipes are stored. Scientific objects themselves are never
serialized. A handle may be lazily reconstructed after process restart only when
the runtime package fingerprint exactly matches the one that created the recipe.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from importlib import metadata
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)
_SCHEMA_VERSION = 1


def runtime_fingerprint() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in ("biosteam", "thermosteam", "qsdsan"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "missing"
    return versions


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class HandleProvenanceStore:
    def __init__(self, url: Optional[str] = None, ttl_seconds: Optional[int] = None) -> None:
        self.url = (url if url is not None else os.getenv("BIOSTEAM_HANDLE_REDIS_URL", "")).strip()
        configured_ttl = ttl_seconds if ttl_seconds is not None else int(
            os.getenv("BIOSTEAM_HANDLE_TTL_SECONDS", "604800")
        )
        self.ttl_seconds = max(3600, int(configured_ttl))
        self._client = (
            redis.Redis.from_url(
