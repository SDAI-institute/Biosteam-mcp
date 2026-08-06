# BioSTEAM / QSDsan MCP

An MCP server that exposes BioSTEAM/QSDsan process design, TEA, LCA, and uncertainty
analysis as tools â€” for eventual integration into the **LCA Copilot**.

## Status
| Piece | State |
|-------|-------|
| [`SPEC.md`](SPEC.md) â€” tools, schemas, transport, integration plan | âœ… done |
| [`engine.py`](engine.py) â€” framework-facing core (MCP-agnostic) | âœ… done + tested |
| [`src/`](src/) â€” FastMCP server (24 tools) wrapping the engine | âœ… done + tested |
| `test_engine.py` + `test_server.py` â€” engine + FastMCP regression coverage | âœ… done |
| LCA-Copilot `skills/biosteam/` wiring | âœ… done |

## Run it
```powershell
conda activate envShilab
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam\mcp"   # cwd MUST be mcp/ (see note below)
python engine.py        # smoke demo against the cornstover biorefinery
python -m src           # start the MCP server over stdio
pytest -q               # engine + server in-memory regression suite
```

Point an MCP client at it with [`mcp.example.json`](mcp.example.json). The 24 tools:

**Build:** `build_system` (named biorefinery), `build_system_from_spec` (custom
BioSTEAM flowsheet), `build_sanitation_system` (QSDsan wastewater/recovery).
`build_system_from_spec` accepts `thermo_model: "ideal"` for explicit Raoult-law
validation using `IdealActivityCoefficients`, `IdealFugacityCoefficients`, and
`MockPoyintingCorrectionFactors`; the build response records the installed thermo
metadata for provenance. Omit it (or use `"default"`) for ThermoSTEAM defaults.
**Analyze:** `simulate_system`, `get_stream_results`, `get_vle_results`, `get_unit_results`, `get_tea_results`, `get_lca_results`,
`get_wastewater_results`, `run_uncertainty`, `run_sensitivity`, `optimize`,
`get_flowsheet_diagram`. Modern MCP 2026-07-28 clients can opt into native Tasks for
`run_uncertainty` and `optimize` when `BIOSTEAM_NATIVE_TASKS_ENABLED=true`; legacy clients
can use `run_uncertainty_async` / `optimize_async` plus the job status/result tools.
