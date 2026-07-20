"""
Uncertainty/sensitivity sanity check (SDAI reliability pass, WS3.3).

Not a correctness benchmark (there's no external reference for a Monte Carlo
distribution) -- a sanity check that `run_uncertainty`/`run_sensitivity` on
the cornstover reference model produce internally consistent, non-degenerate,
physically sensible output:
  - percentiles are properly ordered and bracket the deterministic MSP;
  - feedstock price (the dominant cost driver) has a strong positive
    correlation with MSP;
  - electricity price has a negative correlation, consistent with cornstover
    being a net power EXPORTER (higher electricity price -> more revenue from
    exported power -> lower breakeven MSP needed).

Run:  pytest test_uncertainty_sanity.py    (in envShilab; slower -- runs a
full N=200 Monte Carlo on the real cornstover biorefinery)
"""
from __future__ import annotations

import pytest

from engine import BioSTEAMEngine


@pytest.fixture(scope="module")
def cornstover_result():
    eng = BioSTEAMEngine()
    built = eng.build_system("cornstover")
    assert built["success"], built
    rid = built["result_id"]
    assert eng.simulate_system(rid)["success"]
    return eng, rid


def test_monte_carlo_brackets_deterministic_msp(cornstover_result):
    eng, rid = cornstover_result
    tea = eng.get_tea_results(rid)
    assert tea["success"], tea
    deterministic_msp = tea["tea"]["MSP_usd_per_kg"]

    unc = eng.run_uncertainty(rid, parameters=[
        {"name": "feedstock_price", "target": "feedstock_price",
         "dist": ["triangle", 0.03, 0.05, 0.08]},
        {"name": "elec_price", "target": "electricity_price",
         "dist": ["uniform", 0.03, 0.08]},
    ], N=200, seed=42)
    assert unc["success"], unc

    dist = unc["distribution"]
    assert dist["P5"] < dist["P50"] < dist["P95"], (
        f"Percentiles not properly ordered: {dist}"
    )
    # deterministic MSP should fall within (or very near) the sampled range --
    # a wildly off deterministic value vs. the MC envelope would indicate the
    # two code paths (deterministic TEA vs. Model-based MC) have diverged.
    assert dist["P5"] * 0.5 < deterministic_msp < dist["P95"] * 1.5


def test_sensitivity_reflects_expected_cost_drivers(cornstover_result):
    eng, rid = cornstover_result
    unc = eng.run_uncertainty(rid, parameters=[
