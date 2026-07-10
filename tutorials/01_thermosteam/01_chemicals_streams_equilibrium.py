# %% [markdown]
# # Tier 1 — thermosteam: chemicals, streams, and phase equilibrium
#
# thermosteam is the thermodynamic engine under BioSTEAM. This tier covers:
#
# 1. `Chemical` and `Chemicals` — species and their properties.
# 2. Property packages and how a `Stream` uses them.
# 3. Multiphase streams and vapor–liquid equilibrium (VLE).
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
# A `Chemical` knows its constants (MW, Tb, Tc…) and temperature-dependent models
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

# %%
s = tmo.Stream("s", Water=50, Ethanol=50, units="kmol/hr", T=298.15, P=101325)
print(f"F_mass = {s.F_mass:,.1f} kg/hr")
print(f"rho    = {s.rho:,.1f} kg/m3")
print(f"H      = {s.H:,.0f} kJ/hr (enthalpy relative to reference)")
s.show(flow="kmol/hr")

# %% [markdown]
# ## 4. Vapor–liquid equilibrium
#
# Ask a stream to flash to a target vapor fraction `V` at fixed `P`; thermosteam
# solves the VLE and splits the stream into coexisting phases. Ethanol, being more
# volatile, concentrates in the vapor — the basis of distillation (Tier 2).

# %%
ms = tmo.Stream("ms", Water=50, Ethanol=50, units="kmol/hr")
ms.vle(P=101325, V=0.5)          # 50% vaporized at 1 atm
vapor = ms["g"]
liquid = ms["l"]
y_EtOH = vapor.imol["Ethanol"] / vapor.F_mol
x_EtOH = liquid.imol["Ethanol"] / liquid.F_mol
print(f"flash T        = {ms.T:.2f} K")
print(f"y_Ethanol(vap) = {y_EtOH:.3f}")
print(f"x_Ethanol(liq) = {x_EtOH:.3f}")
print(f"relative volatility (K_EtOH/K_Water) proxy: {y_EtOH/x_EtOH:.2f}")

# %% [markdown]
# ### Bubble and dew points
#
# The bubble point is where the first vapor bubble forms; the dew point where the
# last liquid drop remains. thermosteam computes both from the property package.

# %%
bp = tmo.equilibrium.BubblePoint(chems["Water", "Ethanol"])
dp = tmo.equilibrium.DewPoint(chems["Water", "Ethanol"])
z = np.array([0.5, 0.5])
Tb, y = bp.solve_Ty(z=z, P=101325)
Td, x = dp.solve_Tx(z=z, P=101325)
print(f"bubble T = {Tb:.2f} K,  first vapor y_EtOH = {y[1]:.3f}")
print(f"dew    T = {Td:.2f} K,  last liquid x_EtOH = {x[1]:.3f}")

# %% [markdown]
# ## 5. Mixing and the energy balance
#
# Mixing streams conserves mass and energy. Mix a hot and a cold stream *adiabatically*
# and thermosteam finds the outlet temperature that closes the energy balance.

# %%
hot = tmo.Stream("hot", Water=100, units="kmol/hr", T=360)
cold = tmo.Stream("cold", Water=100, units="kmol/hr", T=300)
mixed = tmo.Stream("mixed")
mixed.mix_from([hot, cold], energy_balance=True)
print(f"adiabatic mix T = {mixed.T:.2f} K  (between 300 and 360 K)")

summary = {
    "flash_T_K": round(float(ms.T), 2),
    "y_ethanol_vapor": round(float(y_EtOH), 3),
    "bubble_T_K": round(float(Tb), 2),
    "mixed_T_K": round(float(mixed.T), 2),
}
print(summary)

# %% [markdown]
# ## You can now…
# - build `Chemical`/`Chemicals` and query properties (MW, Tb, `Psat`);
# - create streams and read derived quantities (`F_mass`, `rho`, `H`);
# - run VLE (`.vle`), bubble/dew points, and adiabatic mixing energy balances.
#
# **Next — Tier 2 (`02_unit_operations`)**: turn this thermodynamics into equipment
# — reactors, distillation, heat exchangers — and write a custom `Unit`.
print("Tier 1 complete.")
