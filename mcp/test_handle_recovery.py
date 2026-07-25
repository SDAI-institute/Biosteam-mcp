from __future__ import annotations

import copy

from engine import BioSTEAMEngine
from src.handle_provenance import runtime_fingerprint


class MemoryProvenance:
    def __init__(self) -> None:
        self.rows = {}

    def save(self, result_id, kind, payload):
        self.rows[result_id] = {
            "schema_version": 1,
            "result_id": result_id,
            "kind": kind,
            "payload": copy.deepcopy(payload),
            "runtime": runtime_fingerprint(),
        }
        return True

    def get(self, result_id):
        row = self.rows.get(result_id)
        return copy.deepcopy(row) if row is not None else None

    def delete(self, result_id):
        self.rows.pop(result_id, None)


SPEC = {
    "id": "recovery_probe",
    "thermo": ["Water", "Ethanol"],
    "thermo_model": "ideal",
    "streams": [
        {"id": "water", "flows": {"Water": 10.0}, "units": "kmol/hr"},
        {"id": "ethanol", "flows": {"Ethanol": 2.0}, "units": "kmol/hr"},
    ],
    "units": [
        {"type": "Mixer", "id": "M1", "ins": ["water", "ethanol"], "outs": ["mixed"]},
    ],
    "product": "mixed",
    "attach_tea": True,
}


def test_custom_system_recovers_under_same_result_id() -> None:
    provenance = MemoryProvenance()
    first = BioSTEAMEngine(provenance=provenance)
    built = first.build_system_from_spec(copy.deepcopy(SPEC))
