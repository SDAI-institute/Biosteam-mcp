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
    assert built["success"] is True
    result_id = built["result_id"]
    before = first.get_stream_results(result_id, "mixed")
    assert before["success"] is True

    second = BioSTEAMEngine(provenance=provenance)
    after = second.get_stream_results(result_id, "mixed")
    assert after["success"] is True
    assert result_id in second._store
    assert result_id in second._recovered_handles
    assert result_id in provenance.rows
    assert after["stream"]["mass_flow_kg_hr"] == before["stream"]["mass_flow_kg_hr"]
    assert after["stream"]["component_mass_flow_kg_hr"] == before["stream"]["component_mass_flow_kg_hr"]

    third = BioSTEAMEngine(provenance=provenance)
    again = third.get_stream_results(result_id, "mixed")
    assert again["success"] is True
    assert result_id in provenance.rows
    assert again["stream"]["mass_flow_kg_hr"] == before["stream"]["mass_flow_kg_hr"]


def test_new_build_after_restart_does_not_overwrite_persisted_handle() -> None:
    provenance = MemoryProvenance()
    first = BioSTEAMEngine(provenance=provenance)
    built = first.build_system_from_spec(copy.deepcopy(SPEC))
    original_id = built["result_id"]
    assert original_id == "sys_custom_1"

    second = BioSTEAMEngine(provenance=provenance)
    new_build = second.build_system_from_spec(copy.deepcopy(SPEC))
    assert new_build["success"] is True
    assert new_build["result_id"] == "sys_custom_2"
    assert original_id in provenance.rows

    recovered = second.get_stream_results(original_id, "mixed")
    assert recovered["success"] is True
    assert original_id in provenance.rows


def test_runtime_mismatch_refuses_reconstruction() -> None:
    provenance = MemoryProvenance()
    first = BioSTEAMEngine(provenance=provenance)
    built = first.build_system_from_spec(copy.deepcopy(SPEC))
    result_id = built["result_id"]
    provenance.rows[result_id]["runtime"] = {"biosteam": "different"}

    second = BioSTEAMEngine(provenance=provenance)
    result = second.simulate_system(result_id)
    assert result["success"] is False
    assert "runtime fingerprint differs" in result["error"]
    assert result_id not in second._store


def test_operating_hours_state_and_dispose_persist_across_restart() -> None:
    provenance = MemoryProvenance()
    first = BioSTEAMEngine(provenance=provenance)
    built = first.build_system_from_spec(copy.deepcopy(SPEC))
    result_id = built["result_id"]

    lca = first.get_lca_results(result_id, "GWP", {"water": 0.1}, operating_days=123)
    assert lca["success"] is True
    assert provenance.rows[result_id]["payload"]["state"]["operating_hours"] == 24 * 123

    second = BioSTEAMEngine(provenance=provenance)
    entry = second._resolve_entry(result_id)
    assert entry is not None
    assert float(entry["system"].operating_hours) == 24 * 123

    disposed = second.dispose_result(result_id)
    assert disposed["success"] is True
    assert result_id not in provenance.rows

    third = BioSTEAMEngine(provenance=provenance)
    missing = third.simulate_system(result_id)
    assert missing["success"] is False
    assert "unknown result_id" in missing["error"]
