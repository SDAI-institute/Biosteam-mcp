# Tier 0 — Foundations

**Start here.** This tier introduces the five objects the entire BioSTEAM/QSDsan
stack is built from and walks a complete build → simulate → inspect loop.

## Learning objectives
- Name the object model — `Chemical` → `Stream` → `Unit` → `System` → `TEA` — and
  which package owns each.
- Set a thermodynamic property package and create material streams.
- Instantiate a unit, wire units into a system, and `simulate()`.
- Read results back off the objects (no separate results file).

## Contents
| File | What |
|------|------|
| `00_first_flowsheet.py` | Runnable percent-format script (`python 00_first_flowsheet.py`) |
| `00_first_flowsheet.ipynb` | Same content, **executed** with real outputs |

## Build the notebook yourself
```powershell
python environment/build_notebook.py tutorials/00_foundations/00_first_flowsheet.py
```

## You can now…
Set thermo, build streams and a `Flash` unit, assemble and simulate a `System`, and
extract results programmatically — the loop every later tier repeats.

**Next:** [Tier 1 — thermosteam](../01_thermosteam/) goes one layer down into
chemicals, property packages, multiphase streams, and phase equilibrium.
