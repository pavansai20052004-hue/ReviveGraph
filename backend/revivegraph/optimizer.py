"""Production configuration allocation, independent output checks and a greedy comparator.

This module never reads scenario examples or the preparation oracle. Inputs are an
immutable imported-inventory snapshot with its registered costs and inspection rules.
"""

from itertools import combinations
from time import monotonic

import ortools
from ortools.sat.python import cp_model

from .domain import RULE_VERSION, eligibility, part_compatibility, ram_configuration, usability

ENGINE_VERSION = "configuration-cpsat-v1"
VALIDATOR_VERSION = "allocation-validator-v1"
BASELINE_VERSION = "asset-id-greedy-v1"
MAX_CONFIGURATIONS = 25_000
MAX_RAM_COMBINATIONS = 100_000
MAX_PHASE_DETERMINISTIC_TIME = 2.0
MAX_PHASE_WALL_SECONDS = 10.0
MAX_SOLVE_WALL_SECONDS = 60.0


def _nonnegative(value, name):
    if type(value) is not int or value < 0 or value > 10**12:
        raise ValueError(f"{name} must be a nonnegative integer at most 10^12.")


def _context(snapshot):
    computers = {c["asset_id"]: c for c in snapshot["computers"]}
    parts = {p["component_id"]: p for p in snapshot["components"]}
    if len(computers) != len(snapshot["computers"]) or len(parts) != len(snapshot["components"]):
        raise ValueError("Duplicate physical or asset IDs in snapshot.")
    if snapshot.get("mode") not in ("simulation", "physical"):
        raise ValueError("Explicit simulation/physical mode is required.")
    failed = set(snapshot.get("failed_component_ids", []))
    if not failed <= parts.keys():
        raise ValueError("Scenario failure references a missing physical component.")
    for p in parts.values():
        if p.get("location_asset_id") and p["location_asset_id"] not in computers:
            raise ValueError("Component location refers to a missing computer.")
    costs = snapshot["operation_costs"]["operations"]
    for op in ("prepare_target", "verify_target", "remove_ram", "remove_storage", "install_ram", "install_storage"):
        for field in ("cost_paise", "technician_minutes"):
            _nonnegative(costs[op][field], f"{op}.{field}")
    return computers, parts, failed, costs


def _base_eligible(target, mode):
    assessment = target.get("assessment", {})
    if target.get("base_health") != "healthy":
        return False
    if assessment.get("assessment_kind") not in ("authored_synthetic_assertion", "human_reviewed_physical_assessment"):
        return False
    if mode == "physical":
        # Registered v1 board declarations are explicitly toy synthetic profiles.
        if target["profile"].get("provenance", "").startswith("synthetic:"):
            return False
        if assessment.get("assessment_kind") != "human_reviewed_physical_assessment":
            return False
    return True


def _part_eligible(part, target, snapshot, failed):
    if part["component_id"] in failed:
        return False
    assessment = part.get("assessment")
    if not assessment or assessment.get("assessment_kind") not in ("authored_synthetic_assertion", "human_reviewed_physical_assessment"):
        return False
    hardware = part_compatibility(part, target["profile"])
    return eligibility(part, target, snapshot["mode"], hardware, assessment,
                       reserved=part.get("reserved", False))["eligible"]


def _ids(allocation):
    return allocation["ram_component_ids"] + [allocation["storage_component_id"]]


def _key(allocation):
    return (allocation["target_asset_id"], tuple(allocation["ram_component_ids"]), allocation["storage_component_id"])


def generate_configurations(snapshot):
    """Enumerate complete supported configurations, fail closed on excessive size."""
    computers, parts, failed, _ = _context(snapshot)
    candidates, examined_ram_sets = [], 0
    for asset_id, target in sorted(computers.items()):
        if not _base_eligible(target, snapshot["mode"]):
            continue
        eligible = [p for _, p in sorted(parts.items()) if _part_eligible(p, target, snapshot, failed)]
        ram = [p for p in eligible if p["type"] == "ram"]
        storage = [p for p in eligible if p["type"] == "storage"]
        profile = target["profile"]
        counts = profile.get("allowed_module_counts")
        if counts is None or profile.get("ram_slots") is None:
            continue
        for count in sorted(counts):
            if count > min(profile["ram_slots"], len(ram)):
                continue
            for modules in combinations(ram, count):
                examined_ram_sets += 1
                if examined_ram_sets > MAX_RAM_COMBINATIONS:
                    raise ValueError("RAM combination limit exceeded; narrow the fleet before solving.")
                if ram_configuration(modules, profile)["decision"] != "compatible":
                    continue
                # A surplus incoming module can never improve any objective if
                # removing it leaves a complete supported RAM set. Retained
                # modules are not pruned: removing one would incur real work.
                if any(p.get("location_asset_id") != asset_id
                       and ram_configuration([q for q in modules if q is not p], profile)["decision"] == "compatible"
                       for p in modules):
                    continue
                for drive in storage:
                    candidates.append({"target_asset_id": asset_id,
                                       "ram_component_ids": [p["component_id"] for p in modules],
                                       "storage_component_id": drive["component_id"]})
                    if len(candidates) > MAX_CONFIGURATIONS:
                        raise ValueError("Configuration limit exceeded; narrow the fleet before solving.")
    return sorted(candidates, key=_key)


def _initial_usable(target, parts, snapshot, failed):
    installed = [p for p in parts.values() if p.get("location_asset_id") == target["asset_id"]]
    return (_base_eligible(target, snapshot["mode"])
            and all(_part_eligible(p, target, snapshot, set()) for p in installed)
            and usability(target, installed, target["profile"])["classification"] == "usable")


def _changed(allocation, target, parts, snapshot, failed):
    installed = {p["component_id"] for p in parts.values() if p.get("location_asset_id") == target["asset_id"]}
    return set(_ids(allocation)) != installed or not _initial_usable(target, parts, snapshot, failed)


def validate_output(snapshot, allocations, budget_paise, time_minutes):
    """Check selected IDs directly against rules; independently recompute global work.

    This checker does not trust CP variables, generated candidates, reported totals,
    or a solver status. It is suitable for validating persisted plans again later.
    """
    _nonnegative(budget_paise, "budget_paise")
    _nonnegative(time_minutes, "time_minutes")
    computers, parts, failed, costs = _context(snapshot)
    if not isinstance(allocations, list):
        raise ValueError("Allocations must be a list.")
    selected, used = {}, {}
    for allocation in allocations:
        if set(allocation) != {"target_asset_id", "ram_component_ids", "storage_component_id"}:
            raise ValueError("Allocation fields do not match the versioned contract.")
        asset_id = allocation["target_asset_id"]
        if not isinstance(asset_id, str):
            raise ValueError("Target IDs must be strings.")
        if asset_id not in computers or asset_id in selected:
            raise ValueError("Missing or duplicate target.")
        target = computers[asset_id]
        if not _base_eligible(target, snapshot["mode"]):
            raise ValueError("Target base is ineligible.")
        if not isinstance(allocation["ram_component_ids"], list) or not allocation["ram_component_ids"]:
            raise ValueError("A complete RAM set is required.")
        ids = _ids(allocation)
        for part_id in ids:
            if not isinstance(part_id, str):
                raise ValueError("Physical component IDs must be strings.")
            if part_id not in parts or part_id in used:
                raise ValueError("Missing part or physical component allocated twice.")
            if not _part_eligible(parts[part_id], target, snapshot, failed):
                raise ValueError(f"Ineligible component {part_id}.")
            used[part_id] = asset_id
        modules = [parts[p] for p in allocation["ram_component_ids"]]
        if any(p["type"] != "ram" for p in modules) or parts[allocation["storage_component_id"]]["type"] != "storage":
            raise ValueError("Wrong component type in configuration.")
        if ram_configuration(modules, target["profile"])["decision"] != "compatible":
            raise ValueError("Unsupported complete RAM configuration.")
        selected[asset_id] = allocation

    operations = []

    def add(operation, asset_id, component_id=None, target_asset_id=None):
        operations.append({"operation": operation, "asset_id": asset_id,
                           "component_id": component_id, "target_asset_id": target_asset_id,
                           **costs[operation]})

    for asset_id, allocation in sorted(selected.items()):
        if _changed(allocation, computers[asset_id], parts, snapshot, failed):
            add("prepare_target", asset_id)
    # One global removal per installed part: displacement and donor extraction
    # are the same physical operation, even when both apply to that part.
    for part_id, part in sorted(parts.items()):
        origin = part.get("location_asset_id")
        destination = used.get(part_id)
        removed = origin and ((destination is not None and destination != origin)
                              or (origin in selected and destination != origin))
        if removed:
            add("remove_" + part["type"], origin, part_id, destination)
    transfers = 0
    for asset_id, allocation in sorted(selected.items()):
        for part_id in _ids(allocation):
            part = parts[part_id]
            if part.get("location_asset_id") != asset_id:
                add("install_" + part["type"], asset_id, part_id, asset_id)
                transfers += 1
        if _changed(allocation, computers[asset_id], parts, snapshot, failed):
            add("verify_target", asset_id)
    totals = {"cost_paise": sum(o["cost_paise"] for o in operations),
              "technician_minutes": sum(o["technician_minutes"] for o in operations),
              "transfers": transfers, "usable_final": len(selected),
              "newly_recovered": sum(not _initial_usable(computers[a], parts, snapshot, failed) for a in selected)}
    if totals["cost_paise"] > budget_paise or totals["technician_minutes"] > time_minutes:
        raise ValueError("Allocation exceeds budget or technician effort.")
    return {"operations": operations, "totals": totals, "validator_version": VALIDATOR_VERSION, "valid": True}


def greedy_baseline(snapshot, budget_paise, time_minutes):
    """Visit target IDs ascending; keep the cheapest feasible incremental choice.

    Equal costs break by total time then sorted RAM IDs/storage ID. Earlier choices
    are never revisited. All checks use the same snapshot and global work accounting.
    """
    configurations = generate_configurations(snapshot)
    selected = []
    for asset_id in sorted({c["target_asset_id"] for c in configurations}):
        choices = []
        for candidate in configurations:
            if candidate["target_asset_id"] != asset_id:
                continue
            try:
                checked = validate_output(snapshot, selected + [candidate], budget_paise, time_minutes)
            except ValueError:
                continue
            choices.append((checked["totals"]["cost_paise"], checked["totals"]["technician_minutes"], _key(candidate), candidate))
        if choices:
            selected.append(min(choices, key=lambda c: c[:3])[3])
    return {"version": BASELINE_VERSION, "allocations": selected,
            **validate_output(snapshot, selected, budget_paise, time_minutes)}


def solve(snapshot, budget_paise, time_minutes):
    """Lexicographic CP-SAT solve; optimal claims require every prior phase proven."""
    _nonnegative(budget_paise, "budget_paise")
    _nonnegative(time_minutes, "time_minutes")
    computers, parts, failed, costs = _context(snapshot)
    configurations = generate_configurations(snapshot)
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"configuration_{i}") for i in range(len(configurations))]
    by_target = {a: [i for i, c in enumerate(configurations) if c["target_asset_id"] == a] for a in computers}
    by_part = {p: [i for i, c in enumerate(configurations) if p in _ids(c)] for p in parts}
    for indices in by_target.values():
        model.add(sum(variables[i] for i in indices) <= 1)
    for indices in by_part.values():
        model.add(sum(variables[i] for i in indices) <= 1)
    cash_terms, time_terms, transfer_terms = [], [], []
    for i, config in enumerate(configurations):
        cash = effort = transfers = 0
        asset_id = config["target_asset_id"]
        if _changed(config, computers[asset_id], parts, snapshot, failed):
            for op in ("prepare_target", "verify_target"):
                cash += costs[op]["cost_paise"]
                effort += costs[op]["technician_minutes"]
        for part_id in _ids(config):
            part = parts[part_id]
            if part.get("location_asset_id") != asset_id:
                op = costs["install_" + part["type"]]
                cash += op["cost_paise"]
                effort += op["technician_minutes"]
                transfers += 1
        cash_terms.append(cash * variables[i])
        time_terms.append(effort * variables[i])
        transfer_terms.append(transfers * variables[i])
    for part_id, part in parts.items():
        origin = part.get("location_asset_id")
        if not origin:
            continue
        retained = sum(variables[i] for i in by_part[part_id] if configurations[i]["target_asset_id"] == origin)
        displaced = sum(variables[i] for i in by_target[origin]) - retained
        moved = sum(variables[i] for i in by_part[part_id] if configurations[i]["target_asset_id"] != origin)
        removed = model.new_bool_var("remove_" + part_id)
        model.add(removed >= displaced)
        model.add(removed >= moved)
        model.add(removed <= displaced + moved)
        op = costs["remove_" + part["type"]]
        cash_terms.append(op["cost_paise"] * removed)
        time_terms.append(op["technician_minutes"] * removed)
    final_count, cash, effort, transfers = sum(variables), sum(cash_terms), sum(time_terms), sum(transfer_terms)
    model.add(cash <= budget_paise)
    model.add(effort <= time_minutes)
    phases = [("usable_final", final_count, True), ("cost_paise", cash, False),
              ("technician_minutes", effort, False), ("transfers", transfers, False)]
    # An exact lexicographic target/configuration rank, rather than a sum of ranks
    # that can collide. Missing target sorts after any selected configuration.
    for asset_id, indices in sorted(by_target.items()):
        if indices:
            rank = len(indices) + sum((rank - len(indices)) * variables[i] for rank, i in enumerate(indices))
            phases.append(("tie:" + asset_id, rank, False))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    solver.parameters.max_deterministic_time = MAX_PHASE_DETERMINISTIC_TIME
    started = monotonic()
    proven, phase_results, best_allocations, predicted = [], [], None, None
    last_status = "UNKNOWN"
    last_attempted_status, termination_reason = None, "all_objectives_proven"
    for name, expression, maximize in phases:
        remaining = MAX_SOLVE_WALL_SECONDS - (monotonic() - started)
        if remaining <= 0:
            last_status = "FEASIBLE" if best_allocations is not None else "UNKNOWN"
            termination_reason = "aggregate_wall_time_limit"
            break
        solver.parameters.max_time_in_seconds = min(MAX_PHASE_WALL_SECONDS, remaining)
        (model.maximize if maximize else model.minimize)(expression)
        status = solver.solve(model)
        last_status = solver.status_name(status)
        last_attempted_status = last_status
        deterministic_time = solver.response_proto.deterministic_time
        phase_results.append({"objective": name, "status": last_status,
                              "value": int(round(solver.objective_value)) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
                              "best_bound": solver.best_objective_bound,
                              "deterministic_time": deterministic_time,
                              "wall_time_seconds": solver.wall_time,
                              "wall_time_limit_seconds": solver.parameters.max_time_in_seconds})
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            termination_reason = {cp_model.INFEASIBLE: "infeasible", cp_model.MODEL_INVALID: "model_invalid"}.get(status, "no_solution_before_limit")
            if best_allocations is not None:
                last_status = "FEASIBLE"
            break
        best_allocations = [c for c, v in zip(configurations, variables) if solver.value(v)]
        predicted = {"usable_final": int(solver.value(final_count)), "cost_paise": int(solver.value(cash)),
                     "technician_minutes": int(solver.value(effort)), "transfers": int(solver.value(transfers))}
        if status != cp_model.OPTIMAL:
            termination_reason = ("deterministic_search_limit" if deterministic_time >= MAX_PHASE_DETERMINISTIC_TIME
                                  else "phase_wall_time_limit" if solver.wall_time >= solver.parameters.max_time_in_seconds
                                  else "phase_objective_not_proven")
            break
        proven.append(name)
        model.add(expression == int(round(solver.objective_value)))
    allocations = best_allocations if best_allocations is not None else []
    checked = validate_output(snapshot, allocations, budget_paise, time_minutes)
    if predicted is not None and any(checked["totals"][name] != value for name, value in predicted.items()):
        raise ValueError("Solver accounting does not match independent output validation.")
    return {"allocations": allocations, **checked,
            "solver": {"status": last_status, "objectives_proven": proven,
                       "last_attempted_status": last_attempted_status,
                       "termination_reason": termination_reason,
                       "stable_tie_break_proven": len(proven) == len(phases),
                       "phases": phase_results, "engine_version": ENGINE_VERSION,
                       "inspection_rule_version": RULE_VERSION, "ortools_version": ortools.__version__,
                       "candidate_count": len(configurations), "elapsed_seconds": round(monotonic() - started, 6),
                       "time_limit_seconds": MAX_SOLVE_WALL_SECONDS,
                       "parameters": {"num_search_workers": 1, "random_seed": 0,
                                      "max_deterministic_time_per_phase": MAX_PHASE_DETERMINISTIC_TIME,
                                      "max_wall_time_seconds_per_phase": MAX_PHASE_WALL_SECONDS,
                                      "max_aggregate_wall_time_seconds": MAX_SOLVE_WALL_SECONDS}},
            "baseline": greedy_baseline(snapshot, budget_paise, time_minutes)}
