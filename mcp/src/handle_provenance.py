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
                self.url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            if self.url
            else None
        )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    @staticmethod
    def _key(result_id: str) -> str:
        return f"sdai:handle:biosteam:{result_id}"

    def save(self, result_id: str, kind: str, payload: dict[str, Any]) -> bool:
        if self._client is None:
            return False
        record = {
            "schema_version": _SCHEMA_VERSION,
            "result_id": result_id,
            "kind": kind,
            "payload": payload,
            "payload_sha256": canonical_sha256(payload),
            "runtime": runtime_fingerprint(),
        }
        try:
            encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            self._client.set(self._key(result_id), encoded, ex=self.ttl_seconds)
            return True
        except (TypeError, ValueError) as exc:
            logger.warning("BioSTEAM handle %s recipe is not JSON-safe: %s", result_id, exc)
        except redis.RedisError as exc:
            logger.warning("BioSTEAM handle provenance save failed: %s", exc)
        return False

    def get(self, result_id: str) -> Optional[dict[str, Any]]:
        if self._client is None:
            return None
        try:
            raw = self._client.get(self._key(result_id))
            if not raw:
                return None
            record = json.loads(raw)
            if not isinstance(record, dict):
                return None
            if record.get("schema_version") != _SCHEMA_VERSION:
                return None
            payload = record.get("payload")
            if not isinstance(payload, dict):
                return None
            if record.get("payload_sha256") != canonical_sha256(payload):
                logger.error("BioSTEAM handle provenance checksum mismatch for %s", result_id)
                return None
            # Refresh provenance TTL when a handle is actively used.
            self._client.expire(self._key(result_id), self.ttl_seconds)
            return record
        except (TypeError, ValueError, redis.RedisError) as exc:
            logger.warning("BioSTEAM handle provenance read failed: %s", exc)
            return None

    def delete(self, result_id: str) -> None:
        if self._client is None:
            return
        try:
            self._client.delete(self._key(result_id))
        except redis.RedisError as exc:
            logger.warning("BioSTEAM handle provenance delete failed: %s", exc)
