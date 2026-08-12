# BioSTEAM / QSDsan MCP Tool Reference

Reviewed package: `biosteam-mcp-server` 0.1.0. The current FastMCP server registers **15 tools**: one health probe plus 14 modeling, analysis, and result-lifecycle tools.

## Health and model discovery — 2 tools

| Tool | Purpose |
|---|---|
| `health_check` | Verify BioSTEAM/thermosteam/QSDsan imports and report versions. |
| `list_biorefinery_models` | List published BioSTEAM biorefinery models supported by the named-model loader. |

## Build / model-state tools — 3 tools

| Tool | Purpose |
|---|---|
| `build_system` | Load a supported published biorefinery model and store it under a `result_id`. |
| `build_system_from_spec` | Build a custom BioSTEAM flowsheet from a structured system specification. |
| `build_sanitation_system` | Build a QSDsan wastewater/resource-recovery system from a structured specification. |

These tools create in-memory model state and are blocked in `BIOSTEAM_MCP_READONLY` mode.

## Simulation and inspection — 4 tools

| Tool | Purpose |
|---|---|
| `simulate_system` | Re-simulate a stored model and return a convergence/summary view. |
| `get_stream_results` | Inspect phase, temperature, pressure, mass/molar/volume flow, composition, and enthalpy for one stream. |
| `get_wastewater_results` | Return QSDsan influent/effluent COD/BOD/TN/TP, removal, and recovery metrics. |
| `get_flowsheet_diagram` | Return node/edge flowsheet data and optionally render an image. |

## Economic and impact analysis — 2 tools

| Tool | Purpose |
|---|---|
| `get_tea_results` | Return FCI, FOC, VOC, NPV, and product minimum selling price where TEA is attached. |
| `get_lca_results` | Calculate annual foreground impact contributions from model flows and caller-supplied characterization factors. |

`get_lca_results` is not a complete background-database LCA engine. The caller owns the provenance and methodological validity of supplied characterization factors.

## Uncertainty, sensitivity, and optimization — 3 tools

| Tool | Purpose |
|---|---|
| `run_uncertainty` | Sample supported economic parameters and return an MSP distribution. |
| `run_sensitivity` | Compute Spearman rank correlations using the most recent uncertainty run. |
| `optimize` | Optimize selected unit variables against MSP or NPV using differential evolution. |

`run_uncertainty` and `optimize` alter stored server/model state and are blocked in read-only mode.

## Lifecycle — 1 tool

| Tool | Purpose |
|---|---|
| `dispose_result` | Remove a stored system/result from the process-wide engine registry. |

## Result identity

Build calls return a `result_id`. All subsequent inspection/analysis calls should use that ID so the study remains tied to one stored system state. Re-simulation, uncertainty, or optimization can change state; record the sequence of operations when results are decision-relevant.

## Read-only mode

Set:

```text
BIOSTEAM_MCP_READONLY=1
```

to block tools that build, re-simulate, sample uncertainty, optimize, or dispose stored state. Read-only tools still inspect existing registered results.

## Review boundary

A converged process simulation does not prove scale-up validity, correct thermodynamics, appropriate cost correlations, valid characterization factors, or a good optimization objective. The MCP layer exposes the modeling engine; engineers remain responsible for model selection, assumptions, validation, and interpretation.