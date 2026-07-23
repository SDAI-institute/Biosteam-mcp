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
