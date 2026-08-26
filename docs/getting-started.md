# Getting started

Everything runs in the **envShilab** conda environment (Python 3.11).

## 1. Install

```powershell
conda activate envShilab
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam"
pip install -r environment/requirements.txt
python -m ipykernel install --user --name envShilab --display-name "Python (envShilab)"
python environment/verify_install.py        # prints versions; fails loud if broken
```

Resolved versions at build time: BioSTEAM 2.51.19, thermosteam 0.51.17, QSDsan 1.4.3,
biorefineries 2.34.10, fastmcp 3.4.4. See
[reference/troubleshooting.md](../reference/troubleshooting.md) for known gotchas.

## 2. Work through the tutorials

Nine tiers, beginner â†’ expert. Each is a percent-format `.py` that runs as a plain
script *and* builds an executed notebook.

```powershell
python tutorials/00_foundations/00_first_flowsheet.py           # run as a script
python environment/build_notebook.py tutorials/00_foundations/00_first_flowsheet.py  # (re)build the notebook
```

See the [tutorials index](../tutorials/README.md) for the full ladder.

## 3. Run the case studies

Five end-to-end studies with reproducible numbers (e.g. cornstover MSP $0.6926/kg):

```powershell
python case_studies/biorefinery_cornstover_ethanol/cornstover_tea.py
```

