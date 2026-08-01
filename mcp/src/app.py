"""FastMCP application for the BioSTEAM / QSDsan MCP server.

Owns the server object, the tool-registration decorators, the blocking-call offload,
and the transport. The analysis logic lives in ``engine.py`` (MCP-agnostic); the tools
in ``tools.py`` are thin async wrappers registered on the ``mcp`` object here.

Design carried from the sibling ``openlca_mcp`` server:
  * Strict-but-permissive ``output_schema`` (``additionalProperties: true`` +
    ``required: ["success"]``) so the shared error envelope validates.
  * Read-only vs mutating tools flagged via ``ToolAnnotations``; mutating tools are
    blocked when the server runs in read-only mode (``BIOSTEAM_MCP_READONLY=1``).
  * Blocking BioSTEAM simulations offloaded with ``anyio.to_thread`` so a slow
    solve never blocks the event loop.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import anyio
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Make the MCP-agnostic engine importable whether launched via ``python -m src``
# from the ``mcp/`` dir or as an installed console script. We insert the *package
# parent* (the ``mcp/`` folder) only — never its parent — so ``import mcp`` keeps
# resolving to the SDK, not this server's folder.
_PKG_PARENT = Path(__file__).resolve().parent.parent
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from engine import BioSTEAMEngine  # noqa: E402

from . import __version__  # noqa: E402
from .job_runtime import ENGINE_LOCK  # noqa: E402
from .schemas import out  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_SERVER_NAME = "biosteam-qsdsan-server"
_SERVER_INSTRUCTIONS = (
    "Use these tools for BioSTEAM/QSDsan bioprocess design, techno-economic analysis "
    "(TEA), and life-cycle assessment (LCA). Call health_check first. build_system "
    "returns a result_id you pass to the analysis tools. build/simulate/run_* mutate "
    "server state; honor read-only mode. Modern MCP 2026-07-28 clients may run "
    "run_uncertainty and optimize as native Tasks when enabled; older clients can use "
    "run_uncertainty_async and optimize_async, polling get_job_status then get_job_result. "
    "Call run_uncertainty before run_sensitivity when using the synchronous path. "
    "Call dispose_result when finished with a result_id. For LCA, supply background "
    "characterization factors (cfs); the server computes the foreground inventory."
)

# Process-wide engine instance holds the result store.
engine = BioSTEAMEngine()

READ_ONLY = os.getenv("BIOSTEAM_MCP_READONLY", "").strip().lower() in ("1", "true", "yes")
NATIVE_TASKS_ENABLED = os.getenv("BIOSTEAM_NATIVE_TASKS_ENABLED", "false").strip().lower() in (
    "1", "true", "yes", "on"
)
NATIVE_TASKS_CONCURRENCY = max(1, int(os.getenv("BIOSTEAM_NATIVE_TASKS_CONCURRENCY", "1")))


def _title(name: str) -> str:
    return name.replace("_", " ").title()


async def offload(fn: Callable[..., Any], *args: Any) -> Any:
    """Run a blocking engine call in a worker thread under the shared engine lock."""

    def _work() -> Any:
        with ENGINE_LOCK:
            return fn(*args)

    return await anyio.to_thread.run_sync(_work)


mcp = FastMCP(name=_SERVER_NAME, version=__version__, instructions=_SERVER_INSTRUCTIONS)
if NATIVE_TASKS_ENABLED:
    from fastmcp_tasks import TasksExtension

    mcp.add_extension(TasksExtension(concurrency=NATIVE_TASKS_CONCURRENCY))


def read_tool(name: str, description: str, output: Optional[dict] = None):
    """Register a read-only tool."""
    return mcp.tool(
        name=name, description=description, output_schema=out(output),
        annotations=ToolAnnotations(
            title=_title(name), readOnlyHint=True, idempotentHint=True, openWorldHint=False
        ),
    )


def mutate_tool(
    name: str,
    description: str,
    output: Optional[dict] = None,
    *,
    task: bool = False,
):
    """Register a mutating tool (changes server state)."""
    return mcp.tool(
        name=name, description=description, output_schema=out(output), task=task,
        annotations=ToolAnnotations(
            title=_title(name), readOnlyHint=False, destructiveHint=False,
            idempotentHint=False, openWorldHint=False,
        ),
    )


def guard_readonly() -> Optional[dict]:
    """Return an error envelope if the server is read-only, else None."""
    if READ_ONLY:
        return {"success": False, "error": "server is in read-only mode"}
    return None


@mcp.custom_route("/health", methods=["GET"])
async def _health(_request):
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "server": _SERVER_NAME})


@read_tool(
    "health_check",
    "Health probe: confirms BioSTEAM/thermosteam/QSDsan import and reports versions. "
    "Call this first.",
    {"versions": {"type": "object", "description": "Installed package versions."}},
)
async def health_check() -> dict:
    return await offload(engine.health_check)


# Register the analysis tools (their decorators run on import).
from . import tools as _tools  # noqa: E402,F401


def run() -> None:
    """Run the server with the configured transport (stdio default; http optional)."""
    transport = os.getenv("TRANSPORT", "stdio").strip().lower()
    logger.info(
        "Starting BioSTEAM/QSDsan FastMCP server "
        "(transport=%s, read_only=%s, native_tasks=%s, task_concurrency=%s)",
        transport, READ_ONLY, NATIVE_TASKS_ENABLED, NATIVE_TASKS_CONCURRENCY,
    )
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport="http",
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8000")),
            path=os.getenv("MCP_HTTP_PATH", "/mcp"),
            stateless_http=True,
            json_response=True,
        )


if __name__ == "__main__":
    run()
