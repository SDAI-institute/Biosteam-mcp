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

- feed contribution: `100 kg/h Ã— 7,920 h Ã— 2.5 = 1,980,000`, matched exactly;
