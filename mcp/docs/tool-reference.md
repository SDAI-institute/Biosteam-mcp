# BioSTEAM / QSDsan MCP Tool Reference

Reviewed package: `biosteam-mcp-server` 0.4.1. The current FastMCP application exposes **24 tools**: one health check, 18 modeling/analysis/result tools, and 5 background-job lifecycle tools.

## Health and model discovery — 2 tools

| Tool | Purpose |
|---|---|
| `health_check` | Verify BioSTEAM, ThermoSTEAM, QSDsan, and server runtime state and report versions. |
| `list_biorefinery_models` | List published BioSTEAM biorefinery models supported by the named-model loader. |

## Build and model state — 4 tools

| Tool | Purpose |
|---|---|
| `build_system` | Load a supported published biorefinery model and store it under a `result_id`. |
| `build_system_from_spec` | Build a custom BioSTEAM flowsheet from a structured specification, including optional explicit ideal-thermo setup. |
| `build_sanitation_system` | Build a QSDsan wastewater/resource-recovery system from a structured specification. |
| `simulate_system` | Re-simulate a stored model and return an updated convergence/summary view. |

These operations create or mutate stored model state and are blocked when `BIOSTEAM_MCP_READONLY=1`.

## Process and thermodynamic inspection — 5 tools

| Tool | Purpose |
|---|---|
| `get_stream_results` | Inspect phase, temperature, pressure, mass/molar/volume flow, composition, and enthalpy for one stream. |
| `get_vle_results` | Calculate bubble/dew equilibrium for a stored stream composition at a specified pressure. |
| `get_unit_results` | Inspect unit design results, connected streams, utilities, and purchase/installed costs. |
| `get_wastewater_results` | Return QSDsan influent/effluent COD, BOD, TN, TP, removal, and recovery metrics. |
| `get_flowsheet_diagram` | Return node/edge flowsheet data and optionally render an image. |

## Economic and impact analysis — 2 tools

| Tool | Purpose |
|---|---|
| `get_tea_results` | Return FCI, FOC, VOC, NPV, and product minimum selling price when TEA is attached. |
| `get_lca_results` | Calculate annual foreground impact contributions from model flows and caller-supplied characterization factors. |

`get_lca_results` is a controlled foreground-impact calculation, not a complete background-database LCA engine. The caller is responsible for the provenance, units, geography, temporal basis, and methodological suitability of supplied characterization factors.

## Uncertainty, sensitivity, and optimization — 5 tools

| Tool | Purpose |
|---|---|
| `run_uncertainty` | Sample supported economic parameters and return an MSP distribution. |
| `run_uncertainty_async` | Start uncertainty analysis as a background job and return a `job_id`. |
| `run_sensitivity` | Compute Spearman rank correlations using the most recent uncertainty run. |
| `optimize` | Optimize selected unit variables against MSP or NPV using differential evolution. |
| `optimize_async` | Start optimization as a background job and return a `job_id`. |

When `BIOSTEAM_NATIVE_TASKS_ENABLED=true` and the client supports MCP Tasks, `run_uncertainty` and `optimize` can use native task behavior. The explicit async tools remain available for clients without MCP Tasks support.

## Background-job lifecycle — 5 tools

| Tool | Purpose |
|---|---|
| `get_job_status` | Poll a background job until `terminal=true`. |
| `get_job_result` | Retrieve the completed job result, with optional paging for large top-level lists. |
| `list_jobs` | List recent background jobs. |
| `cancel_job` | Cancel a queued job when cancellation is still safe. |
| `dispose_job` | Remove a terminal job and its stored result from the job registry. |

## Result lifecycle — 1 tool

| Tool | Purpose |
|---|---|
| `dispose_result` | Remove a stored process-system result from the process-wide engine registry and delete persisted provenance when applicable. |

## Result identity

Build calls return a `result_id`. Use that ID for subsequent simulation, inspection, TEA, impact, uncertainty, sensitivity, optimization, and flowsheet calls so the analysis stays tied to one stored system state.

BioSTEAM MCP 0.4.1 can restore reconstructible process-system handles after a compatible process/container restart when persistence is enabled. The stored record is a strict JSON build recipe and runtime fingerprint, not a serialized scientific Python object.

## Read-only mode

Set:

```text
BIOSTEAM_MCP_READONLY=1
```

to block build, re-simulation, uncertainty, optimization, job mutation, and result disposal operations. Read-only tools can still inspect an existing registered result.

## Review boundary

A converged simulation does not establish physical realism, scale-up validity, appropriate thermodynamics, suitable cost correlations, valid characterization factors, or a meaningful optimization objective. The MCP layer exposes the modeling engine; engineers remain responsible for assumptions, validation, and interpretation.
