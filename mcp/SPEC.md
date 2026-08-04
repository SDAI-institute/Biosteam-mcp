# BioSTEAM / QSDsan MCP Server — Specification

> Status: **fully implemented and tested.** Spec + engine + FastMCP server (`src/`, 17
> tools) + LCA-Copilot skill are all in place; engine and FastMCP regression tests cover the live surface. Beyond the original spec
> below, the built surface adds custom-flowsheet and QSDsan sanitation tools:
> `build_system_from_spec`, `build_sanitation_system`, `get_wastewater_results`,
> `optimize`, `get_stream_results`, `get_unit_results`, `get_flowsheet_diagram` (with optional inline base64). See `src/tools.py`
> for the live surface.

## Purpose

Expose BioSTEAM / QSDsan process modeling, TEA, LCA, and uncertainty analysis as MCP
tools so an agent — ultimately the **LCA Copilot** — can design, simulate, and evaluate
bioprocess systems programmatically, and reconcile results with the existing openLCA /
Brightway LCA stack.

## Design principles (carried from `openlca_mcp`)

Mirror the mature `openlca_mcp` FastMCP server already in this ecosystem:

- **FastMCP**, `src/` layout, `pyproject.toml` console script (`biosteam-mcp`).
- **Strict `output_schema`** with a shared envelope `{ "success": bool, ... }` and
  `additionalProperties: true`, so responses validate in strict clients.
- **Stateless-friendly result handles**: long-lived objects (a built system, a Monte
  Carlo table) are stored server-side under a `result_id`; tools return the id plus a
  summary; `dispose_result` frees it. (Same lifecycle as `openlca_mcp`'s result store.)
- **Blocking calls offloaded** with `anyio.to_thread` — simulations can take seconds.
- **Read-only vs mutating** tools flagged via `ToolAnnotations`; honor a server
  read-only mode.
- Optional **auth / telemetry** modules reused from the openLCA server pattern.

## Architecture

```
mcp/
├── SPEC.md              # this file
├── engine.py           # framework-facing core (pure python; NO mcp deps) — implemented
├── test_engine.py      # tests for the engine — implemented
└── src/                # FastMCP server wrapping engine.py — LATER PHASE
    ├── app.py          # FastMCP object, auth, telemetry, transport, probe tools
    ├── tools.py        # @mcp.tool wrappers over engine.py
    ├── schemas.py      # shared output envelope helpers
    ├── result_store.py # result_id -> live object registry
    └── __main__.py
```

`engine.py` is deliberately MCP-agnostic: it is the same `summarize_system` contract
from Tier 8, generalized. The FastMCP layer is a thin adapter, which keeps the process-
modeling logic testable without a running MCP client.

## Tool surface

All tools return the shared envelope. `result_id` refers to a stored system/model.

| Tool | Kind | Inputs | Returns |
|------|------|--------|---------|
| `health_check` | read | – | `{success, versions:{biosteam,thermosteam,qsdsan}}` |
| `list_biorefinery_models` | read | – | `{success, models:[name,…]}` (from `biorefineries`) |
| `build_system` | mutate | `model_name` \| `spec` | `{success, result_id, summary}` |
| `simulate_system` | mutate | `result_id` | `{success, converged, units, feeds, products}` |
| `get_stream_results` | read | `result_id`, `stream_id` | `{success, stream:{phase, temperature_K, pressure_Pa, mass_flow_kg_hr, molar_flow_kmol_hr, volumetric_flow_m3_hr, enthalpy_kJ_hr, specific_enthalpy_kJ_kg, component_mass_flow_kg_hr, component_molar_flow_kmol_hr}}` |
| `get_vle_results` | read | `result_id`, `stream_id`, `pressure_Pa` | `{success, vle:{components, overall_mole_fraction, bubble:{temperature_K,liquid_mole_fraction,vapor_mole_fraction}, dew:{...}}}` |
| `get_tea_results` | read | `result_id`, `product?` | `{success, tea:{FCI,FOC,VOC,NPV,MSP}}` |
| `get_lca_results` | read | `result_id`, `indicator`, `cfs`, `allocation?` | `{success, total, intensity, by_allocation}` |
| `run_uncertainty` | mutate | `result_id`, `parameters`, `metrics`, `N` | `{success, distributions:{P5,P50,P95}}` |
| `run_sensitivity` | read | `result_id` (after uncertainty) | `{success, spearman:[{param,rho,pval}]}` |
| `optimize` | mutate | `result_id`, `variables`, `objective`, `bounds` | `{success, optimum:{x,objective}}` |
| `get_flowsheet_diagram` | read | `result_id`, `include_image_base64?` | `{success, nodes, edges, image_path, image_base64?}` |
| `dispose_result` | mutate | `result_id` | `{success}` |

Additional tools built beyond the original table:

| Tool | Kind | Inputs | Returns |
|------|------|--------|---------|
| `build_system_from_spec` | mutate | `spec` (thermo/thermo_model?/streams/units/product) | `{success, result_id, summary, thermo}`; `thermo_model:"ideal"` explicitly installs ideal activity/fugacity coefficients and mock Poynting correction for Raoult-law validation |
| `build_sanitation_system` | mutate | `spec` (flow_tot, concentrations, N/P recovery) | `{success, result_id, summary}` |
| `get_wastewater_results` | read | `result_id` | `{success, influent, effluent, removal_pct, recovered_kg_hr}` |
| `get_unit_results` | read | `result_id`, `unit_id` | `{success, unit:{type, design_results, power_utility, heat_utilities, costs}}` |

### Example: `get_tea_results`

```jsonc
// request
{ "result_id": "sys_ab12", "product": "ethanol" }
// response
{ "success": true,
  "tea": { "FCI_MM": 359.8, "FOC_MM_per_yr": 9.8, "VOC_MM_per_yr": 72.6,
           "NPV_MM": 0.0, "MSP_usd_per_kg": 0.6926 } }
```

The value shapes are exactly what `engine.summarize_system` already returns (see Tier 8
and `engine.py`), so the schema is grounded in working code, not aspiration.

## Output envelope

```python
def ok(**data):    return {"success": True, **data}
def err(message):  return {"success": False, "error": message}
```

`output_schema`: `{ "type": "object", "required": ["success"],
"additionalProperties": true }`.

## Server instructions (for the model)

> Use these tools for BioSTEAM/QSDsan bioprocess design, TEA, and LCA. Call
> `health_check` first. `build_system` returns a `result_id` you pass to the analysis
> tools. `build_*`, `simulate_*`, `run_*`, and `optimize` mutate server state; honor
> read-only mode. Call `dispose_result` when done. For LCA, supply background
> characterization factors (`cfs`); the server computes the foreground inventory.

## Integration into LCA Copilot (later)

Add `LCA copilot/skills/biosteam/` (`SKILL.md` + `skill.json`) mirroring
`skills/openlca-ipc/`, registering this MCP so the copilot can:
1. build/simulate a bioprocess (BioSTEAM/QSDsan),
2. get its TEA + foreground LCA inventory,
3. hand that inventory to the existing openLCA/Brightway skills for a formal
   background LCA — the seam demonstrated in the
   [cross-framework LCA case study](../case_studies/cross_framework_lca/).

## Dependencies (server phase)

`mcp>=1.28`, `fastmcp>=3.4`, `biosteam`, `qsdsan`, `biorefineries`, `pydantic>=2`,
`anyio`; optional `uvicorn`/`starlette` (HTTP), telemetry extras — matching
`openlca_mcp/pyproject.toml`.
