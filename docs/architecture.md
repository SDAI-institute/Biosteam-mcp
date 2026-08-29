# Architecture

How the pieces of the BioSTEAM/QSDsan ecosystem fit together, and why.

![Ecosystem architecture](architecture.svg)

## The stack, bottom to top

```
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚  LCA Copilot   (skills/biosteam â†’ biosteam-qsdsan MCP)       â”‚  agent layer
 â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
 â”‚  biosteam-qsdsan MCP server  (mcp/src, FastMCP, 14 tools)    â”‚  tool layer
 â”‚     â””â”€â”€ engine.py  (MCP-agnostic core, the results contract) â”‚
 â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
 â”‚  QSDsan   (SanUnit, WasteStream, dynamic processes)          â”‚  domain frameworks
 â”‚  biorefineries  (published BioSTEAM models)                  â”‚
 â”‚  BioSTEAM   (Unit, System, TEA, LCA)                         â”‚
 â”‚  thermosteam   (Chemical, Stream, equilibrium)               â”‚  thermo engine
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

Each layer only depends on the ones below it. thermosteam is the thermodynamic engine;
BioSTEAM adds process units, systems, TEA, and LCA; QSDsan specializes BioSTEAM for
sanitation. The MCP server exposes all of it as tools; the LCA Copilot consumes those
tools through a skill.

## Repository map

```
Biosteam/
â”œâ”€â”€ tutorials/        9 tiers, beginnerâ†’expert (concept .md + runnable .py + executed .ipynb)
â”œâ”€â”€ case_studies/     5 end-to-end studies with reproducible headline numbers
â”œâ”€â”€ reference/        cheat-sheet, glossary, troubleshooting (version gotchas)
â”œâ”€â”€ environment/      env setup, requirements, verify + notebook-build tooling
