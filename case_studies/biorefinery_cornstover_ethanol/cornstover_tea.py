# %% [markdown]
# # Case study â€” Cornstover â†’ ethanol biorefinery (TEA)
#
# The canonical BioSTEAM biorefinery: dilute-acid pretreatment + enzymatic hydrolysis
# + co-fermentation of corn stover to cellulosic ethanol, based on the NREL design.
# We load the published model and extract its techno-economics, then run a feedstock-
# price sensitivity. **Headline reproduced:** MSP â‰ˆ $0.69/kg ethanol.

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
