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
        }

        disposed = manager.dispose(job_id)
        assert disposed["success"] and disposed["disposed"]
        assert manager.status(job_id)["success"] is False
    finally:
        manager.shutdown()


def test_queued_job_can_be_cancelled_but_running_job_is_not_force_killed() -> None:
    manager = JobManager(max_workers=1, ttl_seconds=60)
    release = threading.Event()

    def blocking() -> dict:
        release.wait(timeout=1.0)
        return {"success": True}

    try:
        first = manager.submit("blocking", blocking)
        deadline = time.time() + 1.0
        while time.time() < deadline and manager.status(first["job_id"])["status"] == "queued":
            time.sleep(0.01)

        running_cancel = manager.cancel(first["job_id"])
        assert running_cancel["cancelled"] is False
        assert running_cancel["cancel_supported"] is False

        second = manager.submit("queued", lambda: {"success": True})
        cancelled = manager.cancel(second["job_id"])
        assert cancelled["success"]
        assert cancelled["cancelled"] is True
        assert cancelled["status"] == "cancelled"

        release.set()
        assert _wait_terminal(manager, first["job_id"])["status"] == "completed"
    finally:
        release.set()
        manager.shutdown()


def test_completed_result_restores_after_manager_restart() -> None:
    persistence = MemoryPersistence()
    first = JobManager(max_workers=1, ttl_seconds=60, persistence=persistence)
    try:
        submitted = first.submit("persisted", lambda: {"success": True, "items": [1, 2, 3]})
        assert _wait_terminal(first, submitted["job_id"])["status"] == "completed"
        job_id = submitted["job_id"]
    finally:
        first.shutdown()

    second = JobManager(max_workers=1, ttl_seconds=60, persistence=persistence)
    try:
        restored = second.result(job_id)
        assert restored["status"] == "completed"
        assert restored["ready"] is True
        assert restored["result"] == {"success": True, "items": [1, 2, 3]}
    finally:
        second.shutdown()


def test_running_record_restores_as_interrupted_without_replay() -> None:
    persistence = MemoryPersistence()
    persistence.save({
        "success": True,
        "job_id": "job_interrupted_fixture",
        "tool_name": "fake_long_tool",
        "status": "running",
        "created_at": time.time() - 5,
        "started_at": time.time() - 4,
        "completed_at": None,
        "terminal": False,
        "result": None,
    })
    manager = JobManager(max_workers=1, ttl_seconds=60, persistence=persistence)
    try:
        status = manager.status("job_interrupted_fixture")
        assert status["status"] == "interrupted"
        assert status["terminal"] is True
        assert "not replayed automatically" in status["error"]
        assert persistence.rows["job_interrupted_fixture"]["status"] == "interrupted"
    finally:
        manager.shutdown()
