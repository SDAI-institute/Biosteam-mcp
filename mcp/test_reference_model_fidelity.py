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
