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
        assert page["result"] == [4, 5, 6]
        assert page["pagination"]["next_offset"] == 7

        disposed = _payload(await client.call_tool("dispose_job", {"job_id": job_id}))
        assert disposed["success"] and disposed["disposed"]


@pytest.mark.asyncio
async def test_spec_build_optimize_diagram():
    async with Client(mcp) as client:
        built = _payload(await client.call_tool("build_system_from_spec", {"spec": _SPEC}))
        assert built["success"]
        rid = built["result_id"]

        stream = _payload(await client.call_tool("get_stream_results", {
            "result_id": rid, "stream_id": "vapor",
        }))
        assert stream["success"]
        assert stream["stream"]["mass_flow_kg_hr"] > 0
        assert stream["stream"]["temperature_K"] > 300
        assert stream["stream"]["pressure_Pa"] > 0
        assert "Water" in stream["stream"]["component_mass_flow_kg_hr"]
        assert "Water" in stream["stream"]["component_molar_flow_kmol_hr"]

        unit = _payload(await client.call_tool("get_unit_results", {
            "result_id": rid, "unit_id": "P1",
        }))
        assert unit["success"]
        assert unit["unit"]["type"] == "Pump"
        assert unit["unit"]["power_utility"]["rate_kW"] >= 0

        tea = _payload(await client.call_tool("get_tea_results", {"result_id": rid}))
        assert tea["success"] and tea["tea"]["MSP_usd_per_kg"] > 0

        opt = _payload(await client.call_tool("optimize", {
            "result_id": rid,
            "variables": [
                {"unit_id": "H1", "attr": "T", "bounds": [345, 372]},
                {"unit_id": "F1", "attr": "V", "bounds": [0.35, 0.65]},
            ],
            "objective": "MSP", "maxiter": 6,
        }))
        assert opt["success"] and opt["objective"] == "MSP"
        assert opt["objective_value"] <= tea["tea"]["MSP_usd_per_kg"] + 1e-6

        diag = _payload(await client.call_tool("get_flowsheet_diagram",
                                               {"result_id": rid, "include_image_base64": True}))
        assert diag["success"]
        assert {n["id"] for n in diag["nodes"]} == {"H1", "F1", "P1"}
        assert len(diag["edges"]) >= 2
        # Graph structure is mandatory; rendered image is best-effort because
        # Graphviz availability/behavior varies by runtime image.
        if diag.get("image_base64") is not None:
            assert len(diag["image_base64"]) > 100

        await client.call_tool("dispose_result", {"result_id": rid})


@pytest.mark.asyncio
async def test_ideal_flash_contract():
    spec = {
        "thermo": ["Water", "Ethanol"],
        "thermo_model": "ideal",
        "streams": [{
            "id": "feed", "flows": {"Water": 50, "Ethanol": 50},
            "units": "kmol/hr", "T": 363.15, "P": 101325,
        }],
        "units": [{
            "type": "Flash", "id": "F1", "ins": ["feed"],
            "outs": ["vapor", "liquid"], "params": {"T": 363.15, "P": 101325},
        }],
        "attach_tea": False,
    }
    async with Client(mcp) as client:
        built = _payload(await client.call_tool("build_system_from_spec", {"spec": spec}))
        assert built["success"]
        assert built["thermo"]["model"] == "ideal"
        assert built["thermo"]["Gamma"] == "IdealActivityCoefficients"
        assert built["thermo"]["Phi"] == "IdealFugacityCoefficients"
        assert built["thermo"]["PCF"] == "MockPoyintingCorrectionFactors"
        rid = built["result_id"]

        vle = _payload(await client.call_tool("get_vle_results", {
            "result_id": rid, "stream_id": "feed", "pressure_Pa": 100_000,
        }))
        assert vle["success"]
        assert vle["vle"]["components"] == ["Water", "Ethanol"]
        assert vle["vle"]["bubble"]["liquid_mole_fraction"]["Water"] == pytest.approx(0.5, abs=1e-12)

        vapor = _payload(await client.call_tool("get_stream_results", {
            "result_id": rid, "stream_id": "vapor",
        }))["stream"]
        liquid = _payload(await client.call_tool("get_stream_results", {
            "result_id": rid, "stream_id": "liquid",
        }))["stream"]
        beta = vapor["molar_flow_kmol_hr"] / (
            vapor["molar_flow_kmol_hr"] + liquid["molar_flow_kmol_hr"]
        )
        y_water = vapor["component_molar_flow_kmol_hr"]["Water"] / vapor["molar_flow_kmol_hr"]
        x_water = liquid["component_molar_flow_kmol_hr"]["Water"] / liquid["molar_flow_kmol_hr"]
        assert beta == pytest.approx(0.7219168857, abs=1e-7)
        assert y_water == pytest.approx(0.4450775696, abs=1e-7)
        assert x_water == pytest.approx(0.6425812206, abs=1e-7)
        await client.call_tool("dispose_result", {"result_id": rid})


@pytest.mark.asyncio
async def test_sanitation_flow():
    async with Client(mcp) as client:
        built = _payload(await client.call_tool("build_sanitation_system", {"spec": {
            "flow_tot": 1000,
            "concentrations": {"S_F": 200, "X_B_Subst": 150, "S_NH4": 40, "S_PO4": 8},
            "N_recovery": 0.6, "P_recovery": 0.8,
        }}))
        assert built["success"]
        rid = built["result_id"]
        assert built["summary"]["influent"]["COD_mgL"] > 0

        ww = _payload(await client.call_tool("get_wastewater_results", {"result_id": rid}))
        assert ww["success"]
        assert ww["removal_pct"]["TN"] > 0
        assert ww["recovered_kg_hr"]["P_as_PO4"] > 0

        await client.call_tool("dispose_result", {"result_id": rid})


@pytest.mark.asyncio
async def test_health_and_models():
    async with Client(mcp) as client:
        health = _payload(await client.call_tool("health_check", {}))
        assert health["success"] and "biosteam" in health["versions"]
        models = _payload(await client.call_tool("list_biorefinery_models", {}))
        assert "cornstover" in models["models"]


@pytest.mark.asyncio
async def test_build_tea_uncertainty_flow():
    async with Client(mcp) as client:
        built = _payload(await client.call_tool("build_system", {"model_name": "cornstover"}))
        assert built["success"]
        rid = built["result_id"]

        tea = _payload(await client.call_tool("get_tea_results", {"result_id": rid}))
        assert tea["success"] and 0.4 < tea["tea"]["MSP_usd_per_kg"] < 1.2

        unc = _payload(await client.call_tool("run_uncertainty", {
            "result_id": rid,
            "parameters": [
                {"name": "Feedstock price", "target": "feedstock_price",
                 "dist": ["triangle", 0.03, 0.0516, 0.08]},
                {"name": "IRR", "target": "IRR", "dist": ["uniform", 0.08, 0.15]},
            ],
            "N": 40,
        }))
        assert unc["success"]
        d = unc["distribution"]
        assert d["P5"] < d["P50"] < d["P95"]

        sens = _payload(await client.call_tool("run_sensitivity", {"result_id": rid}))
        assert sens["success"] and len(sens["spearman"]) == 2

        disp = _payload(await client.call_tool("dispose_result", {"result_id": rid}))
        assert disp["success"]
