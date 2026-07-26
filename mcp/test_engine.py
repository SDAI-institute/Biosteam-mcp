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

    result = engine.get_stream_results(rid, "product")
    assert result["success"] is True
    stream = result["stream"]
    assert stream["mass_flow_kg_hr"] == pytest.approx(150.0, abs=1e-8)
    assert stream["component_mass_flow_kg_hr"]["Water"] == pytest.approx(150.0, abs=1e-8)
    assert stream["component_molar_flow_kmol_hr"]["Water"] == pytest.approx(stream["molar_flow_kmol_hr"], abs=1e-10)
    assert stream["temperature_K"] == pytest.approx(298.15, abs=1e-6)
    assert stream["pressure_Pa"] == pytest.approx(101325, abs=1e-6)
    assert stream["specific_enthalpy_kJ_kg"] is not None
    engine.dispose_result(rid)


def test_ideal_thermo_flash_metadata_and_phase_split(engine):
    built = engine.build_system_from_spec({
        "id": "ideal_flash_probe",
        "thermo": ["Water", "Ethanol"],
        "thermo_model": "ideal",
        "streams": [
            {"id": "feed", "flows": {"Water": 50, "Ethanol": 50},
             "units": "kmol/hr", "T": 363.15, "P": 101325},
        ],
        "units": [
            {"type": "Flash", "id": "F1", "ins": ["feed"],
             "outs": ["vapor", "liquid"], "params": {"T": 363.15, "P": 101325}},
        ],
        "attach_tea": False,
    })
    assert built["success"] is True
    thermo = built["thermo"]
    assert thermo["model"] == "ideal"
    assert thermo["Gamma"] == "IdealActivityCoefficients"
    assert thermo["Phi"] == "IdealFugacityCoefficients"
    assert thermo["PCF"] == "MockPoyintingCorrectionFactors"
    assert thermo["chemicals"] == ["Water", "Ethanol"]

    rid = built["result_id"]
    vle = engine.get_vle_results(rid, "feed", 100_000)
    assert vle["success"] is True
    assert vle["vle"]["components"] == ["Water", "Ethanol"]
    assert vle["vle"]["bubble"]["liquid_mole_fraction"]["Water"] == pytest.approx(0.5, abs=1e-12)
    assert 350 < vle["vle"]["bubble"]["temperature_K"] < 370
    assert 0 < vle["vle"]["bubble"]["vapor_mole_fraction"]["Water"] < 1
    vapor = engine.get_stream_results(rid, "vapor")["stream"]
    liquid = engine.get_stream_results(rid, "liquid")["stream"]
    total_mol = vapor["molar_flow_kmol_hr"] + liquid["molar_flow_kmol_hr"]
    beta = vapor["molar_flow_kmol_hr"] / total_mol
    y_water = vapor["component_molar_flow_kmol_hr"]["Water"] / vapor["molar_flow_kmol_hr"]
    x_water = liquid["component_molar_flow_kmol_hr"]["Water"] / liquid["molar_flow_kmol_hr"]
    assert beta == pytest.approx(0.7219168857, abs=1e-7)
    assert y_water == pytest.approx(0.4450775696, abs=1e-7)
    assert x_water == pytest.approx(0.6425812206, abs=1e-7)
    engine.dispose_result(rid)


def test_unknown_thermo_model_rejected(engine):
    built = engine.build_system_from_spec({
        "thermo": ["Water"],
        "thermo_model": "not-a-real-model",
        "streams": [],
        "units": [],
        "attach_tea": False,
    })
    assert built["success"] is False
    assert "unknown thermo_model" in built["error"]


def test_unit_results_for_custom_pump(engine):
    built = engine.build_system_from_spec({
        "id": "pump_probe",
        "thermo": ["Water"],
        "streams": [
            {"id": "feed", "flows": {"Water": 100}, "units": "kg/hr", "T": 298.15, "P": 101325},
        ],
        "units": [
            {"type": "Pump", "id": "P1", "ins": ["feed"], "outs": ["product"],
             "params": {"P": 1_000_000}},
        ],
        "product": "product",
        "attach_tea": False,
    })
    assert built["success"] is True
    rid = built["result_id"]

    result = engine.get_unit_results(rid, "P1")
    assert result["success"] is True
    unit = result["unit"]
    assert unit["type"] == "Pump"
    assert unit["inlet_streams"] == ["feed"]
    assert unit["outlet_streams"] == ["product"]
    assert 0.3 < unit["design_results"]["Efficiency"] < 0.5
    assert unit["power_utility"]["rate_kW"] == pytest.approx(0.07113047, rel=2e-4)

    product = engine.get_stream_results(rid, "product")["stream"]
    assert product["mass_flow_kg_hr"] == pytest.approx(100.0, abs=1e-8)
    assert product["pressure_Pa"] == pytest.approx(1_000_000.0, abs=1e-6)
    # BioSTEAM's Pump changes pressure in _run; power is accounted as a utility
    # rather than being injected into the outlet stream enthalpy.
    assert product["temperature_K"] == pytest.approx(298.15, abs=1e-6)
    engine.dispose_result(rid)


def test_unknown_result_id(engine):
    assert engine.get_tea_results("nope")["success"] is False
    assert engine.get_stream_results("nope", "x")["success"] is False
    assert engine.get_vle_results("nope", "x", 101325)["success"] is False
    assert engine.get_unit_results("nope", "P1")["success"] is False
    assert engine.dispose_result("nope")["success"] is False
