# %% [markdown]
# # Case study — Sanitation & nutrient recovery under uncertainty (QSDsan)
#
# A resource-recovery sanitation step treats municipal wastewater and recovers N and P.
# Real recovery efficiencies and influent loads are *uncertain*, so we wrap the system
# in a `Model` and run Monte Carlo to get **distributions** of recovered phosphorus and
# effluent quality — the deliverable a sanitation designer actually reports.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import chaospy as cp
import qsdsan as qs
import biosteam as bst

cmps = qs.Components.load_default()
qs.set_thermo(cmps)
print("QSDsan", qs.__version__)

# %% [markdown]
# ## System: influent + a nutrient-recovery SanUnit

# %%
inf = qs.WasteStream("influent")
inf.set_flow_by_concentration(
    flow_tot=1000,
    concentrations={"S_F": 200, "X_B_Subst": 150, "S_NH4": 40, "S_PO4": 8},
    units=("m3/hr", "mg/L"),
)

class NutrientRecovery(qs.SanUnit):
    _N_ins = 1
    _N_outs = 2
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
        for cmp, frac in (("S_NH4", self.N_recovery), ("S_PO4", self.P_recovery)):
            moved = influent.imass[cmp] * frac
            effluent.imass[cmp] -= moved
            recovered.imass[cmp] += moved

U1 = NutrientRecovery("U1", ins=inf, outs=("effluent", "recovered"))
sys = qs.System("san_sys", path=[U1])
sys.simulate()
print(f"baseline P recovered = {U1.outs[1].imass['S_PO4']:.2f} kg/hr")

# %% [markdown]
# ## Uncertain model
#
# Three uncertain inputs: N and P recovery efficiencies and influent phosphate load.
# Metrics: recovered P (kg/hr) and effluent total nitrogen (mg/L).

# %%
def m_P_recovered():
    return U1.outs[1].imass["S_PO4"]
def m_effluent_TN():
    return U1.outs[0].TN

model = bst.Model(sys, indicators=[
    bst.Metric("P recovered", m_P_recovered, "kg/hr"),
    bst.Metric("Effluent TN", m_effluent_TN, "mg/L"),
])

@model.parameter(name="N recovery", element=U1, coupled=True,
                 distribution=cp.Uniform(0.4, 0.8))
def set_N(x):
    U1.N_recovery = x

@model.parameter(name="P recovery", element=U1, coupled=True,
                 distribution=cp.Triangle(0.6, 0.8, 0.95))
def set_P(x):
    U1.P_recovery = x

@model.parameter(name="Influent PO4", element=inf, coupled=True,
                 units="mg/L", distribution=cp.Uniform(6, 12))
def set_PO4(c):
    inf.set_flow_by_concentration(
        flow_tot=1000,
        concentrations={"S_F": 200, "X_B_Subst": 150, "S_NH4": 40, "S_PO4": c},
        units=("m3/hr", "mg/L"),
    )

# %% [markdown]
# ## Monte Carlo

# %%
np.random.seed(7)
samples = model.sample(N=300, rule="L")
model.load_samples(samples)
model.evaluate()

P_rec = np.asarray(model.table.iloc[:, -2], dtype=float)   # P recovered column
TN_eff = np.asarray(model.table.iloc[:, -1], dtype=float)  # effluent TN column
p5, p50, p95 = np.percentile(P_rec, [5, 50, 95])
print(f"P recovered  P5={p5:.2f}  P50={p50:.2f}  P95={p95:.2f} kg/hr")
print(f"effluent TN  mean={TN_eff.mean():.1f} mg/L  (range {TN_eff.min():.1f}-{TN_eff.max():.1f})")

# %% [markdown]
# ## Sensitivity: what drives phosphorus recovery?

# %%
rho, pvals = model.spearman_r()
rho_P = rho.iloc[:, 0]        # correlations vs first metric (P recovered)
ranked = rho_P.reindex(rho_P.abs().sort_values(ascending=False).index)
print("Spearman rho vs P recovered:")
print(ranked.round(3))

results = {
    "P_recovered_P50_kg_hr": round(float(p50), 2),
    "P_recovered_P90_range": [round(float(p5), 2), round(float(p95), 2)],
    "effluent_TN_mean_mgL": round(float(TN_eff.mean()), 1),
}
print(results)
print("QSDsan sanitation case study complete.")
