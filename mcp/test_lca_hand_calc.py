"""
Foreground-LCA hand-calc check (SDAI reliability pass, WS3.2).

`BioSTEAMEngine.get_lca_results` computes a purely arithmetic foreground
inventory: for each feed, `contribution = mass_flow * operating_hours * cf`,
plus an optional electricity term `total_power_kW * operating_hours * cf`.
This test builds a minimal custom system with a KNOWN feed mass flow (and,
separately, a known power draw), so both terms can be verified against a
hand calculation independent of the engine's own code.

Run:  pytest test_lca_hand_calc.py    (in envShilab)
"""
from __future__ import annotations

import pytest

from engine import BioSTEAMEngine

HOURS_330_DAYS = 24 * 330  # get_lca_results' default operating_days=330


@pytest.fixture
def engine():
    return BioSTEAMEngine()


def test_feed_contribution_matches_hand_calc(engine):
    spec = {
        "thermo": ["Water"],
        "streams": [{"id": "feed", "flows": {"Water": 100}, "units": "kg/hr"}],
        "units": [{"type": "Mixer", "id": "M1", "ins": ["feed"], "outs": ["product"]}],
        "attach_tea": False,
    }
    built = engine.build_system_from_spec(spec)
    assert built["success"], built
    rid = built["result_id"]
    assert engine.simulate_system(rid)["success"]

    cf = 2.5
    lca = engine.get_lca_results(rid, "GWP", {"feed": cf}, operating_days=330)
    assert lca["success"], lca

    expected = 100 * HOURS_330_DAYS * cf  # 1,980,000.0
    assert lca["total"] == pytest.approx(expected, rel=1e-9)
    assert lca["breakdown"]["feed"] == pytest.approx(expected, rel=1e-9)


def test_electricity_contribution_matches_hand_calc(engine):
    spec = {
        "thermo": ["Water"],
        "streams": [{"id": "feed", "flows": {"Water": 1000}, "units": "kg/hr",
                     "P": 101325}],
        "units": [{"type": "Pump", "id": "P1", "ins": ["feed"], "outs": ["product"],
                   "params": {"P": 5 * 101325}}],
        "attach_tea": False,
    }
    built = engine.build_system_from_spec(spec)
    assert built["success"], built
    rid = built["result_id"]
    assert engine.simulate_system(rid)["success"]

    system = engine._store[rid]["system"]
    kw_rate = sum(u.power_utility.rate for u in system.units if u.power_utility)
    assert kw_rate > 0, "test setup should draw nonzero power"

    elec_cf = 0.5
    lca = engine.get_lca_results(rid, "GWP", {"feed": 0.0, "electricity": elec_cf},
                                 operating_days=330)
    assert lca["success"], lca

    expected = kw_rate * HOURS_330_DAYS * elec_cf
    # the engine rounds breakdown entries to 1 decimal place
    assert lca["breakdown"]["electricity"] == pytest.approx(round(expected, 1), abs=0.05)
    assert lca["total"] == pytest.approx(round(expected, 1), abs=0.05)
