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
                record = JobRecord.restore(payload)
            except (KeyError, TypeError, ValueError):
                continue
            if record.completed_at is not None and float(record.completed_at) < cutoff:
                self._persistence.delete(record.job_id)
                continue
            if record.status in {"queued", "running"}:
                record.status = "interrupted"
                record.completed_at = now
                record.error = (
                    "job interrupted by MCP process restart; it was not replayed automatically. "
                    "Resubmit the compatibility job or use native MCP Tasks for restart redelivery."
                )
                self._persist(record)
            self._jobs[record.job_id] = record

    def _cleanup_expired(self) -> None:
        cutoff = _now() - self.ttl_seconds
        with self._lock:
            expired = [
                job_id
                for job_id, record in self._jobs.items()
                if record.status in _TERMINAL
                and record.completed_at is not None
                and record.completed_at < cutoff
            ]
            for job_id in expired:
                del self._jobs[job_id]
                self._persistence.delete(job_id)

    def submit(self, tool_name: str, fn: Callable[..., Any], *args: Any) -> dict[str, Any]:
        self._cleanup_expired()
        record = JobRecord(job_id=f"job_{uuid.uuid4().hex[:16]}", tool_name=tool_name)
        with self._lock:
            self._jobs[record.job_id] = record
            self._persist(record)
            record.future = self._executor.submit(self._run, record.job_id, fn, args)
        return record.public()

    def _run(self, job_id: str, fn: Callable[..., Any], args: tuple[Any, ...]) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status == "cancelled":
                return
            record.status = "running"
            record.started_at = _now()
            self._persist(record)
        try:
            with ENGINE_LOCK:
                value = fn(*args)
        except Exception as exc:
            with self._lock:
                record = self._jobs.get(job_id)
                if record is None:
                    return
                record.status = "failed"
                record.error = f"{type(exc).__name__}: {exc}"
                record.completed_at = _now()
                self._persist(record)
            return
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            record.result = value
            record.status = "completed"
            record.completed_at = _now()
            self._persist(record)

    def get(self, job_id: str) -> Optional[JobRecord]:
        self._cleanup_expired()
        with self._lock:
            return self._jobs.get(job_id)

    def status(self, job_id: str) -> dict[str, Any]:
        record = self.get(job_id)
        return record.public() if record else {"success": False, "error": f"unknown job_id '{job_id}'"}

    def result(self, job_id: str, *, field: Optional[str] = None,
               offset: int = 0, limit: int = 50) -> dict[str, Any]:
        record = self.get(job_id)
        if record is None:
            return {"success": False, "error": f"unknown job_id '{job_id}'"}
        if record.status != "completed":
            body = record.public()
            body["ready"] = False
            return body
        offset = max(0, int(offset))
        limit = min(200, max(1, int(limit)))
        value = record.result
        body = record.public()
        body["ready"] = True
        if field is not None:
            if not isinstance(value, dict) or field not in value:
                return {"success": False, "error": f"result field '{field}' not found", "job_id": job_id}
            selected = value[field]
            if not isinstance(selected, list):
                body.update({"field": field, "result": selected})
                return body
            page = selected[offset: offset + limit]
            body.update({"field": field, "result": page, "pagination": {
                "offset": offset, "limit": limit, "total": len(selected),
                "next_offset": offset + len(page) if offset + len(page) < len(selected) else None,
            }})
            return body
        body["result"] = value
        return body

    def cancel(self, job_id: str) -> dict[str, Any]:
        record = self.get(job_id)
        if record is None:
            return {"success": False, "error": f"unknown job_id '{job_id}'"}
        with self._lock:
            if record.status in _TERMINAL:
                body = record.public()
                body["cancelled"] = record.status == "cancelled"
                return body
            if record.status == "running":
                body = record.public()
                body.update({"cancelled": False, "cancel_supported": False,
                             "message": "running BioSTEAM jobs cannot be interrupted safely"})
                return body
            cancelled = bool(record.future and record.future.cancel())
            if cancelled:
                record.status = "cancelled"
                record.completed_at = _now()
                self._persist(record)
            body = record.public()
            body.update({"cancelled": cancelled, "cancel_supported": True})
            return body

    def list_jobs(self, limit: int = 20) -> dict[str, Any]:
        self._cleanup_expired()
        limit = min(100, max(1, int(limit)))
        with self._lock:
            records = sorted(self._jobs.values(), key=lambda r: r.created_at, reverse=True)[:limit]
        return {"success": True, "jobs": [record.public() for record in records]}

    def dispose(self, job_id: str) -> dict[str, Any]:
        record = self.get(job_id)
        if record is None:
            return {"success": False, "error": f"unknown job_id '{job_id}'"}
        if record.status not in _TERMINAL:
            return {"success": False, "error": "cannot dispose a non-terminal job", "job_id": job_id}
        with self._lock:
            self._jobs.pop(job_id, None)
            self._persistence.delete(job_id)
        return {"success": True, "job_id": job_id, "disposed": True}

    def shutdown(self, *, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)


jobs = JobManager(
    max_workers=int(os.getenv("BIOSTEAM_JOB_WORKERS", "1")),
    ttl_seconds=int(os.getenv("BIOSTEAM_JOB_TTL_SECONDS", "3600")),
)
