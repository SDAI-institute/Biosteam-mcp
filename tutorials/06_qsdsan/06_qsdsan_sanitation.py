# %% [markdown]
# # Tier 6 â€” QSDsan: sanitation & resource recovery
#
# QSDsan extends BioSTEAM to sanitation and resource-recovery systems. Its streams
# are **`WasteStream`s** (with wastewater composite variables â€” COD, BOD, N, P), its
# units are **`SanUnit`s**, and it ships 100+ published unit models plus dynamic
# process simulation. This tier:
#
# 1. Loads QSDsan `Components` and builds a `WasteStream` by concentration.
# 2. Reads composite variables (COD, BOD, TN, TP).
# 3. Builds a resource-recovery `SanUnit` and a small `System`.
# 4. Computes removal efficiency and recovered nutrient mass.

# %%
import warnings
warnings.filterwarnings("ignore")

import qsdsan as qs
import qsdsan.sanunits as su

cmps = qs.Components.load_default()
qs.set_thermo(cmps)
print("QSDsan", qs.__version__, "| loaded", len(cmps), "components")
print("available SanUnit models:", len([n for n in dir(su) if n[0].isupper()]))

# %% [markdown]
# ## 1. An influent WasteStream by concentration
#
# `set_flow_by_concentration` builds a stream from a volumetric flow and pollutant
# concentrations (mg/L) â€” how wastewater data actually arrives.

# %%
inf = qs.WasteStream("influent")
inf.set_flow_by_concentration(
    flow_tot=1000,                       # m3/hr
    concentrations={
        "S_F": 200,       # readily biodegradable COD
        "X_B_Subst": 150, # slowly biodegradable substrate
        "S_NH4": 40,      # ammonium N
        "S_PO4": 8,       # phosphate P
    },
    units=("m3/hr", "mg/L"),
)

# %% [markdown]
# ## 2. Composite variables
#
# QSDsan computes wastewater aggregates from the component composition automatically.

# %%
print(f"flow  = {inf.F_vol:,.0f} m3/hr")
print(f"COD   = {inf.COD:,.1f} mg/L")
print(f"BOD   = {inf.BOD:,.1f} mg/L")
