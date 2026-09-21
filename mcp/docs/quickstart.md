# BioSTEAM / QSDsan MCP Quick Start

Use the MCP server to build or load process systems, simulate them, inspect streams, evaluate techno-economics, calculate foreground impact contributions from supplied factors, and run uncertainty, sensitivity, or optimization workflows.

## Requirements

- Python 3.11+
- BioSTEAM 2.51+
- QSDsan 1.4+
- biorefineries 2.34+
- chaospy 4.3+
- the validated SDAI environment or an equivalent compatible environment

The reviewed MCP package version is 0.4.1.

## 1. Install

From the MCP directory:

```bash
cd Biosteam/mcp
pip install -e .
```

The repository's validated development environment is `envShilab`; its broader learning-hub README records the resolved package versions used for current tutorials and case studies.

## 2. Start the server

From `Biosteam/mcp`:

```bash
python -m src
```

The installed console script is:

```bash
biosteam-mcp
```

For streamable HTTP:

```bash
TRANSPORT=http MCP_PORT=8000 python -m src
```

## 3. Verify the environment

Start with:

```text
health_check
```

This confirms imports and reports installed package versions. A healthy import does not validate a particular process model.

## 4. Choose a system path

Three build paths are available:

- `build_system` — load a named published `biorefineries` model such as cornstover.
- `build_system_from_spec` — build a custom BioSTEAM flowsheet from a structured specification.
- `build_sanitation_system` — build a QSDsan wastewater/resource-recovery system from a structured specification.

Each returns a `result_id` that identifies the stored model state.

## 5. Inspect before interpreting

For a built BioSTEAM system:

```text
simulate_system
→ get_stream_results
→ get_tea_results
→ optional get_lca_results
```

For QSDsan sanitation systems, use `get_wastewater_results` for influent/effluent composite variables, removal efficiencies, and nutrient recovery metrics.

## 6. Foreground impact calculation boundary

`get_lca_results` multiplies model feed/electricity quantities by characterization factors supplied by the caller. This is useful for controlled foreground impact accounting, but the MCP server does not provide a complete background LCI database or perform full database-linked LCA by itself.

For a full LCA study, document the source, unit, geography, temporal basis, and method basis of every supplied factor—or link the process inventory to an LCA engine such as openLCA or Brightway.

## 7. Uncertainty and optimization

`run_uncertainty` currently samples supported economic parameters and reports the resulting MSP distribution. Run it before `run_sensitivity`, which computes Spearman rank correlations from the most recent uncertainty run.

`optimize` changes selected unit variables using differential evolution and leaves the stored system at the optimum. Treat optimization bounds, objective choice, convergence settings, and model feasibility as explicit study inputs.

## 8. Cleanup

Call:

```text
dispose_result
```

when the stored system is no longer needed.

## Next

- [Tool Reference](tool-reference.md)
- [Validation Scope](validation.md)
- [MCP README](../README.md)
- [BioSTEAM/QSDsan learning hub](../../README.md)
