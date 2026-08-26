# Getting started

Everything runs in the **envShilab** conda environment (Python 3.11).

## 1. Install

```powershell
conda activate envShilab
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam"
pip install -r environment/requirements.txt
python -m ipykernel install --user --name envShilab --display-name "Python (envShilab)"
python environment/verify_install.py        # prints versions; fails loud if broken
```

Resolved versions at build time: BioSTEAM 2.51.19, thermosteam 0.51.17, QSDsan 1.4.3,
biorefineries 2.34.10, fastmcp 3.4.4. See
[reference/troubleshooting.md](../reference/troubleshooting.md) for known gotchas.

## 2. Work through the tutorials

Nine tiers, beginner → expert. Each is a percent-format `.py` that runs as a plain
script *and* builds an executed notebook.

```powershell
python tutorials/00_foundations/00_first_flowsheet.py           # run as a script
python environment/build_notebook.py tutorials/00_foundations/00_first_flowsheet.py  # (re)build the notebook
```

See the [tutorials index](../tutorials/README.md) for the full ladder.

## 3. Run the case studies

Five end-to-end studies with reproducible numbers (e.g. cornstover MSP $0.6926/kg):

```powershell
python case_studies/biorefinery_cornstover_ethanol/cornstover_tea.py
```

See the [case-studies index](../case_studies/README.md).

## 4. Run the MCP server

> **Run from the `mcp/` directory.** The package is named `src` (not `mcp`) to avoid
> shadowing the `mcp` SDK, and it adds `mcp/` to `sys.path` so the sibling `engine.py`
> resolves.

```powershell
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam\mcp"
python engine.py        # smoke demo (cornstover) — no MCP client needed
python -m src           # start the MCP server over stdio
pytest -q               # 10 tests (engine + in-memory FastMCP client)
```

### Connect a client
Point any MCP client at the server with [`mcp/mcp.example.json`](../mcp/mcp.example.json):

```json
{
  "mcpServers": {
    "biosteam": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "D:/01code/Projects/SDAI- Ecosystem/Biosteam/mcp",
      "env": {"PYTHONWARNINGS": "ignore", "TRANSPORT": "stdio"}
    }
  }
}
```

### HTTP transport (optional)
```powershell
$env:TRANSPORT="http"; $env:MCP_PORT="8000"; python -m src
```

### Read-only mode
Set `BIOSTEAM_MCP_READONLY=1` to block every mutating tool (`build_*`, `simulate_*`,
`run_uncertainty`, `optimize`, `dispose_result`).

## 5. A first tool session

Once connected, a minimal flow:

1. `health_check()` → confirm versions.
2. `build_system(model_name="cornstover")` → `result_id`.
3. `get_tea_results(result_id)` → MSP, FCI, NPV.
4. `run_uncertainty(result_id, parameters=[...])` then `run_sensitivity(result_id)`.
5. `dispose_result(result_id)`.

See the [MCP tool reference](mcp-tool-reference.md) for every tool.

## 6. Use it from the LCA Copilot

The copilot skill lives at `LCA copilot/skills/biosteam/` (`SKILL.md` + `skill.json`)
and points at this server. It loads through the copilot's own `SkillRegistry` alongside
the openlca-ipc / brightway2 skills. See [architecture](architecture.md) for the LCA
foreground↔background seam.
