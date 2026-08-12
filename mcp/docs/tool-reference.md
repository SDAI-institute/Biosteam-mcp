# BioSTEAM / QSDsan MCP Tool Reference

Reviewed package: `biosteam-mcp-server` 0.1.0. The current FastMCP server registers **15 tools**: one health probe plus 14 modeling, analysis, and result-lifecycle tools.

## Health and model discovery â€” 2 tools

| Tool | Purpose |
|---|---|
| `health_check` | Verify BioSTEAM/thermosteam/QSDsan imports and report versions. |
| `list_biorefinery_models` | List published BioSTEAM biorefinery models supported by the named-model loader. |

## Build / model-state tools â€” 3 tools

| Tool | Purpose |
|---|---|
| `build_system` | Load a supported published biorefinery model and store it under a `result_id`. |
| `build_system_from_spec` | Build a custom BioSTEAM flowsheet from a structured system specification. |
| `build_sanitation_system` | Build a QSDsan wastewater/resource-recovery system from a structured specification. |

These tools create in-memory model state and are blocked in `BIOSTEAM_MCP_READONLY` mode.

## Simulation and inspection â€” 4 tools

| Tool | Purpose |
|---|---|
| `simulate_system` | Re-simulate a stored model and return a convergence/summary view. |
| `get_stream_results` | Inspect phase, temperature, pressure, mass/molar/volume flow, composition, and enthalpy for one stream. |
| `get_wastewater_results` | Return QSDsan influent/effluent COD/BOD/TN/TP, removal, and recovery metrics. |
| `get_flowsheet_diagram` | Return node/edge flowsheet data and optionally render an image. |
