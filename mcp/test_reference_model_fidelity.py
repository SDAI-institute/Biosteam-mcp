"""
Reference-model fidelity check (SDAI reliability pass, WS3.1).

BioSTEAM is a process-simulation/TEA tool, NOT an LCA engine -- its numbers
have no LCA benchmark to be judged against. The correctness question that
matters here is narrower and more important: does the MCP layer (engine.py's
build_system/simulate_system/get_tea_results) faithfully proxy BioSTEAM's own
simulation output for one of its own shipped reference models, or does the
wrapper's attribute-discovery heuristic (`_find_attr`) or unit conversion
introduce error?

Run in TWO SEPARATE subprocesses (not two imports in one process) so a
result can't be trivially "correct" just because Python's module cache
handed both code paths the identical object -- each subprocess gets a fresh
interpreter and re-simulates independently.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent

_VIA_ENGINE = rf"""
import sys, json
sys.path.insert(0, r"{MCP_DIR}")
from engine import BioSTEAMEngine

eng = BioSTEAMEngine()
built = eng.build_system("cornstover")
assert built["success"], built
rid = built["result_id"]
sim = eng.simulate_system(rid)
assert sim["success"], sim
tea = eng.get_tea_results(rid)
assert tea["success"], tea
print(json.dumps(tea["tea"]))
"""

_DIRECT_API = r"""
import importlib, json

mod = importlib.import_module("biorefineries.cornstover")
mod.load()
system = mod.sys
tea = mod.tea
product = mod.ethanol
system.simulate()

out = {
    "FCI_MM": round(tea.FCI / 1e6, 3),
    "FOC_MM_per_yr": round(tea.FOC / 1e6, 3),
    "VOC_MM_per_yr": round(tea.VOC / 1e6, 3),
    "NPV_MM": round(tea.NPV / 1e6, 2),
    "MSP_usd_per_kg": round(float(tea.solve_price(product)), 4),
}
print(json.dumps(out))
"""


def _run(code: str) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, (
        f"subprocess failed (rc={result.returncode}):\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    # last non-empty line is the JSON payload (biosteam prints noisy warnings)
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    return json.loads(lines[-1])


def test_mcp_engine_matches_direct_biosteam_api():
    """The MCP wrapper's TEA numbers for the cornstover reference model must
    match calling BioSTEAM/biorefineries directly, within floating-point
    tolerance -- confirms build_system's _find_attr heuristic picks the
    right system/tea/product and introduces no translation error."""
    via_engine = _run(_VIA_ENGINE)
    direct = _run(_DIRECT_API)

    assert set(via_engine.keys()) == set(direct.keys())
    for key in direct:
        assert via_engine[key] == direct[key], (
            f"{key}: engine={via_engine[key]!r} vs direct={direct[key]!r}"
        )
