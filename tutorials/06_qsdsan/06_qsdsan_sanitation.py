# %% [markdown]
# # Tier 6 — QSDsan: sanitation & resource recovery
#
# QSDsan extends BioSTEAM to sanitation and resource-recovery systems. Its streams
# are **`WasteStream`s** (with wastewater composite variables — COD, BOD, N, P), its
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
# concentrations (mg/L) — how wastewater data actually arrives.

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
print(f"TN    = {inf.TN:,.1f} mg/L")
print(f"TP    = {inf.TP:,.1f} mg/L")

# nutrient loads (kg/hr): concentration (mg/L = g/m3) x flow (m3/hr) / 1000
N_load = inf.TN * inf.F_vol / 1000
P_load = inf.TP * inf.F_vol / 1000
print(f"N load = {N_load:,.1f} kg/hr   P load = {P_load:,.1f} kg/hr")

# %% [markdown]
# ## 3. A resource-recovery SanUnit
#
# A `SanUnit` follows the same pattern as `bst.Unit` but operates on `WasteStream`s.
# This one recovers a fraction of nutrients (N, P) into a concentrated product stream
# and passes treated effluent — the essence of resource recovery.

# %%
class NutrientRecovery(qs.SanUnit):
    """Split recoverable nutrients into a concentrated recovery stream."""
    _N_ins = 1
    _N_outs = 2   # [0] treated effluent, [1] recovered nutrients

    def __init__(self, ID="", ins=None, outs=(), thermo=None,
                 init_with="WasteStream", *, N_recovery=0.6, P_recovery=0.8):
        super().__init__(ID, ins, outs, thermo, init_with=init_with)
        self.N_recovery = N_recovery
        self.P_recovery = P_recovery

    def _run(self):
        influent = self.ins[0]
        effluent, recovered = self.outs
        effluent.copy_like(influent)
        recovered.empty()
        # Move a fraction of the N- and P-bearing components into the recovery stream.
        for cmp, frac in (("S_NH4", self.N_recovery), ("S_PO4", self.P_recovery)):
            moved = influent.imass[cmp] * frac
            effluent.imass[cmp] -= moved
            recovered.imass[cmp] += moved

U1 = NutrientRecovery("U1", ins=inf, outs=("effluent", "recovered"),
                      N_recovery=0.6, P_recovery=0.8)

sys = qs.System("recovery_sys", path=[U1])
sys.simulate()

# %% [markdown]
# ## 4. Removal efficiency and recovered mass

# %%
eff, rec = U1.outs
TN_removal = 1 - eff.TN / inf.TN
TP_removal = 1 - eff.TP / inf.TP
N_recovered = rec.imass["S_NH4"]     # kg/hr
P_recovered = rec.imass["S_PO4"]     # kg/hr
print(f"effluent TN = {eff.TN:,.1f} mg/L  (TN removal {100*TN_removal:.0f}%)")
print(f"effluent TP = {eff.TP:,.1f} mg/L  (TP removal {100*TP_removal:.0f}%)")
print(f"recovered N = {N_recovered:,.1f} kg/hr")
print(f"recovered P = {P_recovered:,.1f} kg/hr")

summary = {
    "influent_COD_mgL": round(float(inf.COD), 1),
    "TN_removal_pct": round(100 * float(TN_removal), 1),
    "P_recovered_kg_hr": round(float(P_recovered), 2),
}
print(summary)

# %% [markdown]
# ## You can now…
# - load QSDsan `Components` and build a `WasteStream` by concentration;
# - read composite variables (COD, BOD, TN, TP) and compute nutrient loads;
# - write a `SanUnit` and assemble/simulate a QSDsan `System`;
# - quantify removal efficiency and recovered resource mass.
#
# > Beyond steady state, QSDsan does **dynamic** process simulation (ASM/ADM models
# > via `Process` objects) and ships validated systems in **EXPOsan**. The QSDsan
# > case study builds one of these end to end with uncertainty.
#
# **Next — Tier 7 (`07_uncertainty_optimization`)**: `Model`s, Monte Carlo, sensitivity,
# and optimization across BioSTEAM *and* QSDsan.
print("Tier 6 complete.")
