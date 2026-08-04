# BioSTEAM / QSDsan MCP Server â€” Specification

> Status: **fully implemented and tested.** Spec + engine + FastMCP server (`src/`, 17
> tools) + LCA-Copilot skill are all in place; engine and FastMCP regression tests cover the live surface. Beyond the original spec
> below, the built surface adds custom-flowsheet and QSDsan sanitation tools:
> `build_system_from_spec`, `build_sanitation_system`, `get_wastewater_results`,
> `optimize`, `get_stream_results`, `get_unit_results`, `get_flowsheet_diagram` (with optional inline base64). See `src/tools.py`
> for the live surface.

## Purpose

Expose BioSTEAM / QSDsan process modeling, TEA, LCA, and uncertainty analysis as MCP
tools so an agent â€” ultimately the **LCA Copilot** â€” can design, simulate, and evaluate
bioprocess systems programmatically, and reconcile results with the existing openLCA /
Brightway LCA stack.

## Design principles (carried from `openlca_mcp`)

Mirror the mature `openlca_mcp` FastMCP server already in this ecosystem:

- **FastMCP**, `src/` layout, `pyproject.toml` console script (`biosteam-mcp`).
- **Strict `output_schema`** with a shared envelope `{ "success": bool, ... }` and
  `additionalProperties: true`, so responses validate in strict clients.
- **Stateless-friendly result handles**: long-lived objects (a built system, a Monte
  Carlo table) are stored server-side under a `result_id`; tools return the id plus a
  summary; `dispose_result` frees it. (Same lifecycle as `openlca_mcp`'s result store.)
- **Blocking calls offloaded** with `anyio.to_thread` â€” simulations can take seconds.
- **Read-only vs mutating** tools flagged via `ToolAnnotations`; honor a server
  read-only mode.
- Optional **auth / telemetry** modules reused from the openLCA server pattern.

## Architecture

```
mcp/
â”œâ”€â”€ SPEC.md              # this file
â”œâ”€â”€ engine.py           # framework-facing core (pure python; NO mcp deps) â€” implemented
â”œâ”€â”€ test_engine.py      # tests for the engine â€” implemented
â””â”€â”€ src/                # FastMCP server wrapping engine.py â€” LATER PHASE
    â”œâ”€â”€ app.py          # FastMCP object, auth, telemetry, transport, probe tools
    â”œâ”€â”€ tools.py        # @mcp.tool wrappers over engine.py
    â”œâ”€â”€ schemas.py      # shared output envelope helpers
    â”œâ”€â”€ result_store.py # result_id -> live object registry
    â””â”€â”€ __main__.py
```

`engine.py` is deliberately MCP-agnostic: it is the same `summarize_system` contract
from Tier 8, generalized. The FastMCP layer is a thin adapter, which keeps the process-
modeling logic testable without a running MCP client.

