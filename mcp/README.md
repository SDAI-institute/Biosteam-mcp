# BioSTEAM / QSDsan MCP

An MCP server that exposes BioSTEAM/QSDsan process design, TEA, LCA, and uncertainty
analysis as tools — for eventual integration into the **LCA Copilot**.

## Status
| Piece | State |
|-------|-------|
| [`SPEC.md`](SPEC.md) — tools, schemas, transport, integration plan | ✅ done |
| [`engine.py`](engine.py) — framework-facing core (MCP-agnostic) | ✅ done + tested |
| [`src/`](src/) — FastMCP server (24 tools) wrapping the engine | ✅ done + tested |
| `test_engine.py` + `test_server.py` — engine + FastMCP regression coverage | ✅ done |
| LCA-Copilot `skills/biosteam/` wiring | ✅ done |

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

BioSTEAM 0.4.1 can also recover reconstructible process-system `result_id` handles after an
MCP process/container restart. The build recipe is stored as strict JSON in Redis; no
scientific Python object is serialized. Recovery is allowed only when the installed
BioSTEAM/ThermoSTEAM/QSDsan runtime fingerprint matches the recipe. The engine restores
recorded operating hours and optimized unit attributes before exposing the original handle.
`dispose_result` deletes both live state and persisted provenance.
**Meta:** `health_check`, `list_biorefinery_models`, `get_job_status`, `get_job_result`,
`list_jobs`, `cancel_job`, `dispose_job`, `dispose_result`.

> **Why cwd must be `mcp/`:** the package is named `src` (not `mcp`) so it never
> shadows the `mcp` SDK on import, and `src/app.py` adds `mcp/` to `sys.path` so the
> sibling `engine.py` resolves. Launch from this directory (or via the console script
> `biosteam-mcp` after `pip install -e .`).

## Why an engine + a server split
`engine.py` holds all process-modeling logic and returns plain `{success, ...}` dicts —
the exact contract from tutorial [Tier 8](../tutorials/08_expert_integration/). The
FastMCP server (next phase) is a thin adapter that stores results under `result_id`s and
decorates these functions as tools, mirroring the existing
[`openlca_mcp`](../../openlca_mcp/) server. This keeps the modeling logic testable
without a live MCP client and de-risks the server build.

## Layout
```
mcp/
├── SPEC.md              # tool/schema/transport spec
├── engine.py            # framework-facing core (MCP-agnostic)
├── test_engine.py       # engine tests
├── test_server.py       # in-memory FastMCP client tests
├── pyproject.toml       # installable; console script `biosteam-mcp`
├── mcp.example.json     # MCP client config
└── src/                 # FastMCP server package
    ├── app.py           # FastMCP object, tool decorators, offload, transport
    ├── tools.py         # @read_tool / @mutate_tool wrappers over engine
    ├── schemas.py       # output-envelope helper
    ├── __init__.py
    └── __main__.py      # `python -m src`
```

## Documentation

- [Quick start](docs/quickstart.md)
- [Client configuration](docs/client-configuration.md)
- [Tool reference](docs/tool-reference.md)
- [Validation scope](docs/validation.md)
- [Reliability record](RELIABILITY.md)
- [MCP specification](SPEC.md)

## Possible next steps
- Register the skill's MCP server in the running LCA-Copilot config so the agent can
  call these tools live.
- QSDsan **dynamic** simulation (ASM/ADM process models) over MCP.
- Uncertainty/sensitivity for sanitation metrics (currently MSP-only).
