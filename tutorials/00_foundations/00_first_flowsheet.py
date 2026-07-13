# %% [markdown]
# # Tier 0 — Foundations: your first BioSTEAM flowsheet
#
# **Goal:** meet the five objects the whole stack is built from, then build,
# simulate, and inspect a small process — end to end.
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
# "sets the thermo" — every stream created afterward shares this package.

# %%
bst.settings.set_thermo(["Water", "Ethanol"])
bst.settings.get_thermo().chemicals

# %% [markdown]
# ## 2. Create a stream
#
# A `Stream` carries molar flows plus a thermodynamic state (T, P, phase). Ask it
# for derived quantities and it computes them from the property package.

# %%
feed = bst.Stream("feed", Water=1000, Ethanol=500, units="kmol/hr", T=298.15)
print(f"mass flow      : {feed.F_mass:,.0f} kg/hr")
print(f"vol. flow      : {feed.F_vol:,.2f} m3/hr")
print(f"ethanol mass % : {100 * feed.imass['Ethanol'] / feed.F_mass:.1f}%")
feed.show()

# %% [markdown]
# ## 3. Add units
#
# A `Flash` drum partially vaporizes the feed; ethanol (more volatile) enriches in
# the vapor. Units declare their inlets (`ins`) and outlets (`outs`); we give the
# flash a vapor fraction `V` and pressure `P` as its operating spec.

# %%
F1 = bst.Flash("F1", ins=feed, outs=("vapor", "liquid"), V=0.5, P=101325)

# %% [markdown]
# ## 4. Wire units into a System and simulate
#
# A `System` sequences the units and solves them (converging any recycle loops).
# `simulate()` runs mass/energy balances and populates every outlet stream.

# %%
sys = bst.System("sys", path=[F1])
sys.simulate()

vapor, liquid = F1.outs
x_vap = vapor.imol["Ethanol"] / vapor.F_mol
x_liq = liquid.imol["Ethanol"] / liquid.F_mol
print(f"ethanol mole fraction  vapor={x_vap:.3f}  liquid={x_liq:.3f}")
print(f"flash separated the more-volatile ethanol into the vapor: {x_vap > x_liq}")

# %% [markdown]
# ## 5. Read results back off the objects
#
# Results live on the objects you built — no separate results file. This is how
# every later tier extracts numbers (and how the MCP server will, too).

# %%
sys.show()

# %%
# A one-line programmatic summary — the pattern the case studies reuse.
summary = {
    "feed_kg_hr": round(feed.F_mass, 1),
    "vapor_ethanol_molfrac": round(x_vap, 3),
    "liquid_ethanol_molfrac": round(x_liq, 3),
}
print(summary)

# %% [markdown]
# ## You can now…
#
# - set a thermo property package and create streams with `bst.Stream`;
# - instantiate a `Unit` (here `Flash`) with `ins`/`outs` and an operating spec;
# - assemble a `System` and `simulate()` it;
# - read derived results (`F_mass`, `imol`, `.show()`) back off the objects.
#
# **Next — Tier 1 (`01_thermosteam`)**: go one layer down into chemicals, property
# packages, multiphase streams, and phase equilibrium — the engine under all of this.
print("Tier 0 complete.")
