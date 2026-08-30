# BioSTEAM + QSDsan Ecosystem — Master Checklist

> Legend: `[ ]` todo · `[~]` in progress / partial · `[x]` done
> This file is the source-of-truth progress tracker. Flip boxes as tiers land.

## Phase 0 — Scaffold & environment
- [x] Create the folder tree under `Biosteam/`
- [x] `environment/requirements.txt`
- [x] `environment/setup.md`
- [x] `environment/verify_install.py`
- [x] Install stack into **envShilab** (biosteam 2.51.19, qsdsan 1.4.3, thermosteam 0.51.17)
- [x] Register Jupyter kernel `Python (envShilab)`
- [x] `verify_install.py` runs clean; runtime smoke test passed (cornstover MSP $0.693/kg)
- [x] `environment/build_notebook.py` engine (percent-.py → executed .ipynb)
- [x] Top-level `README.md`
- [x] `CHECKLIST.md` (this file)

## Phase 1 — Tutorials (author + execute each tier)
Each tier = `README.md` (concepts) + `NN_*.ipynb` (executed) + `NN_*.py` (script).

- [x] Tier 0 — `00_foundations` — object model, first end-to-end flowsheet
- [x] Tier 1 — `01_thermosteam` — chemicals, thermo, streams, equilibrium
- [x] Tier 2 — `02_unit_operations` — built-in units, specs, custom Unit
- [x] Tier 3 — `03_systems_flowsheets` — systems, recycle, convergence, specs
- [x] Tier 4 — `04_tea` — TEA subclassing, CAPEX/OPEX, NPV, MSP
- [x] Tier 5 — `05_lca` — characterization factors, allocation, impacts
- [x] Tier 6 — `06_qsdsan` — SanUnit, WasteStream, resource recovery
- [x] Tier 7 — `07_uncertainty_optimization` — Model/Parameter/Metric, MC, sensitivity, optimization
- [x] Tier 8 — `08_expert_integration` — cross-framework, results contract, MCP-facing API
- [x] `reference/` — cheat-sheet, glossary, troubleshooting (version gotchas)

## Phase 2 — Case studies (executed, real outputs)
- [x] `biorefinery_cornstover_ethanol` — full TEA (MSP $0.69/kg, FCI $360MM)
- [x] `biodiesel_lipidcane` — co-product allocation (mass/energy/economic), IRR 20.8%
- [x] `qsdsan_sanitation_recovery` — Monte Carlo uncertainty + sensitivity
- [x] `cross_framework_lca` — impacts reconciled across tools (exact)
- [x] `optimization_uncertainty` — optimization (−18% MSP) + Monte Carlo at optimum

## Phase 3 — MCP (spec now, implement later)
- [x] `mcp/SPEC.md` — tools, schemas, transport, integration plan
- [x] `mcp/engine.py` — framework-facing core (MCP-agnostic, mirrors Tier 8 contract)
- [x] `mcp/src/` — FastMCP server (app + tools + schemas), mirrors `openlca_mcp`
- [x] 14 tools: build_system / build_system_from_spec / **build_sanitation_system** /
      simulate / get_tea / get_lca / **get_wastewater_results** / run_uncertainty /
      run_sensitivity / optimize / get_flowsheet_diagram (+**base64**) / dispose + probes
- [x] `mcp/test_engine.py` + `mcp/test_server.py` — 10 tests passing (engine + in-memory client)
- [x] `LCA copilot/skills/biosteam/` skill wiring (`SKILL.md` + `skill.json`, loader-verified)
- [ ] Future: QSDsan **dynamic** sim (ASM/ADM); sanitation uncertainty; register server in live copilot config

## Phase 4 — Documentation
- [x] `docs/index.md` — documentation home / TOC
- [x] `docs/getting-started.md` — install, tutorials, run server, connect client
- [x] `docs/architecture.md` (+ `architecture.svg`) — layers, results contract, LCA seam
- [x] `docs/mcp-tool-reference.md` — all 14 tools (introspected from the live server)
- [x] `docs/engine-api.md` — `engine.py` API reference
- [x] Top `README.md` links to `docs/`; all doc links verified
