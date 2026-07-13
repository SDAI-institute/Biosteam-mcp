# %% [markdown]
# # Tier 0 â€” Foundations: your first BioSTEAM flowsheet
#
# **Goal:** meet the five objects the whole stack is built from, then build,
# simulate, and inspect a small process â€” end to end.
#
# The object model, bottom to top:
#
# | Object | Package | What it is |
# |--------|---------|-----------|
# | `Chemical` / `Chemicals` | thermosteam | a species and its thermo properties |
# | `Stream` | thermosteam | flowing material (composition, T, P, phase) |
# | `Unit` | biosteam | a piece of equipment that transforms streams |
# | `System` | biosteam | units wired together, solved (incl. recycle) |
# | `TEA` | biosteam | techno-economic analysis over a `System` |
#
# You *build* streams and units, wire them into a system, `simulate()`, then read
# results back off the objects. That loop is the whole framework.

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst
import thermosteam as tmo

print("BioSTEAM", bst.__version__, "| thermosteam", tmo.__version__)

# %% [markdown]
# ## 1. Define a thermodynamic property package
#
# Nothing has properties until you tell the stack which chemicals exist. This
# "sets the thermo" â€” every stream created afterward shares this package.

# %%
bst.settings.set_thermo(["Water", "Ethanol"])
bst.settings.get_thermo().chemicals

# %% [markdown]
# ## 2. Create a stream
#
# A `Stream` carries molar flows plus a thermodynamic state (T, P, phase). Ask it
