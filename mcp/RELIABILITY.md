# BioSTEAM MCP â€” Reliability Verification (SDAI reliability pass)

**Method:** independently tested `biosteam_mcp` for correctness. **Critical
framing, established before any testing began:** BioSTEAM is a
process-simulation / techno-economic-analysis (TEA) tool, **not** an LCA
engine â€” it computes capital/operating cost and mass/energy balances, not
impact categories from an LCI. It has no LCA benchmark to be judged against
and was never compared to Brightway or openLCA on "accuracy." Instead, its
correctness was judged against **its own domain**: does the MCP layer
faithfully proxy BioSTEAM's own simulation output, and does its (much
narrower) foreground-LCA arithmetic compute correctly?

**Bottom line: no defects found.** All three targeted checks passed
(reference-model fidelity, foreground-LCA hand-calc, uncertainty/sensitivity
sanity), on top of the pre-existing 10-test suite which continues to pass.

## Environment

- Runs in the `envShilab` conda environment (Python 3.11.9) â€” the pinned env
  for `biosteam`/`qsdsan`/`biorefineries`.
- Original test suite (`test_engine.py`, `test_server.py`): **10/10 passed**
  (re-confirmed at the start of this pass; only benign `thermosteam`
  registry-rename warnings).
- Post-hardening: **15/15 passed** (10 original + 5 new), ~92s total (the new
  tests exercise the real `biorefineries.cornstover` reference model, which is
  the slow part).

## WS3.1 â€” Reference-model fidelity (MCP layer vs. direct BioSTEAM API)

The engine's `build_system`/`simulate_system`/`get_tea_results` path is a thin
wrapper: `build_system` does `importlib.import_module("biorefineries.<name>")`
+ `mod.load()`, then locates the system/TEA/product objects via a small
`_find_attr` name-heuristic (`[f"{model}_sys", "sys", "system"]`, etc.).
`get_tea_results` reads `tea.FCI`/`.FOC`/`.VOC`/`.NPV`/`.solve_price()`
directly â€” very little translation logic, but the attribute-discovery
heuristic is exactly the kind of place a silent wrong-object bug could hide.

**Test design:** ran the MCP engine path and a hand-written direct API call
(`mod.sys`, `mod.tea`, `mod.ethanol`, confirmed to be the actual attribute
names `biorefineries.cornstover` exposes after `load()`) in **two separate
subprocesses** â€” not two imports in the same process, which would trivially
"match" by sharing Python's cached module object rather than proving anything
about the wrapper.

| TEA metric (cornstover) | Via MCP engine | Direct BioSTEAM API | Match |
|---|---|---|---|
| FCI ($MM) | âœ“ | âœ“ | âœ… identical |
| FOC ($MM/yr) | âœ“ | âœ“ | âœ… identical |
| VOC ($MM/yr) | âœ“ | âœ“ | âœ… identical |
| NPV ($MM) | âœ“ | âœ“ | âœ… identical |
| MSP ($/kg) | âœ“ | âœ“ | âœ… identical |

