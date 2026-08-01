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
# parent* (the ``mcp/`` folder) only â€” never its parent â€” so ``import mcp`` keeps
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
