# Tier 8 — Expert integration & the MCP-facing API

The capstone: one framework-agnostic results contract for BioSTEAM *and* QSDsan, and
the design of the surface the MCP server will expose.

## Learning objectives
- Write a single `summarize_system` contract that works across frameworks and model
  sizes (toy flowsheet → published biorefinery).
- Drive it from the `biorefineries` cornstover model and read real results
  (68 units, ~$210 MM installed, MSP ≈ $0.69/kg).
- Understand why `qsdsan.System`/`TEA`/`Model` subclass BioSTEAM's — so tooling is
  framework-agnostic by construction.
- See the MCP tool output as just this dict serialized.

## Contents
| File | What |
|------|------|
| `08_integration_and_api.py` | Runnable percent-format script |
| `08_integration_and_api.ipynb` | Executed notebook with real outputs |

## Leads into
- The [case studies](../../case_studies/) — everything applied end-to-end.
- [`mcp/SPEC.md`](../../mcp/SPEC.md) — the contract turned into tool schemas.
