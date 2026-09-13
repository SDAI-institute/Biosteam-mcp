# Results — Cornstover → ethanol biorefinery

Reproduced from the published BioSTEAM `biorefineries.cornstover` model
(dilute-acid pretreatment + enzymatic hydrolysis + co-fermentation, NREL design).
Run `cornstover_tea.py` or the executed notebook to regenerate.

## Headline numbers
| Metric | Value |
|--------|-------|
| Units in system | 68 |
| Ethanol output | ≈185 kt/yr (21,978 kg/hr) |
| **Minimum selling price (MSP)** | **$0.6926 / kg ethanol** |
| IRR at MSP | 10.0% (target return, by calibration) |
| Installed equipment cost | $210.0 MM |
| Fixed capital investment (FCI) | $359.8 MM |
| Fixed operating cost (FOC) | $9.8 MM/yr |
| Variable operating cost (VOC) | $72.6 MM/yr |

## Feedstock-price sensitivity
Corn stover price is the dominant lever. Baseline ≈ $51.6/tonne.

| Cornstover $/t | MSP $/kg |
|----------------|----------|
| 31.0 | 0.5941 |
| 41.3 | 0.6434 |
| 51.6 | 0.6927 |
| 61.9 | 0.7420 |
| 72.2 | 0.7912 |

≈ $0.0048/kg MSP per $10/tonne of feedstock — nearly linear.

## Notes
- MSP is the robust headline metric; IRR equals the 10% target because the model's
  ethanol price is calibrated to the MSP (a useful self-consistency check).
- Full cradle-to-gate LCA of this system is treated in the
  [cross-framework LCA case study](../cross_framework_lca/), which pairs the BioSTEAM
  foreground inventory with background characterization factors.
