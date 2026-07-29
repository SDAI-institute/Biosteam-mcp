"""Bounded compatibility jobs with optional Redis restart persistence."""

from __future__ import annotations

import os
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .job_persistence import RedisJobPersistence

ENGINE_LOCK = threading.RLock()
_TERMINAL = {"completed", "failed", "cancelled", "interrupted"}


def _now() -> float:
    return time.time()


@dataclass
class JobRecord:
    job_id: str
    tool_name: str
    status: str = "queued"
    created_at: float = field(default_factory=_now)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    future: Optional[Future] = field(default=None, repr=False)

    def public(self, *, include_result: bool = False) -> dict[str, Any]:
        body: dict[str, Any] = {
            "success": True,
            "job_id": self.job_id,
            "tool_name": self.tool_name,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "terminal": self.status in _TERMINAL,
        }
        if self.error is not None:
            body["error"] = self.error
        if include_result and self.status == "completed":
            body["result"] = self.result
        return body

    def persisted(self) -> dict[str, Any]:
        return {
            **self.public(include_result=True),
            "result": self.result if self.status == "completed" else None,
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> "JobRecord":
        return cls(
            job_id=str(payload["job_id"]),
            tool_name=str(payload.get("tool_name") or "unknown"),
            status=str(payload.get("status") or "failed"),
            created_at=float(payload.get("created_at") or _now()),
            started_at=payload.get("started_at"),
            completed_at=payload.get("completed_at"),
            result=payload.get("result"),
            error=payload.get("error"),
        )


class JobManager:
    """Thread-backed registry; Redis preserves terminal state across restarts."""

    def __init__(
        self,
        max_workers: int = 1,
        ttl_seconds: int = 3600,
        persistence: Any = None,
        persistence_url: Optional[str] = None,
    ) -> None:
        self.max_workers = max(1, int(max_workers))
        self.ttl_seconds = max(60, int(ttl_seconds))
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="biosteam-mcp-job",
        )
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.RLock()
        self._persistence = persistence or RedisJobPersistence(
            persistence_url if persistence_url is not None else os.getenv("BIOSTEAM_JOB_REDIS_URL"),
            "biosteam",
            self.ttl_seconds,
        )
        self._restore()

    def _persist(self, record: JobRecord) -> None:
        self._persistence.save(record.persisted())

    def _restore(self) -> None:
        now = _now()
        cutoff = now - self.ttl_seconds
        for payload in self._persistence.load_all():
            try:
