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
