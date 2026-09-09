# Results — Cross-framework LCA

Demonstrates the foreground/background split and reconciles BioSTEAM's built-in
impact aggregation against an independent inventory × CF calculation (the pattern
for coupling BioSTEAM with openLCA / Brightway).

## Headline numbers
| Path | Total GWP |
|------|-----------|
| BioSTEAM `get_total_feeds_impact` + `get_net_electricity_impact` | 325.330 kt CO₂e/yr |
| Independent inventory × background CF | 325.330 kt CO₂e/yr |
| Relative difference | 0.00 (exact) |

## Foreground inventory (per year)
| Flow | Amount | Background CF | Contribution |
|------|--------|---------------|--------------|
| Glucose feed | 271,096,373 kg | 1.20 kg CO₂e/kg | 325.316 kt |
| Electricity | 32,564 kWh | 0.45 kg CO₂e/kWh | 0.015 kt |

## Takeaway
BioSTEAM supplies the **foreground inventory**; the **background CFs** come from your
database ecosystem (openLCA / Brightway). Because the two aggregation paths agree
exactly, the inventory is portable — you can compute impacts in BioSTEAM for speed and
re-run them against a full ecoinvent background in openLCA for a formal study. This is
the seam where the BioSTEAM MCP plugs into your existing LCA Copilot.
