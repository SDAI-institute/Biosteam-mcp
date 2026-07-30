"""Strict JSON persistence for compatibility background-job registries."""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable, Optional

import redis

logger = logging.getLogger(__name__)


class RedisJobPersistence:
    """Best-effort Redis persistence for JSON-safe job metadata and results."""

    def __init__(
        self,
        url: Optional[str],
        namespace: str,
        ttl_seconds: int,
    ) -> None:
        self.url = (url or "").strip()
        self.namespace = namespace.strip()
        self.ttl_seconds = max(60, int(ttl_seconds))
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

    def _key(self, job_id: str) -> str:
        return f"sdai:compat-job:{self.namespace}:{job_id}"

    def save(self, payload: dict[str, Any]) -> bool:
        if self._client is None:
            return False
        try:
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            self._client.set(
                self._key(str(payload["job_id"])),
                encoded,
                ex=self.ttl_seconds,
            )
            return True
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Compatibility job %s is not JSON-persistable: %s",
                payload.get("job_id"),
                exc,
            )
        except redis.RedisError as exc:
            logger.warning("Compatibility-job Redis save failed: %s", exc)
        return False

    def load_all(self) -> list[dict[str, Any]]:
        if self._client is None:
            return []
        rows: list[dict[str, Any]] = []
        try:
            pattern = self._key("*")
            for key in self._client.scan_iter(match=pattern, count=100):
                raw = self._client.get(key)
                if not raw:
                    continue
                try:
                    value = json.loads(raw)
                except (TypeError, ValueError):
                    logger.warning("Skipping invalid persisted job record at %s", key)
                    continue
                if isinstance(value, dict):
                    rows.append(value)
        except redis.RedisError as exc:
            logger.warning("Compatibility-job Redis restore failed: %s", exc)
        return rows

    def delete(self, job_id: str) -> None:
        if self._client is None:
            return
        try:
            self._client.delete(self._key(job_id))
        except redis.RedisError as exc:
            logger.warning("Compatibility-job Redis delete failed: %s", exc)

    def refresh(self, job_ids: Iterable[str]) -> None:
        if self._client is None:
            return
        try:
            pipe = self._client.pipeline(transaction=False)
            for job_id in job_ids:
                pipe.expire(self._key(job_id), self.ttl_seconds)
            pipe.execute()
        except redis.RedisError as exc:
            logger.warning("Compatibility-job Redis TTL refresh failed: %s", exc)
