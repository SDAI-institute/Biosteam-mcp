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
