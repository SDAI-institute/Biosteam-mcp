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
        {"name": "feedstock_price", "target": "feedstock_price",
         "dist": ["triangle", 0.03, 0.05, 0.08]},
        {"name": "elec_price", "target": "electricity_price",
         "dist": ["uniform", 0.03, 0.08]},
    ], N=200, seed=42)
    assert unc["success"], unc

    sens = eng.run_sensitivity(rid)
    assert sens["success"], sens
    by_param = {row["parameter"]: row["rho"] for row in sens["spearman"]}

    feedstock_rho = next(v for k, v in by_param.items() if "feedstock" in k.lower())
    elec_rho = next(v for k, v in by_param.items() if "elec" in k.lower())

    # Feedstock is cornstover's dominant cost driver: strong positive correlation.
    assert feedstock_rho > 0.7, f"Expected strong positive rho, got {feedstock_rho}"
    # Cornstover exports surplus electricity: higher price -> more revenue ->
    # lower breakeven MSP -> negative correlation.
    assert elec_rho < 0, f"Expected negative rho for electricity price, got {elec_rho}"


def test_uncertainty_restores_economic_state():
    """Monte Carlo must not leak sampled economics into later analyses."""
    import biosteam as bst

    eng = BioSTEAMEngine()
    built = eng.build_system("cornstover")
    assert built["success"], built
    entry = eng._store[built["result_id"]]
    feedstock, tea, product = entry["feedstock"], entry["tea"], entry["product"]
    tea_before = eng.get_tea_results(built["result_id"])
    assert tea_before["success"], tea_before
    before = (float(feedstock.price), float(bst.PowerUtility.price),
              float(tea.IRR), float(product.price))

    unc = eng.run_uncertainty(built["result_id"], parameters=[
        {"name": "feedstock_price", "target": "feedstock_price", "dist": ["uniform", 0.091, 0.092]},
        {"name": "elec_price", "target": "electricity_price", "dist": ["uniform", 0.123, 0.124]},
        {"name": "irr", "target": "IRR", "dist": ["uniform", 0.201, 0.202]},
    ], N=8, seed=7)
    assert unc["success"], unc

    after = (float(feedstock.price), float(bst.PowerUtility.price),
             float(tea.IRR), float(product.price))
    assert after == pytest.approx(before, rel=0, abs=1e-12)

    tea_after = eng.get_tea_results(built["result_id"])
    assert tea_after["success"], tea_after
    for key in ("FCI_MM", "FOC_MM_per_yr", "VOC_MM_per_yr", "MSP_usd_per_kg"):
        assert tea_after["tea"][key] == pytest.approx(tea_before["tea"][key], rel=0, abs=1e-9)


def test_uncertainty_does_not_contaminate_named_model_rebuild():
    """A later named-model build must retain the pre-uncertainty baseline."""
    import biosteam as bst

    eng = BioSTEAMEngine()
    first = eng.build_system("cornstover")
    assert first["success"], first
    first_rid = first["result_id"]
    first_tea = eng.get_tea_results(first_rid)
    assert first_tea["success"], first_tea
    first_entry = eng._store[first_rid]
    first_state = (
        float(first_entry["feedstock"].price), float(bst.PowerUtility.price),
        float(first_entry["tea"].IRR), float(first_entry["product"].price),
    )

    unc = eng.run_uncertainty(first_rid, parameters=[
        {"name": "feedstock_price", "target": "feedstock_price",
         "dist": ["triangle", 0.03, 0.05, 0.08]},
        {"name": "elec_price", "target": "electricity_price",
         "dist": ["uniform", 0.03, 0.08]},
    ], N=40, seed=42)
    assert unc["success"], unc

    second = eng.build_system("cornstover")
    assert second["success"], second
    second_rid = second["result_id"]
    second_tea = eng.get_tea_results(second_rid)
    assert second_tea["success"], second_tea
    second_entry = eng._store[second_rid]
    second_state = (
        float(second_entry["feedstock"].price), float(bst.PowerUtility.price),
        float(second_entry["tea"].IRR), float(second_entry["product"].price),
    )

    assert second["summary"] == first["summary"]
    for key in ("FCI_MM", "FOC_MM_per_yr", "VOC_MM_per_yr", "MSP_usd_per_kg"):
        assert second_tea["tea"][key] == pytest.approx(first_tea["tea"][key], rel=0, abs=1e-9)
    assert second_state == pytest.approx(first_state, rel=0, abs=1e-12)
