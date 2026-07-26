"""Tests for the MCP reference engine.

Run:  pytest mcp/test_engine.py    (in envShilab)

These assert the engine's contract against the real BioSTEAM cornstover model, so they
double as a regression check that the environment still works.
"""

from __future__ import annotations

import pytest

from engine import BioSTEAMEngine


@pytest.fixture(scope="module")
def engine():
    return BioSTEAMEngine()


def test_health_check(engine):
    res = engine.health_check()
    assert res["success"] is True
    assert "biosteam" in res["versions"]


def test_list_models(engine):
    res = engine.list_biorefinery_models()
    assert res["success"] is True
    assert "cornstover" in res["models"]


def test_build_and_tea(engine):
    built = engine.build_system("cornstover")
    assert built["success"] is True
    rid = built["result_id"]
    assert built["summary"]["n_units"] > 50

    tea = engine.get_tea_results(rid)
    assert tea["success"] is True
    # MSP for cornstover ethanol is ~$0.69/kg; allow a wide band for version drift.
    assert 0.4 < tea["tea"]["MSP_usd_per_kg"] < 1.2
    assert tea["tea"]["FCI_MM"] > 100

    engine.dispose_result(rid)


def test_lca_contract(engine):
    built = engine.build_system("cornstover")
    rid = built["result_id"]
    lca = engine.get_lca_results(rid, "GWP", {"cornstover": 0.05, "electricity": 0.45})
    assert lca["success"] is True
    assert lca["indicator"] == "GWP"
    assert "cornstover" in lca["breakdown"]
    engine.dispose_result(rid)


def test_stream_results_for_custom_mixer(engine):
    built = engine.build_system_from_spec({
        "id": "stream_probe",
        "thermo": ["Water"],
        "streams": [
            {"id": "a", "flows": {"Water": 100}, "units": "kg/hr", "T": 298.15, "P": 101325},
            {"id": "b", "flows": {"Water": 50}, "units": "kg/hr", "T": 298.15, "P": 101325},
        ],
        "units": [{"type": "Mixer", "id": "M1", "ins": ["a", "b"], "outs": ["product"], "params": {}}],
        "product": "product",
        "attach_tea": False,
    })
    assert built["success"] is True
    rid = built["result_id"]

