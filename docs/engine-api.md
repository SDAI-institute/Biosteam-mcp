# Engine API (`mcp/engine.py`)

`engine.py` is the MCP-agnostic core. Import and use it directly (no MCP client needed) —
the FastMCP server is a thin wrapper over exactly these methods. Every method returns the
shared envelope: `{"success": True, ...}` or `{"success": False, "error": ...}`.

```python
# from the mcp/ directory:
from engine import BioSTEAMEngine
eng = BioSTEAMEngine()
```

## Class `BioSTEAMEngine`

Stateful: `build_*` methods register a system under a generated `result_id`; analysis
methods take that id. The store is an in-process dict.

| Method | Signature | Returns |
|--------|-----------|---------|
| `health_check` | `()` | `{success, versions}` |
| `list_biorefinery_models` | `()` | `{success, models}` |
| `build_system` | `(model_name)` | `{success, result_id, summary}` |
| `build_system_from_spec` | `(spec)` | `{success, result_id, summary}` |
| `build_sanitation_system` | `(spec)` | `{success, result_id, summary}` |
| `simulate_system` | `(result_id)` | `{success, ...summary}` |
| `get_tea_results` | `(result_id)` | `{success, tea}` |
| `get_lca_results` | `(result_id, indicator, cfs, operating_days=330)` | `{success, indicator, total, breakdown}` |
| `get_wastewater_results` | `(result_id)` | `{success, influent, effluent, removal_pct, recovered_kg_hr}` |
| `run_uncertainty` | `(result_id, parameters, N=200, seed=42)` | `{success, metric, N, distribution}` |
| `run_sensitivity` | `(result_id)` | `{success, spearman}` |
| `optimize` | `(result_id, variables, objective="MSP", seed=1, maxiter=20)` | `{success, objective, optimum, objective_value}` |
| `get_flowsheet_diagram` | `(result_id, save_path=None, fmt="png", include_image_base64=False)` | `{success, nodes, edges, feeds, products, image_path}` |
| `dispose_result` | `(result_id)` | `{success}` |

See the [MCP tool reference](mcp-tool-reference.md) for parameter shapes and examples —
the tool params map 1:1 to these method arguments.

## Stored entry shape

Each `result_id` maps to a dict:

```python
{
  "system":   <bst.System | qs.System>,
  "tea":      <bst.TEA | None>,
  "product":  <bst.Stream | None>,     # for MSP
  "feedstock": <bst.Stream | None>,    # for feedstock_price uncertainty
  "model":    <bst.Model | None>,      # cached by run_uncertainty for run_sensitivity
  # sanitation systems also carry:
  "kind": "sanitation",
  "influent": <qs.WasteStream>, "effluent": ..., "recovered": ...,
}
```

## Design contracts

- **JSON-friendly only.** Every returned value is a primitive, list, or dict — no live
  objects — so results serialize over MCP unchanged.
- **No hidden recomputation.** Analysis methods read results off the live objects that
  `build_*`/`simulate_system` already populated. (`get_wastewater_results` reads cached
  composite variables, so it doesn't re-simulate — important because QSDsan and BioSTEAM
  share thermosteam's global thermo state.)
- **Errors are values.** Methods catch exceptions and return `{"success": False,
  "error": ...}` rather than raising, so the server always produces a valid envelope.

## Extending the engine

To add a capability: add a method to `BioSTEAMEngine` returning `ok(...)`/`err(...)`,
then wrap it in `mcp/src/tools.py` with `@read_tool` or `@mutate_tool` and an output
schema. Add a test to `mcp/test_engine.py` (engine-level) and/or `mcp/test_server.py`
(through the in-memory client). The
[optimization case study](../case_studies/optimization_uncertainty/) and
[Tier 7](../tutorials/07_uncertainty_optimization/) contain reusable patterns
(optimization, Monte Carlo) for new tools.
