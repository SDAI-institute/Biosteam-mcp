# BioSTEAM MCP — Reliability Verification (SDAI reliability pass)

**Method:** independently tested `biosteam_mcp` for correctness. **Critical
framing, established before any testing began:** BioSTEAM is a
process-simulation / techno-economic-analysis (TEA) tool, **not** an LCA
engine — it computes capital/operating cost and mass/energy balances, not
impact categories from an LCI. It has no LCA benchmark to be judged against
and was never compared to Brightway or openLCA on "accuracy." Instead, its
correctness was judged against **its own domain**: does the MCP layer
faithfully proxy BioSTEAM's own simulation output, and does its (much
narrower) foreground-LCA arithmetic compute correctly?

**Bottom line: no defects found.** All three targeted checks passed
(reference-model fidelity, foreground-LCA hand-calc, uncertainty/sensitivity
sanity), on top of the pre-existing 10-test suite which continues to pass.

## Environment

- Runs in the `envShilab` conda environment (Python 3.11.9) — the pinned env
  for `biosteam`/`qsdsan`/`biorefineries`.
- Original test suite (`test_engine.py`, `test_server.py`): **10/10 passed**
  (re-confirmed at the start of this pass; only benign `thermosteam`
  registry-rename warnings).
- Post-hardening: **15/15 passed** (10 original + 5 new), ~92s total (the new
  tests exercise the real `biorefineries.cornstover` reference model, which is
  the slow part).

## WS3.1 — Reference-model fidelity (MCP layer vs. direct BioSTEAM API)

The engine's `build_system`/`simulate_system`/`get_tea_results` path is a thin
wrapper: `build_system` does `importlib.import_module("biorefineries.<name>")`
+ `mod.load()`, then locates the system/TEA/product objects via a small
`_find_attr` name-heuristic (`[f"{model}_sys", "sys", "system"]`, etc.).
`get_tea_results` reads `tea.FCI`/`.FOC`/`.VOC`/`.NPV`/`.solve_price()`
directly — very little translation logic, but the attribute-discovery
heuristic is exactly the kind of place a silent wrong-object bug could hide.

**Test design:** ran the MCP engine path and a hand-written direct API call
(`mod.sys`, `mod.tea`, `mod.ethanol`, confirmed to be the actual attribute
names `biorefineries.cornstover` exposes after `load()`) in **two separate
subprocesses** — not two imports in the same process, which would trivially
"match" by sharing Python's cached module object rather than proving anything
about the wrapper.

| TEA metric (cornstover) | Via MCP engine | Direct BioSTEAM API | Match |
|---|---|---|---|
| FCI ($MM) | ✓ | ✓ | ✅ identical |
| FOC ($MM/yr) | ✓ | ✓ | ✅ identical |
| VOC ($MM/yr) | ✓ | ✓ | ✅ identical |
| NPV ($MM) | ✓ | ✓ | ✅ identical |
| MSP ($/kg) | ✓ | ✓ | ✅ identical |

(`test_reference_model_fidelity.py`) — the MCP layer introduces no
translation error for this reference model.

## WS3.2 — Foreground LCA hand-calc

`get_lca_results` computes `contribution = feed_mass_flow × operating_hours ×
characterization_factor` per feed, plus an optional
`electricity_kWh × cf` term. Built a minimal custom system via
`build_system_from_spec` with a known feed flow (100 kg/hr) and, separately, a
known power draw (a `Pump` unit), and hand-verified both terms:

| Term | Hand calc | Engine result | Match |
|---|---|---|---|
| Feed: 100 kg/hr × 7920 h × 2.5 | 1,980,000.0 | **1,980,000.0** | ✅ exact |
| Electricity: 0.3208 kW × 7920 h × 0.5 | 1270.35 (rounds to 1270.4) | **1270.4** | ✅ exact |

(`test_lca_hand_calc.py`) — both arithmetic paths are correct.

## WS3.3 — Uncertainty/sensitivity sanity (cornstover reference model)

Not a correctness benchmark (no external reference exists for a Monte Carlo
distribution) — a sanity check that the results are internally consistent and
physically sensible:

- **Percentile ordering:** P5 (0.6253) < P50 (0.7026) < P95 (0.7901) $/kg MSP,
  correctly bracketing the deterministic MSP (0.6927).
- **Feedstock price** (cornstover's dominant cost driver): Spearman ρ = 0.952
  with MSP — strongly positive, as expected.
- **Electricity price:** ρ = -0.29 — **negative**, and correctly so: cornstover
  is a net power *exporter* (excess electricity sold), so a higher price
  *increases revenue* and *lowers* the breakeven MSP.

(`test_uncertainty_sanity.py`) — the tool's internal logic is coherent and its
directional relationships make physical sense.

## Findings

**No defects.** The MCP layer's wrapping logic, foreground-LCA arithmetic, and
uncertainty/sensitivity pipeline all check out against independent
verification. No fixes were required in `engine.py` or `mcp/src/`.

## What changed

- `test_reference_model_fidelity.py` (new): MCP-vs-direct-API subprocess
  comparison on the cornstover reference model.
- `test_lca_hand_calc.py` (new): feed + electricity contribution hand-calc
  checks on a minimal custom system.
- `test_uncertainty_sanity.py` (new): percentile-ordering and
  cost-driver-direction sanity on the cornstover model's Monte Carlo/Spearman
  output.

## Handle recovery qualification (0.4.1)

Reconstructible BioSTEAM system handles now persist build provenance as strict JSON rather
than serialized scientific objects. The persisted record includes a SHA-256 checksum and the
exact installed BioSTEAM/ThermoSTEAM/QSDsan runtime versions. A fresh MCP process may lazily
rebuild the original system under the same `result_id` only when that runtime fingerprint
matches.

The recovery state also records deterministic post-build mutations currently made by the
public API: LCA operating hours and optimization-selected unit attributes. Those mutations are
reapplied and the system is re-simulated before the recovered handle becomes available.
Runtime mismatches are refused instead of silently rebuilding under different scientific
software. `dispose_result` removes both the in-memory object and persisted recipe. Result-ID
allocation also checks persisted provenance before issuing a new ID, so a fresh process cannot
overwrite an older recoverable handle merely because its local counter restarted at zero.

Focused regression: 25/25 fast server/engine/job/handle tests passed. The isolated Redis DB 13
restart qualifier additionally proved build -> analyze -> container restart -> reuse the same
`result_id` with identical stream mass/component results -> dispose -> restart -> handle absent.

## Reproduce

```bash
cd Biosteam/mcp
/c/MSI/anaconda3/envs/envShilab/python.exe -m pytest -q   # 15 passed, ~90s
```
