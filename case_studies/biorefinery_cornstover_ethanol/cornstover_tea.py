# %% [markdown]
# # Case study — Cornstover → ethanol biorefinery (TEA)
#
# The canonical BioSTEAM biorefinery: dilute-acid pretreatment + enzymatic hydrolysis
# + co-fermentation of corn stover to cellulosic ethanol, based on the NREL design.
# We load the published model and extract its techno-economics, then run a feedstock-
# price sensitivity. **Headline reproduced:** MSP ≈ $0.69/kg ethanol.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from biorefineries import cornstover as cs

cs.load()
sys = cs.cornstover_sys
tea = cs.cornstover_tea
ethanol = cs.ethanol
print("units in system:", len(sys.units))

# %% [markdown]
# ## Scale

# %%
OPERATING_HOURS = tea.operating_hours
ethanol_kg_hr = ethanol.F_mass
ethanol_kt_yr = ethanol_kg_hr * OPERATING_HOURS / 1e6
print(f"ethanol output   = {ethanol_kg_hr:,.0f} kg/hr  ({ethanol_kt_yr:,.0f} kt/yr)")
print(f"operating hours  = {OPERATING_HOURS:,.0f} hr/yr")

# %% [markdown]
# ## Techno-economics
#
# `solve_price` returns the minimum ethanol selling price (MSP) at the model's target
# IRR. Because the model's ethanol price is calibrated to that MSP, `solve_IRR`
# returns the target return — a good sanity check.

# %%
msp = tea.solve_price(ethanol)
irr = tea.solve_IRR()
print(f"MSP              = ${msp:.4f}/kg ethanol")
print(f"IRR at MSP       = {irr:.1%}   (target return, by calibration)")
print(f"installed equip  = ${tea.installed_equipment_cost/1e6:,.1f} MM")
print(f"FCI              = ${tea.FCI/1e6:,.1f} MM")
print(f"FOC              = ${tea.FOC/1e6:,.1f} MM/yr")
print(f"VOC              = ${tea.VOC/1e6:,.1f} MM/yr")

# %% [markdown]
# ## Feedstock-price sensitivity
#
# Corn stover price is the dominant cost lever. Sweep it and re-solve MSP.

# %%
base_price = cs.cornstover.price
print(f"baseline cornstover price = ${base_price*1000:,.1f}/tonne")
factors = [0.6, 0.8, 1.0, 1.2, 1.4]
rows = []
for f in factors:
    cs.cornstover.price = base_price * f
    sys.simulate()
    rows.append((base_price * f * 1000, tea.solve_price(ethanol)))
cs.cornstover.price = base_price
sys.simulate()
for price_t, msp_f in rows:
    print(f"  cornstover ${price_t:6,.1f}/t -> MSP ${msp_f:.4f}/kg")
slope = (rows[-1][1] - rows[0][1]) / (rows[-1][0] - rows[0][0]) * 1000
print(f"dMSP/d(feed $/t) ~ ${slope:.4f} per kg per $1000/t")

# %% [markdown]
# ## Headline results (recorded in results.md)

# %%
results = {
    "n_units": len(sys.units),
    "ethanol_kt_per_yr": round(float(ethanol_kt_yr), 0),
    "MSP_usd_per_kg": round(float(msp), 4),
    "IRR_at_MSP": round(float(irr), 3),
    "FCI_MM": round(float(tea.FCI) / 1e6, 1),
    "installed_equipment_MM": round(float(tea.installed_equipment_cost) / 1e6, 1),
}
print(results)
print("Cornstover case study complete.")
