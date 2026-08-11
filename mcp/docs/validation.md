# BioSTEAM / QSDsan MCP Validation Scope

This page summarizes the current repository reliability evidence without presenting BioSTEAM as a full LCA engine or generalizing fixture results beyond their tested scope. The detailed record remains in [`RELIABILITY.md`](../RELIABILITY.md).

## Validation framing

BioSTEAM is primarily a process-simulation and techno-economic-analysis framework. The MCP reliability pass therefore asks whether the MCP/engine layer faithfully exposes process/TEA results and whether its narrower foreground-impact arithmetic is correct for controlled hand calculations.

It is not evaluated as a substitute for openLCA or Brightway background-database LCA.

## Reviewed environment

The repository reliability note records the validated `envShilab` environment with Python 3.11.9 and the pinned BioSTEAM/QSDsan ecosystem. The post-hardening suite records **15 passing tests**: the original engine/server tests plus reference-model fidelity, foreground-impact hand calculation, and uncertainty/sensitivity sanity checks.

## Reference-model fidelity

The reliability pass compares the MCP engine path against an independent direct BioSTEAM API process for the published cornstover biorefinery in separate Python subprocesses.

The recorded FCI, FOC, VOC, NPV, and MSP values match between the MCP engine path and direct BioSTEAM API for that reference model. This supports fidelity of the tested wrapper path; it is not an external validation of the cornstover model itself.

## Foreground impact hand calculation

The validation builds a minimal custom model with known flows and supplied characterization factors. The recorded checks include:

- feed contribution: `100 kg/h × 7,920 h × 2.5 = 1,980,000`, matched exactly;
- electricity contribution: approximately `0.3208 kW × 7,920 h × 0.5 = 1,270.4`, matched by the engine.

These tests validate the arithmetic path used by `get_lca_results` for the fixtures. They do not create or validate a background life-cycle inventory.

## Uncertainty and sensitivity sanity

The cornstover test records correctly ordered MSP percentiles around the deterministic value and physically interpretable Spearman directions for selected economic drivers. This is an internal-consistency/sanity check, not an external benchmark for the Monte Carlo distribution.

## What this evidence supports

Within the documented environment and fixtures, the tests support statements that:

- the tested MCP wrapper reproduced direct BioSTEAM TEA outputs for the reference model;
- the tested foreground factor arithmetic matched independent hand calculations;
- the tested uncertainty/sensitivity workflow behaved coherently for the selected parameters.

## What it does not support

The validation does **not** establish:

- physical or scale-up validity of arbitrary BioSTEAM/QSDsan models;
- accuracy of cost correlations for a particular project;
- validity or completeness of caller-supplied characterization factors;
- equivalence to a full background-database LCA engine;
- correctness of every optimization problem or uncertainty distribution;
- hosted reliability, security, or customer outcomes.

## Reproduction

The repository records:

```bash
cd Biosteam/mcp
/c/MSI/anaconda3/envs/envShilab/python.exe -m pytest -q
```

Preserve the environment package versions and source revision with any reproduced validation record.