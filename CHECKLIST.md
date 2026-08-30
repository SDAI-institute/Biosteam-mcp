# BioSTEAM + QSDsan Ecosystem â€” Master Checklist

> Legend: `[ ]` todo Â· `[~]` in progress / partial Â· `[x]` done
> This file is the source-of-truth progress tracker. Flip boxes as tiers land.

## Phase 0 â€” Scaffold & environment
- [x] Create the folder tree under `Biosteam/`
- [x] `environment/requirements.txt`
- [x] `environment/setup.md`
- [x] `environment/verify_install.py`
- [x] Install stack into **envShilab** (biosteam 2.51.19, qsdsan 1.4.3, thermosteam 0.51.17)
- [x] Register Jupyter kernel `Python (envShilab)`
- [x] `verify_install.py` runs clean; runtime smoke test passed (cornstover MSP $0.693/kg)
- [x] `environment/build_notebook.py` engine (percent-.py â†’ executed .ipynb)
- [x] Top-level `README.md`
- [x] `CHECKLIST.md` (this file)

## Phase 1 â€” Tutorials (author + execute each tier)
Each tier = `README.md` (concepts) + `NN_*.ipynb` (executed) + `NN_*.py` (script).

- [x] Tier 0 â€” `00_foundations` â€” object model, first end-to-end flowsheet
- [x] Tier 1 â€” `01_thermosteam` â€” chemicals, thermo, streams, equilibrium
