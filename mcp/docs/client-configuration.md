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
