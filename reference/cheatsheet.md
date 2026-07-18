# BioSTEAM / QSDsan cheat-sheet

Quick, copy-pasteable snippets for the versions in `envShilab` (BioSTEAM 2.51,
thermosteam 0.51, QSDsan 1.4).

## Thermo & streams
```python
import biosteam as bst, thermosteam as tmo
bst.settings.set_thermo(["Water", "Ethanol"])          # active property package
s = bst.Stream("s", Water=100, Ethanol=50, units="kmol/hr", T=350, P=101325)
s.F_mass, s.F_mol, s.F_vol, s.rho, s.H                  # derived quantities
s.imol["Ethanol"], s.imass["Ethanol"]                  # indexed flows
s.vle(P=101325, V=0.5); s["g"]; s["l"]                 # flash to a vapor fraction
```

## Units
```python
F1 = bst.Flash("F1", ins=s, outs=("v", "l"), V=0.5, P=101325)
H1 = bst.HXutility("H1", ins=s, outs="hot", T=370)
D1 = bst.BinaryDistillation("D1", ins=s, outs=("d","b"),
                            LHK=("Water","Glycerol"), k=1.5, Lr=0.99, Hr=0.99, P=101325)
u.simulate()
u.design_results          # dict of sized quantities
u.purchase_cost, u.installed_cost
D1.design_results["Reflux"], D1.design_results["Actual stages"]   # NOT D1.reflux
```

## Reactions
```python
from thermosteam.reaction import Reaction
rxn = Reaction("Glucose -> 2 Ethanol + 2 CO2", reactant="Glucose", X=0.9)
rxn(stream)               # apply conversion in place
```

## Custom unit
```python
class MyUnit(bst.Unit):
    _N_ins = 1; _N_outs = 1
    def _run(self):
        out = self.outs[0]; out.copy_like(self.ins[0])
        # ... transform out ...
```

## Systems
```python
sys = bst.System.from_units("sys", units=[U1, U2, U3])   # auto-detects recycle
sys.simulate(); sys.show()
sys.units, sys.feeds, sys.products, sys.installed_equipment_cost
```

## TEA (subclass; implement `_FOC`)
```python
class MyTEA(bst.TEA):
    def _FOC(self, FCI): return self.labor_cost + FCI * 0.02
tea = MyTEA(sys, IRR=0.10, duration=(2020,2040), depreciation="MACRS7",
            income_tax=0.21, operating_days=330, lang_factor=3, ...)
tea.FCI, tea.FOC, tea.VOC, tea.NPV
tea.solve_price(product)          # MSP
tea.solve_IRR(); tea.get_cashflow_table()
```

## LCA
```python
bst.settings.define_impact_indicator("GWP", "kg*CO2e")
feed.set_CF("GWP", 1.2)                       # per kg
bst.PowerUtility.set_CF("GWP", 0.45)          # per kWh
sys.operating_hours = 24 * 330                # REQUIRED for the aggregators (annual)
sys.get_total_feeds_impact("GWP")             # kg CO2e/yr
sys.get_net_electricity_impact("GWP")
```

## Uncertainty & sensitivity
```python
import chaospy as cp
model = bst.Model(sys, indicators=[bst.Metric("MSP", getter, "USD/kg")])   # `indicators`, not `metrics`
@model.parameter(name="Feed price", element=feed, kind="isolated",
                 distribution=cp.Triangle(0.05, 0.10, 0.16))
def _(p): feed.price = p
samples = model.sample(N=200, rule="L"); model.load_samples(samples); model.evaluate()
model.table                     # results DataFrame (params + indicators)
rho, pvalues = model.spearman_r()   # returns TWO DataFrames
```

## QSDsan
```python
import qsdsan as qs
cmps = qs.Components.load_default(); qs.set_thermo(cmps)
ws = qs.WasteStream("ws")
ws.set_flow_by_concentration(1000, {"S_F":200,"S_NH4":40}, units=("m3/hr","mg/L"))
ws.COD, ws.BOD, ws.TN, ws.TP    # composite variables
class MySanUnit(qs.SanUnit):     # NOTE: qs.SanUnit, not qs.sanunits.SanUnit
    _N_ins = 1; _N_outs = 2
    def _run(self): ...
qs.System("s", path=[U1]).simulate()
# qs.System / qs.TEA / qs.Model subclass the BioSTEAM ones -> tooling is shared.
```

## Published biorefineries
```python
from biorefineries import cornstover as cs
cs.load()
cs.cornstover_sys, cs.cornstover_tea, cs.ethanol
cs.cornstover_tea.solve_price(cs.ethanol)     # ~$0.69/kg
```
