# Documentation

Consolidated documentation for the BioSTEAM/QSDsan ecosystem — a beginner→expert
curriculum plus an MCP server that exposes the frameworks as agent tools.

## Start here
- **[Getting started](getting-started.md)** — install, run tutorials/case studies, run the MCP server, connect a client.
- **[Architecture](architecture.md)** — how the layers fit (thermosteam → BioSTEAM/QSDsan → MCP → LCA Copilot), the results contract, and the LCA foreground↔background seam.

## Reference
- **[MCP tool reference](mcp-tool-reference.md)** — all 14 server tools with params, returns, and examples.
- **[Engine API](engine-api.md)** — the MCP-agnostic `engine.py` core you can call directly.
- **[Cheat-sheet](../reference/cheatsheet.md)** · **[Glossary](../reference/glossary.md)** · **[Troubleshooting](../reference/troubleshooting.md)** — quick lookups and version gotchas.

## Learn
- **[Tutorials](../tutorials/README.md)** — 9 tiers, each concept `.md` + runnable `.py` + executed `.ipynb`.
- **[Case studies](../case_studies/README.md)** — 5 end-to-end studies with reproducible numbers.

## Build / operate
- **[MCP server](../mcp/README.md)** — server layout, run instructions, tests.
- **[MCP spec](../mcp/SPEC.md)** — the design spec (schemas, transport, integration plan).
- **[CHECKLIST](../CHECKLIST.md)** — live progress across all phases.

## At a glance

| Area | State |
|------|-------|
| Tutorials (9 tiers) | ✅ all executed with real outputs |
| Case studies (5) | ✅ all executed, reproducible headline numbers |
| Reference docs | ✅ cheat-sheet, glossary, troubleshooting |
| MCP server | ✅ 14 tools, 10 tests passing (BioSTEAM + QSDsan) |
| LCA Copilot skill | ✅ wired at `LCA copilot/skills/biosteam/`, loader-verified |

The frameworks: **thermosteam** (thermo engine) → **BioSTEAM** (units, systems, TEA,
LCA) → **QSDsan** (sanitation & resource recovery) → **biorefineries** (published
models). See [architecture](architecture.md) for the full picture.
