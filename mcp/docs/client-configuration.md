# BioSTEAM / QSDsan MCP Client Configuration

Use stdio for local developer clients. Use streamable HTTP only when a remote/client integration requires it.

## Local stdio

Install from the MCP directory in the intended BioSTEAM/QSDsan environment:

```bash
cd Biosteam/mcp
pip install -e .
```

The `cwd` must remain the `mcp/` directory so the `src` package and sibling `engine.py` resolve consistently.

Example client configuration:

```json
{
  "mcpServers": {
    "biosteam": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "/absolute/path/to/Biosteam/mcp",
      "env": {
        "TRANSPORT": "stdio",
        "BIOSTEAM_MCP_READONLY": "true"
      }
    }
  }
}
```

## Local HTTP

Start the server with:

```bash
TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8000 python -m src
```

Keep the local HTTP service private unless an authenticated gateway or secure tunnel is intentionally configured.

## First client calls

```text
health_check
→ list_biorefinery_models
```

Then select one of the three model paths:

```text
build_system
build_system_from_spec
build_sanitation_system
```

Do not interpret TEA, foreground impact, uncertainty, or optimization results until the selected process system and assumptions have been reviewed.

## Read-only mode

Set:

```text
BIOSTEAM_MCP_READONLY=true
```

when the client should inspect existing state without building, re-simulating, optimizing, running uncertainty mutations, or disposing stored state.

## Remote clients

For any remote, web-hosted, or sandboxed MCP client, route only the MCP HTTP endpoint through an authenticated HTTPS gateway, VPN, or secure tunnel appropriate to that client. Do not publish the raw container/runtime port.

After changing tools or schemas, rebuild the runtime, rescan client tools, and verify `health_check` before a study.