# Troubleshooting & version gotchas

Real issues hit while building these tutorials against the `envShilab` stack
(BioSTEAM 2.51.19, thermosteam 0.51.17, QSDsan 1.4.3, pandas 3.0.3). Each entry is a
symptom → cause → fix.

## `BinaryDistillation` raises `cannot meet specifications! stages > 100`
**Cause:** the light/heavy key pair forms an **azeotrope** (ethanol/water,
ethyl-acetate/water) or has relative volatility ≈ 1 (water/acetic acid, due to vapor-
phase association). McCabe–Thiele can't cross it.
**Fix:** choose a wide-boiling, non-azeotropic pair for teaching (e.g. water/glycerol),
or model a real separation with molecular sieves / extractive distillation. See Tier 2.

## `Flash` raises `unsupported operand type(s) for +: 'float' and 'NoneType'`
**Cause:** the feed contains a **non-volatile solid** (e.g. Glucose) with no gas-phase
enthalpy model; the flash tries to compute a vapor enthalpy for it.
**Fix:** keep solids out of the vapor path — react them away first (X=1.0) or route
them around the flash. See Tier 5.

## `get_total_feeds_impact` raises `float * NoneType`
**Cause:** the *real* `None` is `system.operating_hours` — the impact aggregators
return **annual** values and multiply by operating hours.
**Fix:** set `sys.operating_hours = 24 * operating_days` (or attach a TEA) before
calling any `get_*_impact`. See Tier 5.

## `Model.__init__() got an unexpected keyword argument 'metrics'`
**Cause:** this BioSTEAM version renamed the constructor argument to **`indicators`**.
**Fix:** `bst.Model(sys, indicators=[bst.Metric(...)])`.

## `'list' object has no attribute 'columns'` after `spearman_r()`
**Cause:** `model.spearman_r()` returns **two** DataFrames (rho, p-values).
**Fix:** `rho, pvalues = model.spearman_r()`.

## `module 'qsdsan.sanunits' has no attribute 'SanUnit'`
**Cause:** the base class lives at `qs.SanUnit`; `qsdsan.sanunits` holds concrete
models only.
**Fix:** subclass `qs.SanUnit`.

## `BinaryDistillation` has no attribute `reflux`
**Fix:** read it from `D1.design_results["Reflux"]` (and `["Actual stages"]`).

## IRR comes back absurd (e.g. 2400%)
**Cause:** capital is negligible relative to throughput in a toy system, so any margin
implies an enormous return; the solver hits its bound.
**Fix:** report **MSP** (robust) for toy systems; only trust IRR when capital intensity
is realistic (see the cornstover case study). See Tier 4.

## A gradient optimizer (`L-BFGS-B`) doesn't move off the start point
**Cause:** the metric surface is flat/noisy near the nominal design, so the numerical
gradient is ≈0.
**Fix:** use a gradient-free optimizer (`differential_evolution`, or
`minimize_scalar(..., method="bounded")` for 1-D). See the optimization case study.

## Notebook execution
Notebooks are (re)built from the percent-format `.py` via
`python environment/build_notebook.py <script.py>`. If a cell errors, the build fails
loudly (`allow_errors=False`) — fix the `.py`, rebuild. The kernel name is `envShilab`.

## Pandas 3.0 note
The stack imports and runs cleanly under pandas 3.0.3 here, but it's newer than the
stack targets. If you see obscure pandas errors, pin `pandas<3` in a fresh env.
