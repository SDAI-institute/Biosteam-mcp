# MCP Tool Reference

Complete reference for the **biosteam-qsdsan** MCP server (`Biosteam/mcp`). 14 tools.
Every tool returns the shared envelope: `{"success": true, ...}` on success or
`{"success": false, "error": "..."}` on failure.

Signatures below are the live server's (`*` = required). A typical session:
`health_check` → `build_*` → analysis tools (`get_*`, `run_*`, `optimize`) → `dispose_result`.

---

## Meta

### `health_check`
Confirm BioSTEAM/thermosteam/QSDsan import and report versions. Call first.
- **Params:** none
- **Returns:** `{success, versions: {biosteam, thermosteam, qsdsan}}`

### `list_biorefinery_models`
List published biorefinery models `build_system` can load.
- **Params:** none
- **Returns:** `{success, models: [str]}` — e.g. `["cornstover","lipidcane","sugarcane","corn"]`

### `dispose_result`
Free a stored result.
- **Params:** `result_id*: string`
- **Returns:** `{success}`

---

## Build

### `build_system`
Load a published biorefinery by name and register it.
- **Params:** `model_name*: string` (e.g. `"cornstover"`)
- **Returns:** `{success, result_id, summary}` where `summary = {system, n_units, installed_equipment_cost_MM, feeds, products}`
- **Example:** `build_system(model_name="cornstover")` → `result_id`, 68 units.

### `build_system_from_spec`
Build a custom BioSTEAM flowsheet from JSON.
- **Params:** `spec*: object`
- **Returns:** `{success, result_id, summary}`
- **Spec shape:**
  ```json
  {
    "thermo": ["Water", "Ethanol"],
    "streams": [
      {"id": "feed", "flows": {"Water": 1000, "Ethanol": 500},
       "units": "kmol/hr", "T": 298.15, "price": 0.10}
    ],
    "units": [
      {"type": "HXutility", "id": "H1", "ins": ["feed"], "outs": ["hot"],
       "params": {"T": 355}},
      {"type": "Flash", "id": "F1", "ins": ["hot"], "outs": ["vapor", "liquid"],
       "params": {"V": 0.5, "P": 101325}},
      {"type": "Pump", "id": "P1", "ins": ["liquid"], "outs": ["bottoms"]}
    ],
    "product": "vapor",
    "attach_tea": true
  }
  ```
  `type` is any BioSTEAM unit class name. A `ConventionalTEA` is attached unless
  `attach_tea` is false. `product` (a stream id) enables MSP.

### `build_sanitation_system`
Build a QSDsan wastewater / nutrient-recovery system.
- **Params:** `spec*: object`
- **Returns:** `{success, result_id, summary}` — `summary.influent` has COD/BOD/TN/TP (mg/L).
- **Spec shape:**
  ```json
  {
    "flow_tot": 1000,
    "concentrations": {"S_F": 200, "X_B_Subst": 150, "S_NH4": 40, "S_PO4": 8},
    "N_recovery": 0.6,
    "P_recovery": 0.8
  }
  ```
  `flow_tot` in m³/hr; `concentrations` in mg/L keyed by QSDsan component IDs.

---

## Analyze

### `simulate_system`
Re-simulate a built system.
- **Params:** `result_id*: string`
- **Returns:** `{success, system, n_units, feeds, products, installed_equipment_cost_MM}`

### `get_tea_results`
Techno-economics of a built system.
- **Params:** `result_id*: string`
- **Returns:** `{success, tea: {FCI_MM, FOC_MM_per_yr, VOC_MM_per_yr, NPV_MM, MSP_usd_per_kg}}`
- **Example:** cornstover → `MSP_usd_per_kg: 0.6926`, `FCI_MM: 359.8`.

### `get_lca_results`
Foreground life-cycle impact given background characterization factors.
- **Params:** `result_id*: string`, `indicator*: string` (e.g. `"GWP"`), `cfs*: object`, `operating_days: integer = 330`
- **`cfs`:** map of feed-stream ID → per-kg factor, plus optional `"electricity"` → per-kWh factor.
- **Returns:** `{success, indicator, total, breakdown}` (annual; `breakdown` per flow).
- **Example:** `get_lca_results(rid, "GWP", {"cornstover": 0.05, "electricity": 0.45})`.

### `get_wastewater_results`
Composite variables, removal efficiency, and recovered nutrient mass (sanitation systems only).
- **Params:** `result_id*: string`
- **Returns:** `{success, influent, effluent, removal_pct: {COD, TN, TP}, recovered_kg_hr: {N_as_NH4, P_as_PO4}}`
- **Example:** TN removal 46.2%, TP 55.7%, P recovered 6.4 kg/hr.

### `run_uncertainty`
Monte Carlo over economic parameters; metric = product MSP.
- **Params:** `result_id*: string`, `parameters*: array`, `N: integer = 200`, `seed: integer = 42`
- **`parameters`:** list of `{name, target, dist}` where `target ∈ {"feedstock_price","electricity_price","IRR"}` and `dist = ["triangle", lo, mid, hi]` or `["uniform", lo, hi]`.
- **Returns:** `{success, metric, N, distribution: {mean, P5, P50, P95}}`
- **Example:**
  ```json
  {"result_id": "sys_cornstover_1", "N": 200,
   "parameters": [
     {"name": "Feedstock price", "target": "feedstock_price", "dist": ["triangle", 0.03, 0.0516, 0.08]},
     {"name": "IRR", "target": "IRR", "dist": ["uniform", 0.08, 0.15]}
   ]}
  ```

### `run_sensitivity`
Spearman ranking of MSP drivers, from the most recent `run_uncertainty` on this result.
- **Params:** `result_id*: string`
- **Returns:** `{success, spearman: [{parameter, rho}]}` (sorted by |rho|)

### `optimize`
Tune unit design/operating variables against a metric (gradient-free differential evolution).
- **Params:** `result_id*: string`, `variables*: array`, `objective: string = "MSP"`, `maxiter: integer = 20`
- **`variables`:** list of `{unit_id, attr, bounds: [lo, hi]}`.
- **`objective`:** `"MSP"` (minimize) or `"NPV"` (maximize). Leaves the system at the optimum.
- **Returns:** `{success, objective, optimum: {"<unit>.<attr>": value}, objective_value}`
- **Example:** minimize MSP over `[{"unit_id":"H1","attr":"T","bounds":[345,372]}, {"unit_id":"F1","attr":"V","bounds":[0.35,0.65]}]` → MSP $0.159/kg.

### `get_flowsheet_diagram`
Flowsheet as a node/edge graph, plus a rendered image when Graphviz is available.
- **Params:** `result_id*: string`, `save_path: string|null`, `fmt: string = "png"`, `include_image_base64: boolean = false`
- **Returns:** `{success, nodes: [{id, type}], edges: [{from, to, stream}], feeds, products, image_path}` (+ `image_base64`, `image_mime` when requested).

---

## Errors

Every tool returns `{"success": false, "error": "<message>"}` rather than raising. Common cases:
- `unknown result_id '...'` — the id was never created or was disposed.
- `this result is not a sanitation system` — `get_wastewater_results` on a non-QSDsan result.
- `MSP objective needs a system with a TEA and a product` — `optimize`/`run_uncertainty` on a system built without a product.
- `unknown unit type '...'` / `could not build system from spec` — bad `build_system_from_spec` input.
- `server is in read-only mode` — a mutating tool while `BIOSTEAM_MCP_READONLY=1`.
