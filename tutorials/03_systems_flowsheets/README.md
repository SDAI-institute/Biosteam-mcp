# Tier 3 — Systems & flowsheets

Wire units into a `System`, solve recycle loops to convergence, and encode operating
policy with specifications.

## Learning objectives
- Build a recycle loop and let `System.from_units` detect it.
- Simulate to convergence and read steady-state recycle flows.
- Distinguish single-pass vs overall conversion (a system-level insight).
- Attach a process `specification`.

## Contents
| File | What |
|------|------|
| `03_systems_recycle_convergence.py` | Runnable percent-format script |
| `03_systems_recycle_convergence.ipynb` | Executed notebook with real outputs |

## Build the notebook
```powershell
python environment/build_notebook.py tutorials/03_systems_flowsheets/03_systems_recycle_convergence.py
```

> **Diagrams:** `sys.diagram()` renders the flowsheet but needs the Graphviz `dot`
> executable on PATH. It's omitted from the executed notebook so it runs anywhere.

**Next:** [Tier 4 — TEA](../04_tea/).
