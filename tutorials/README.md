# Tutorials — beginner → expert

Nine tiers. Each ships a concept `README.md`, a runnable percent-format `.py`, and an
**executed** `.ipynb` (real outputs). Work top to bottom.

| Tier | Folder | You'll learn |
|------|--------|--------------|
| 0 | [00_foundations](00_foundations/) | The object model; build → simulate → inspect a first flowsheet |
| 1 | [01_thermosteam](01_thermosteam/) | Chemicals, property packages, streams, VLE, energy balances |
| 2 | [02_unit_operations](02_unit_operations/) | Built-in units, design/cost, a custom `Unit`, azeotropes |
| 3 | [03_systems_flowsheets](03_systems_flowsheets/) | Systems, recycle convergence, specifications |
| 4 | [04_tea](04_tea/) | `TEA` subclass, CAPEX/OPEX, NPV, minimum selling price |
| 5 | [05_lca](05_lca/) | Characterization factors, impact aggregation, allocation |
| 6 | [06_qsdsan](06_qsdsan/) | `WasteStream`, composite variables, `SanUnit`, resource recovery |
| 7 | [07_uncertainty_optimization](07_uncertainty_optimization/) | `Model`, Monte Carlo, Spearman sensitivity, optimization |
| 8 | [08_expert_integration](08_expert_integration/) | Framework-agnostic results contract; the MCP-facing API |

## Running

```powershell
conda activate envShilab
# run a tier as a plain script:
python tutorials/00_foundations/00_first_flowsheet.py
# or (re)build its executed notebook:
python environment/build_notebook.py tutorials/00_foundations/00_first_flowsheet.py
```

Every `.py` is a percent-format script (`# %%` cells) that runs top-to-bottom *and*
converts to a notebook via [`environment/build_notebook.py`](../environment/build_notebook.py).

## Then
Apply it all in the [case studies](../case_studies/), and see the tooling direction in
[`mcp/SPEC.md`](../mcp/SPEC.md).
