# %% [markdown]
# # Tier 1 â€” thermosteam: chemicals, streams, and phase equilibrium
#
# thermosteam is the thermodynamic engine under BioSTEAM. This tier covers:
#
# 1. `Chemical` and `Chemicals` â€” species and their properties.
# 2. Property packages and how a `Stream` uses them.
# 3. Multiphase streams and vaporâ€“liquid equilibrium (VLE).
# 4. Mixing and energy balances.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import thermosteam as tmo

print("thermosteam", tmo.__version__)

# %% [markdown]
# ## 1. A single chemical and its properties
#
# A `Chemical` knows its constants (MW, Tb, Tcâ€¦) and temperature-dependent models
# (vapor pressure, heat capacity, density). Properties are looked up / estimated
# from thermosteam's databanks.

# %%
water = tmo.Chemical("Water")
print(f"Water  MW={water.MW:.3f} g/mol  Tb={water.Tb:.2f} K  Tc={water.Tc:.1f} K")
print(f"Psat(373.15 K) = {water.Psat(373.15):,.0f} Pa   (~1 atm, as expected)")

# %% [markdown]
# ## 2. A property package (`Chemicals`) and setting thermo
#
# A `Chemicals` object is the package a stream draws on. `set_thermo` makes it the
# active package so every new `Stream` shares it.

# %%
chems = tmo.Chemicals(["Water", "Ethanol", "Glycerol"])
tmo.settings.set_thermo(chems)
for c in chems:
    print(f"{c.ID:10s} MW={c.MW:7.3f}  Tb={c.Tb:7.2f} K")

# %% [markdown]
# ## 3. Streams and derived quantities
#
# A `Stream` stores molar flows plus (T, P, phase); everything else is computed.

