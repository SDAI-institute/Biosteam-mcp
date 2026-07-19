# BioSTEAM + QSDsan Ecosystem

A self-contained, hands-on curriculum and tooling asset for the **BioSTEAM /
thermosteam / QSDsan** stack â€” from first principles to expert-level system design,
techno-economic analysis (TEA), life-cycle assessment (LCA), uncertainty, and
optimization â€” plus an **MCP server** so an agent (e.g. the LCA Copilot) can drive
these frameworks programmatically.

## What's here

| Path | What it is |
|------|-----------|
| [`docs/`](docs/) | **Consolidated documentation** â€” start at [`docs/index.md`](docs/index.md) |
| [`environment/`](environment/) | Env setup, pinned deps, and `verify_install.py` |
| [`tutorials/`](tutorials/) | 9 tiers, beginner â†’ expert (concept `.md` + executed `.ipynb` + runnable `.py`) |
| [`case_studies/`](case_studies/) | 5 end-to-end studies with real, reproducible headline numbers |
| [`reference/`](reference/) | Cheat-sheets, API map, glossary, troubleshooting |
| [`mcp/`](mcp/) | MCP server â€” 14 tools (BioSTEAM + QSDsan), 10 tests passing |
| [`CHECKLIST.md`](CHECKLIST.md) | Master progress tracker |

**New here?** Read [`docs/getting-started.md`](docs/getting-started.md). Building against
the MCP? See the [tool reference](docs/mcp-tool-reference.md).

## The frameworks in one paragraph

**thermosteam** is the thermodynamic engine: `Chemical`s, property packages, and
material/energy `Stream`s. **BioSTEAM** builds on it with process `Unit`s, `System`s
(with recycle convergence), `TEA`, and LCA. **QSDsan** builds on BioSTEAM for
sanitation and resource-recovery systems (`SanUnit`, `WasteStream`, dynamic
processes) with first-class uncertainty/sensitivity via `Model`s. The
