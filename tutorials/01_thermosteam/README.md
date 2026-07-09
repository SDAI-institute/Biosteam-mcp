# Tier 1 — thermosteam

The thermodynamic engine under BioSTEAM: chemicals, property packages, streams, and
phase equilibrium.

## Learning objectives
- Build `Chemical` / `Chemicals` and query properties (MW, Tb, `Psat`).
- Understand how a `Stream` draws on the active thermo package.
- Run vapor–liquid equilibrium (`.vle`), bubble/dew points, and energy-balanced mixing.

## Contents
| File | What |
|------|------|
| `01_chemicals_streams_equilibrium.py` | Runnable percent-format script |
| `01_chemicals_streams_equilibrium.ipynb` | Executed notebook with real outputs |

## Build the notebook
```powershell
python environment/build_notebook.py tutorials/01_thermosteam/01_chemicals_streams_equilibrium.py
```

**Next:** [Tier 2 — Unit operations](../02_unit_operations/).
