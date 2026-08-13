# BioSTEAM / QSDsan MCP Quick Start

Use the MCP server to build or load process systems, simulate them, inspect streams, evaluate techno-economics, calculate foreground impact contributions from supplied factors, and run uncertainty, sensitivity, or optimization workflows.

## Requirements

- Python 3.11+
- BioSTEAM 2.51+
- QSDsan 1.4+
- biorefineries 2.34+
- chaospy 4.3+
- the validated SDAI environment or an equivalent compatible environment

The reviewed MCP package version is 0.1.0.

## 1. Install

From the MCP directory:

```bash
cd Biosteam/mcp
pip install -e .
```

The repository's validated development environment is `envShilab`; its broader learning-hub README records the resolved package versions used for current tutorials and case studies.

## 2. Start the server

From `Biosteam/mcp`:

```bash
python -m src
```

The installed console script is:

```bash
biosteam-mcp
```

For streamable HTTP:

```bash
