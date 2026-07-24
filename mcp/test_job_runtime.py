from __future__ import annotations

import threading
import time

from src.job_runtime import JobManager


class MemoryPersistence:
    def __init__(self) -> None:
        self.rows = {}

    def save(self, payload):
        self.rows[payload["job_id"]] = dict(payload)
        return True

    def load_all(self):
        return [dict(row) for row in self.rows.values()]

    def delete(self, job_id):
        self.rows.pop(job_id, None)


def _wait_terminal(manager: JobManager, job_id: str, timeout: float = 2.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = manager.status(job_id)
        if status.get("terminal"):
            return status
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} did not reach a terminal state")


def test_job_completion_and_paged_result() -> None:
    manager = JobManager(max_workers=1, ttl_seconds=60)
    try:
        submitted = manager.submit(
            "fake_long_tool", lambda: {"success": True, "items": list(range(10))}
        )
        assert submitted["success"]
        assert submitted["status"] in {"queued", "running"}
        job_id = submitted["job_id"]

        status = _wait_terminal(manager, job_id)
        assert status["status"] == "completed"

        page = manager.result(job_id, field="items", offset=3, limit=4)
        assert page["success"]
        assert page["ready"]
        assert page["result"] == [3, 4, 5, 6]
        assert page["pagination"] == {
            "offset": 3,
            "limit": 4,
            "total": 10,
            "next_offset": 7,
