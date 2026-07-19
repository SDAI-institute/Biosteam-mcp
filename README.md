# BioSTEAM + QSDsan Ecosystem

A self-contained, hands-on curriculum and tooling asset for the **BioSTEAM /
thermosteam / QSDsan** stack — from first principles to expert-level system design,
techno-economic analysis (TEA), life-cycle assessment (LCA), uncertainty, and
optimization — plus an **MCP server** so an agent (e.g. the LCA Copilot) can drive
these frameworks programmatically.

## What's here

| Path | What it is |
|------|-----------|
| [`docs/`](docs/) | **Consolidated documentation** — start at [`docs/index.md`](docs/index.md) |
| [`environment/`](environment/) | Env setup, pinned deps, and `verify_install.py` |
| [`tutorials/`](tutorials/) | 9 tiers, beginner → expert (concept `.md` + executed `.ipynb` + runnable `.py`) |
| [`case_studies/`](case_studies/) | 5 end-to-end studies with real, reproducible headline numbers |
| [`reference/`](reference/) | Cheat-sheets, API map, glossary, troubleshooting |
| [`mcp/`](mcp/) | MCP server — 14 tools (BioSTEAM + QSDsan), 10 tests passing |
| [`CHECKLIST.md`](CHECKLIST.md) | Master progress tracker |

**New here?** Read [`docs/getting-started.md`](docs/getting-started.md). Building against
the MCP? See the [tool reference](docs/mcp-tool-reference.md).

## The frameworks in one paragraph

**thermosteam** is the thermodynamic engine: `Chemical`s, property packages, and
material/energy `Stream`s. **BioSTEAM** builds on it with process `Unit`s, `System`s
(with recycle convergence), `TEA`, and LCA. **QSDsan** builds on BioSTEAM for
sanitation and resource-recovery systems (`SanUnit`, `WasteStream`, dynamic
processes) with first-class uncertainty/sensitivity via `Model`s. The
**biorefineries** package ships canonical, published BioSTEAM models (cornstover
ethanol, lipidcane biodiesel, …) used throughout the case studies.

## Learning path

Work top-to-bottom through `tutorials/`; each tier's `README.md` states its
objectives and "you can now…" outcomes. Tiers 0–3 build the modeling core, 4–5 add
economics and impacts, 6 brings in QSDsan, 7 covers uncertainty & optimization, and
8 is expert integration (and defines the surface the MCP exposes). Then the
`case_studies/` apply everything end-to-end.

## Quick start

```powershell
conda activate envShilab
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam"
pip install -r environment/requirements.txt
python -m ipykernel install --user --name envShilab --display-name "Python (envShilab)"
python environment/verify_install.py
```

See [`environment/setup.md`](environment/setup.md) for details and the isolated-env
fallback.

## Resolved environment

Target: **envShilab**, Python 3.11.9. Resolved and smoke-tested at build time:

| Package | Version |
|---------|---------|
| BioSTEAM | 2.51.19 |
| thermosteam | 0.51.17 |
| QSDsan | 1.4.3 |
| biorefineries | 2.34.10 |
| chaospy | 4.3.15 |
| NumPy | 1.26.4 |
| pandas | 3.0.3 |

Re-run `python environment/verify_install.py` to confirm on your machine. All 9 tutorial
tiers, 5 case studies, and the MCP engine tests execute cleanly on this set. (pandas 3.0
is newer than the stack targets but runs fine here — see
[reference/troubleshooting.md](reference/troubleshooting.md).)

## Status

See [`CHECKLIST.md`](CHECKLIST.md) for live progress across all phases.
