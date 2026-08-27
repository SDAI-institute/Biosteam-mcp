# Engine API (`mcp/engine.py`)

`engine.py` is the MCP-agnostic core. Import and use it directly (no MCP client needed) â€”
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
