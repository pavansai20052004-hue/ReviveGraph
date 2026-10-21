"""Production engine regression tests; handwritten examples are never app inputs."""
import copy
import json
from itertools import product
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from revivegraph.main import create_app, inventory
from revivegraph.optimizer import generate_configurations, solve, validate_output
from revivegraph import optimizer

FIXTURE = Path(__file__).resolve().parents[2] / "datasets" / "synthetic-v1"
HEADERS = {"X-Actor-ID": "engine-test", "Idempotency-Key": "engine-test-key"}


@pytest.fixture
def snapshot(tmp_path):
    app = create_app(tmp_path / "engine.sqlite3", FIXTURE)
    client = TestClient(app)
    registration = client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).json()["id"]
    batch = client.post("/api/v1/imports/preview", data={"registration_id": registration},
                        files={"computers_file": ("computers.csv", (FIXTURE / "computers.csv").read_bytes()),
                               "components_file": ("components.csv", (FIXTURE / "components.csv").read_bytes())}, headers=HEADERS).json()
    result = client.post(f"/api/v1/imports/{batch['batch_id']}/commit",
                         json={"preview_hash": batch["preview_hash"], "expected_revision": 0}, headers=HEADERS)
    assert result.status_code == 200, result.text
    with app.state.db.connect() as connection:
        computers, components = inventory(connection, "RG-DEMO-12")
    return {"computers": computers, "components": components, "operation_costs": json.loads((FIXTURE / "operation_costs.json").read_text()),
            "mode": "simulation", "failed_component_ids": []}


def restricted(snapshot, target_ids, candidate_ids):
    result = copy.deepcopy(snapshot)
    result["computers"] = [c for c in result["computers"] if c["asset_id"] in target_ids]
    result["components"] = [p for p in result["components"] if p["location_asset_id"] in target_ids or p["component_id"] in candidate_ids]
    # Restricted test universes treat listed external candidates as available stock.
    for p in result["components"]:
        if p["location_asset_id"] not in target_ids:
            p["location_asset_id"] = None
    return result


@pytest.mark.parametrize("target_ids,candidate_ids,budget,minutes,expected", [
    (["RG-PC-02", "RG-PC-04"], ["RG-RAM-15", "RG-RAM-16"], 58000, 82, 2),
    (["RG-PC-01", "RG-PC-03"], ["RG-SSD-06"], 64000, 88, 1),
    (["RG-PC-05"], ["RG-SSD-16"], 100000, 100, 0),
    (["RG-PC-02"], ["RG-RAM-04"], 100000, 100, 0),
    (["RG-PC-06"], ["RG-RAM-11"], 100000, 100, 0),
    (["RG-PC-09"], [], 100000, 100, 0),
    (["RG-PC-05"], ["RG-SSD-06"], 0, 38, 0),
    (["RG-PC-05"], ["RG-SSD-06"], 29000, 0, 0),
    (["RG-PC-05"], ["RG-SSD-06"], 29000, 38, 1),
    (["RG-PC-05"], ["RG-SSD-06"], 28999, 38, 0),
    (["RG-PC-05"], ["RG-SSD-06"], 29000, 37, 0),
])
def test_tiny_optima(snapshot, target_ids, candidate_ids, budget, minutes, expected):
    case = restricted(snapshot, target_ids, candidate_ids)
    result = solve(case, budget, minutes)
    assert result["totals"]["usable_final"] == expected
    assert result["solver"]["status"] == "OPTIMAL"
    assert result["solver"]["stable_tie_break_proven"]
    assert result["totals"]["newly_recovered"] == expected
    if len(target_ids) == 2 and "RG-PC-04" in target_ids:
        assert result["baseline"]["totals"]["usable_final"] == 1
        assert result["totals"]["cost_paise"] == 58000
        assert result["totals"]["technician_minutes"] == 82


def test_small_complete_enumeration_matches_cpsat(snapshot):
    case = restricted(snapshot, ["RG-PC-02", "RG-PC-04"], ["RG-RAM-15", "RG-RAM-16"])
    configs = generate_configurations(case)
    per_target = [[None] + [c for c in configs if c["target_asset_id"] == target] for target in ("RG-PC-02", "RG-PC-04")]
    feasible = []
    for choice in product(*per_target):
        allocations = [c for c in choice if c]
        # Independent tiny oracle: every supplied target requires one 8 GiB RAM
        # and retains its own healthy storage. One RAM removal, one install,
        # preparation and verification are required per recovered machine.
        ids = [a["ram_component_ids"][0] for a in allocations]
        if len(ids) != len(set(ids)):
            continue
        if any(a["target_asset_id"] == "RG-PC-04" and a["ram_component_ids"] != ["RG-RAM-15"] for a in allocations):
            continue
        cost, effort = len(allocations) * 29000, len(allocations) * 41
        if cost <= 58000 and effort <= 82:
            feasible.append(len(allocations))
    assert max(feasible) == solve(case, 58000, 82)["totals"]["usable_final"] == 2


def test_documented_feasible_arithmetic_independently_rechecked(snapshot):
    allocations = [
        {"target_asset_id": f"RG-PC-{n:02}", "ram_component_ids": [ram], "storage_component_id": storage}
        for n, ram, storage in [(1, "RG-RAM-01", "RG-SSD-06"), (2, "RG-RAM-11", "RG-SSD-02"),
                                 (3, "RG-RAM-03", "RG-SSD-11"), (4, "RG-RAM-07", "RG-SSD-05"),
                                 (5, "RG-RAM-05", "RG-SSD-12"), (6, "RG-RAM-12", "RG-SSD-07"),
                                 (7, "RG-RAM-08", "RG-SSD-15")]]
    checked = validate_output(snapshot, allocations, 250000, 330)
    assert checked["totals"] == {"cost_paise": 217000, "technician_minutes": 304, "transfers": 7, "usable_final": 7, "newly_recovered": 7}
    snapshot["failed_component_ids"] = ["RG-RAM-07"]
    with pytest.raises(ValueError, match="Ineligible component"):
        validate_output(snapshot, allocations, 250000, 330)
    allocations[3]["ram_component_ids"] = ["RG-RAM-15"]
    checked = validate_output(snapshot, allocations, 250000, 330)
    assert (checked["totals"]["cost_paise"], checked["totals"]["technician_minutes"]) == (215000, 299)


def test_main_deterministic_and_failure_selected_from_actual_plan(snapshot):
    result = solve(snapshot, 250000, 330)
    assert result["solver"]["status"] == "OPTIMAL"
    assert result["totals"]["cost_paise"] <= 250000
    assert result["totals"]["technician_minutes"] <= 330
    assert solve(snapshot, 250000, 330)["allocations"] == result["allocations"]
    donor_op = next(op for op in result["operations"] if op["operation"].startswith("remove_") and op["target_asset_id"] is not None and op["target_asset_id"] != op["asset_id"])
    snapshot["failed_component_ids"] = [donor_op["component_id"]]
    revised = solve(snapshot, 250000, 330)
    assert donor_op["component_id"] not in [part for a in revised["allocations"] for part in a["ram_component_ids"] + [a["storage_component_id"]]]
    assert revised["solver"]["status"] == "OPTIMAL"


def test_invalid_outputs_rejected(snapshot):
    allocation = {"target_asset_id": "RG-PC-05", "ram_component_ids": ["RG-RAM-05"], "storage_component_id": "RG-SSD-06"}
    with pytest.raises(ValueError, match="duplicate target"):
        validate_output(snapshot, [allocation, allocation], 100000, 100)
    with pytest.raises(ValueError, match="exceeds"):
        validate_output(snapshot, [allocation], 0, 100)
    second = {"target_asset_id": "RG-PC-01", "ram_component_ids": ["RG-RAM-01"], "storage_component_id": "RG-SSD-06"}
    with pytest.raises(ValueError, match="allocated twice"):
        validate_output(snapshot, [allocation, second], 100000, 100)
    allocation["ram_component_ids"] = ["RG-RAM-04"]
    with pytest.raises(ValueError, match="Ineligible component"):
        validate_output(snapshot, [allocation], 100000, 100)


def test_physical_and_unknown_assessments_are_excluded(snapshot):
    snapshot["mode"] = "physical"
    assert solve(snapshot, 250000, 330)["totals"]["usable_final"] == 0
    snapshot["mode"] = "simulation"
    case = restricted(snapshot, ["RG-PC-05"], ["RG-SSD-06"])
    next(p for p in case["components"] if p["component_id"] == "RG-SSD-06")["assessment"]["assessment_kind"] = "unknown"
    assert solve(case, 250000, 330)["totals"]["usable_final"] == 0


def test_already_usable_retained_configuration_costs_zero_and_is_not_recovered(snapshot):
    case = restricted(snapshot, ["RG-PC-05"], ["RG-SSD-06"])
    next(p for p in case["components"] if p["component_id"] == "RG-SSD-06")["location_asset_id"] = "RG-PC-05"
    result = solve(case, 0, 0)
    assert result["totals"] == {"cost_paise": 0, "technician_minutes": 0, "transfers": 0, "usable_final": 1, "newly_recovered": 0}
    assert not result["operations"]


def test_donor_displacement_removal_counted_once(snapshot):
    case = restricted(snapshot, ["RG-PC-02", "RG-PC-05"], ["RG-RAM-15", "RG-SSD-06"])
    allocations = [
        {"target_asset_id": "RG-PC-02", "ram_component_ids": ["RG-RAM-05"], "storage_component_id": "RG-SSD-02"},
        {"target_asset_id": "RG-PC-05", "ram_component_ids": ["RG-RAM-15"], "storage_component_id": "RG-SSD-06"},
    ]
    checked = validate_output(case, allocations, 100000, 200)
    assert sum(o["component_id"] == "RG-RAM-05" and o["operation"] == "remove_ram" for o in checked["operations"]) == 1
    assert checked["totals"]["usable_final"] == 2
    assert checked["totals"]["cost_paise"] == 65000
    # Both targets need prep+verification, two RAM installs, one SSD install,
    # and the old faulty PC-02 RAM plus transferred PC-05 RAM are each removed.
    assert checked["totals"]["technician_minutes"] == 92
    # The solver itself must not count the donor without its valid replacement.
    limited = restricted(snapshot, ["RG-PC-02", "RG-PC-05"], [])
    assert solve(limited, 100000, 200)["totals"]["usable_final"] == 1


@pytest.mark.parametrize("interrupted_phase,reported_status,expected_proofs,expected_count", [
    (1, "FEASIBLE", [], 1),
    (1, "UNKNOWN", [], 0),
    (2, "UNKNOWN", ["usable_final"], 1),
])
def test_interrupted_solver_never_claims_unproven_optimality(snapshot, monkeypatch, interrupted_phase, reported_status, expected_proofs, expected_count):
    # Use a real solved candidate, overriding only the externally reported stop
    # status to exercise otherwise timing-dependent cancellation boundaries.
    real_solver_class = optimizer.cp_model.CpSolver

    class InterruptedSolver(real_solver_class):
        calls = 0

        def solve(self, model, *args, **kwargs):
            actual_status = super().solve(model, *args, **kwargs)
            self.calls += 1
            if self.calls == interrupted_phase:
                return getattr(optimizer.cp_model, reported_status)
            return actual_status

    monkeypatch.setattr(optimizer.cp_model, "CpSolver", InterruptedSolver)
    case = restricted(snapshot, ["RG-PC-05"], ["RG-SSD-06"])
    result = solve(case, 29000, 38)
    assert result["solver"]["status"] == ("UNKNOWN" if expected_count == 0 else "FEASIBLE")
    assert result["solver"]["last_attempted_status"] == reported_status
    assert result["solver"]["objectives_proven"] == expected_proofs
    assert not result["solver"]["stable_tie_break_proven"]
    assert result["totals"]["usable_final"] == expected_count
    assert result["solver"]["parameters"]["max_deterministic_time_per_phase"] == 2.0
    assert result["solver"]["termination_reason"] != "all_objectives_proven"


def test_wall_cancellation_during_tie_preserves_only_completed_proofs(snapshot, monkeypatch):
    case = restricted(snapshot, ["RG-PC-05"], ["RG-SSD-06"])
    clock = iter([0, 0, 0, 0, 0, 61, 61])
    monkeypatch.setattr(optimizer, "monotonic", lambda: next(clock))
    result = solve(case, 29000, 38)
    assert result["solver"]["status"] == "FEASIBLE"
    assert result["solver"]["last_attempted_status"] == "OPTIMAL"
    assert result["solver"]["termination_reason"] == "aggregate_wall_time_limit"
    assert result["solver"]["objectives_proven"] == ["usable_final", "cost_paise", "technician_minutes", "transfers"]
    assert not result["solver"]["stable_tie_break_proven"]
    assert result["totals"]["usable_final"] == 1
