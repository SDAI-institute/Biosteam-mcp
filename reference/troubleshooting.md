# Troubleshooting & version gotchas

Real issues hit while building these tutorials against the `envShilab` stack
(BioSTEAM 2.51.19, thermosteam 0.51.17, QSDsan 1.4.3, pandas 3.0.3). Each entry is a
symptom â†’ cause â†’ fix.

## `BinaryDistillation` raises `cannot meet specifications! stages > 100`
**Cause:** the light/heavy key pair forms an **azeotrope** (ethanol/water,
ethyl-acetate/water) or has relative volatility â‰ˆ 1 (water/acetic acid, due to vapor-
phase association). McCabeâ€“Thiele can't cross it.
**Fix:** choose a wide-boiling, non-azeotropic pair for teaching (e.g. water/glycerol),
or model a real separation with molecular sieves / extractive distillation. See Tier 2.

## `Flash` raises `unsupported operand type(s) for +: 'float' and 'NoneType'`
**Cause:** the feed contains a **non-volatile solid** (e.g. Glucose) with no gas-phase
enthalpy model; the flash tries to compute a vapor enthalpy for it.
**Fix:** keep solids out of the vapor path â€” react them away first (X=1.0) or route
them around the flash. See Tier 5.

## `get_total_feeds_impact` raises `float * NoneType`
**Cause:** the *real* `None` is `system.operating_hours` â€” the impact aggregators
return **annual** values and multiply by operating hours.
**Fix:** set `sys.operating_hours = 24 * operating_days` (or attach a TEA) before
calling any `get_*_impact`. See Tier 5.
