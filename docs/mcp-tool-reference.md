# MCP Tool Reference

Complete reference for the **biosteam-qsdsan** MCP server (`Biosteam/mcp`). 14 tools.
Every tool returns the shared envelope: `{"success": true, ...}` on success or
`{"success": false, "error": "..."}` on failure.

Signatures below are the live server's (`*` = required). A typical session:
`health_check` â†’ `build_*` â†’ analysis tools (`get_*`, `run_*`, `optimize`) â†’ `dispose_result`.

---

## Meta

### `health_check`
Confirm BioSTEAM/thermosteam/QSDsan import and report versions. Call first.
- **Params:** none
- **Returns:** `{success, versions: {biosteam, thermosteam, qsdsan}}`

### `list_biorefinery_models`
List published biorefinery models `build_system` can load.
- **Params:** none
- **Returns:** `{success, models: [str]}` â€” e.g. `["cornstover","lipidcane","sugarcane","corn"]`

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
- **Example:** `build_system(model_name="cornstover")` â†’ `result_id`, 68 units.

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
