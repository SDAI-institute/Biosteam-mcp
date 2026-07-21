"""Integration test for the FastMCP server via the in-memory client.

Run:  pytest mcp/test_server.py    (from the mcp/ dir, in envShilab)

Exercises the real tool surface end-to-end without a transport, using
``fastmcp.Client(mcp)`` which connects in-process.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastmcp import Client

from src.app import NATIVE_TASKS_ENABLED, engine, mcp


def _payload(result):
    """Extract the structured dict from a CallToolResult across fastmcp versions."""
    data = getattr(result, "structured_content", None) or getattr(result, "data", None)
    if data:
        return data
    # Fall back to the first text content block.
    block = result.content[0]
    return json.loads(block.text)


@pytest.mark.asyncio
async def test_tool_listing():
    async with Client(mcp) as client:
        tools = {t.name for t in await client.list_tools()}
    expected = {
        "health_check", "list_biorefinery_models", "build_system",
        "build_system_from_spec", "build_sanitation_system", "simulate_system",
        "get_stream_results", "get_vle_results", "get_unit_results", "get_tea_results", "get_lca_results",
        "get_wastewater_results",
        "run_uncertainty", "run_uncertainty_async", "run_sensitivity",
        "optimize", "optimize_async", "get_job_status", "get_job_result",
        "list_jobs", "cancel_job", "dispose_job", "get_flowsheet_diagram",
        "dispose_result",
    }
    assert expected <= tools


@pytest.mark.asyncio
async def test_native_task_metadata_switch():
    """The long synchronous tools advertise native Tasks only when explicitly enabled."""
    uncertainty = await mcp.get_tool("run_uncertainty")
    optimize_tool = await mcp.get_tool("optimize")
    expected_mode = "optional" if NATIVE_TASKS_ENABLED else "forbidden"
    assert uncertainty.task_config.mode == expected_mode
    assert optimize_tool.task_config.mode == expected_mode


_SPEC = {
    "thermo": ["Water", "Ethanol"],
    "streams": [{"id": "feed", "flows": {"Water": 1000, "Ethanol": 500},
                 "units": "kmol/hr", "T": 298.15, "price": 0.10}],
    "units": [
        {"type": "HXutility", "id": "H1", "ins": ["feed"], "outs": ["hot"],
         "params": {"T": 355}},
        {"type": "Flash", "id": "F1", "ins": ["hot"], "outs": ["vapor", "liquid"],
         "params": {"V": 0.5, "P": 101325}},
        {"type": "Pump", "id": "P1", "ins": ["liquid"], "outs": ["bottoms"]},
    ],
    "product": "vapor",
}


@pytest.mark.asyncio
async def test_async_job_tool_roundtrip(monkeypatch):
    def fake_uncertainty(result_id, parameters, N, seed):
        return {
            "success": True,
            "metric": "fake",
            "result_id": result_id,
            "samples": list(range(N)),
        }

    monkeypatch.setattr(engine, "run_uncertainty", fake_uncertainty)

    async with Client(mcp) as client:
        submitted = _payload(await client.call_tool("run_uncertainty_async", {
            "result_id": "res_fake",
            "parameters": [],
            "N": 12,
            "seed": 7,
        }))
        assert submitted["success"]
        job_id = submitted["job_id"]

        status = None
        for _ in range(100):
            status = _payload(await client.call_tool("get_job_status", {"job_id": job_id}))
            if status["terminal"]:
                break
            await asyncio.sleep(0.01)
        assert status is not None and status["status"] == "completed"

        page = _payload(await client.call_tool("get_job_result", {
            "job_id": job_id,
            "field": "samples",
            "offset": 4,
            "limit": 3,
        }))
        assert page["ready"]
