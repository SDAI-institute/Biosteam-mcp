# Environment setup

The tutorials run on **Python 3.11** in the existing **`envShilab`** conda env.

## 1. Activate the env

```powershell
conda activate envShilab
python --version   # expect Python 3.11.x
```

## 2. Install the stack

```powershell
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam"
pip install -r environment/requirements.txt
```

This pulls a large tree — `biosteam` brings `thermosteam` + `chemicals`, and `qsdsan`
builds on `biosteam`. Expect a few minutes on first install.

> **If a dependency conflict breaks envShilab**, create an isolated env instead:
> ```powershell
> conda create -n envBioSTEAM python=3.11 -y
> conda activate envBioSTEAM
> pip install -r environment/requirements.txt
> ```

## 3. Register the Jupyter kernel

So the notebooks in `tutorials/` and `case_studies/` run against this env:

```powershell
python -m ipykernel install --user --name envShilab --display-name "Python (envShilab)"
```

## 4. Verify

```powershell
python environment/verify_install.py
```

You should see version numbers for BioSTEAM, thermosteam, QSDsan and no
`MISSING (REQUIRED)` lines. The resolved versions are recorded in the top-level
[`README.md`](../README.md).

## Executing notebooks headlessly

Each tier's notebook is meant to be run end-to-end so its committed outputs are real:

```powershell
jupyter nbconvert --to notebook --execute --inplace tutorials/00_foundations/00_first_flowsheet.ipynb
```
