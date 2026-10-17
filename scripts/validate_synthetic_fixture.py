"""Preparation-only validator and tiny-case oracle for synthetic-v1.

This script does not implement the production compatibility service or optimizer.
It validates a deliberately small, declared simulation universe using stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "datasets" / "synthetic-v1"
COMPUTER_COLUMNS = ["asset_id", "owner_id", "board_profile_id", "base_health", "provenance"]
COMPONENT_COLUMNS = [
    "component_id", "owner_id", "location_asset_id", "type", "ram_generation",
    "form_factor", "capacity_gib", "capacity_gb", "speed_mt_s", "voltage_mv",
    "ecc", "buffered", "interface", "health", "provenance", "evidence_ref",
]
OPERATIONS = {
    "prepare_target", "remove_ram", "remove_storage", "install_ram",
    "install_storage", "verify_target",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def integer(value: object, label: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, f"{label} must be an integer >= {minimum}")
    return value


def read_csv(path: Path, columns: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == columns, f"{path.name}: CSV columns differ from architecture v1")
        rows = list(reader)
    require(all(None not in row and all(value is not None for value in row.values()) for row in rows),
            f"{path.name}: malformed CSV row")
    return rows


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def unique_by(rows: list[dict], key: str, label: str) -> dict[str, dict]:
    ids = [row[key] for row in rows]
    require(all(ids) and len(ids) == len(set(ids)), f"duplicate/empty {label} IDs")
    return {row[key]: row for row in rows}


def synthetic(value: object, label: str) -> None:
    require(isinstance(value, str) and value.startswith("synthetic:") and len(value) > 10,
            f"{label}: explicit synthetic provenance required")


def profile_known(profile: dict) -> bool:
    decisive = ["ram_generation", "ram_voltage_mv", "udimm_non_ecc_unbuffered",
                "ram_slots", "max_per_slot_gib", "max_total_gib", "approved_speeds_mt_s",
                "allowed_module_counts", "mixed_modules_allowed", "sata_ports",
                "sata_boot_supported", "sata_data_available", "sata_power_available",
                "bays_2_5_inch"]
    return all(profile.get(field) is not None for field in decisive)


def compatible(part: dict, profile: dict) -> bool:
    if not profile_known(profile):
        return False
    if part["type"] == "ram":
        return (
            part["ram_generation"] == profile["ram_generation"]
            and part["form_factor"] == "UDIMM"
            and int(part["voltage_mv"]) == profile["ram_voltage_mv"]
            and part["ecc"] == part["buffered"] == "false"
            and profile["udimm_non_ecc_unbuffered"] is True
            and int(part["capacity_gib"]) <= profile["max_per_slot_gib"]
            and int(part["speed_mt_s"]) in profile["approved_speeds_mt_s"]
        )
    return (
        part["type"] == "storage" and part["form_factor"] == "2.5-inch"
        and part["interface"] == "SATA" and profile["sata_ports"] >= 1
        and profile["sata_boot_supported"] is True
        and profile["sata_data_available"] is True
        and profile["sata_power_available"] is True
        and profile["bays_2_5_inch"] >= 1
    )


def blockers(computer: dict, installed: list[dict], profile: dict) -> list[str]:
    base = computer["base_health"]
    if base != "healthy":
        return [f"base_{base}"]
    if not profile_known(profile):
        return ["board_boot_support_unknown"]
    found = []
    for kind in ("ram", "storage"):
        parts = [part for part in installed if part["type"] == kind]
        if not parts:
            found.append(f"{kind}_missing")
        elif kind == "storage" and len(parts) != 1:
            found.append("storage_layout_invalid")
        elif kind == "ram" and (len(parts) not in profile["allowed_module_counts"] or
                                sum(int(part["capacity_gib"]) for part in parts) > profile["max_total_gib"] or
                                (len(parts) > 1 and not profile["mixed_modules_allowed"] and
                                 len({(part["capacity_gib"], part["speed_mt_s"]) for part in parts}) != 1)):
            found.append("ram_layout_invalid")
        else:
            if kind == "ram" and len(parts) > 1:
                if any(part["health"] != "healthy" for part in parts):
                    found.append("ram_unhealthy")
                elif any(not compatible(part, profile) for part in parts) or sum(int(part["capacity_gib"]) for part in parts) < 8:
                    found.append("ram_ineligible")
                continue
            part = parts[0]
            if part["health"] != "healthy":
                found.append(f"{kind}_{part['health']}:{part['component_id']}")
            elif not compatible(part, profile) or int(part["capacity_gib" if kind == "ram" else "capacity_gb"]) < (8 if kind == "ram" else 240):
                found.append(f"{kind}_ineligible:{part['component_id']}")
    return found


def validate_inventory(folder: Path) -> tuple[dict, dict, dict, dict, dict, dict]:
    manifest = read_json(folder / "manifest.json")
    board_data = read_json(folder / "board_profiles.json")
    costs = read_json(folder / "operation_costs.json")
    scenarios = read_json(folder / "scenarios.json")
    computers = unique_by(read_csv(folder / "computers.csv", COMPUTER_COLUMNS), "asset_id", "computer")
    components = unique_by(read_csv(folder / "components.csv", COMPONENT_COLUMNS), "component_id", "component")
    profiles = unique_by(board_data["profiles"], "id", "board profile")
    require(manifest["fixture_id"] == "revivegraph-synthetic-v1" and manifest["mode"] == "simulation", "wrong fixture identity/mode")
    require(set(manifest["files"]) == {"computers.csv", "components.csv", "board_profiles.json", "operation_costs.json", "scenarios.json"}, "manifest file list mismatch")
    require(len(computers) == manifest["expected_computers"] == 12, "expected exactly 12 computers")
    require(len(components) == manifest["expected_components"], "component count mismatch")
    synthetic(manifest["provenance"], "manifest")
    synthetic(board_data["provenance"], "board profiles")
    synthetic(costs["provenance"], "operation costs")
    synthetic(scenarios["provenance"], "scenarios")
    context = manifest["assessment_record_context"]
    synthetic(context["source"], "assessment source")
    require(context["recorded_date"] == manifest["created_date"] and context["reviewer"] and context["acceptance_scope"].startswith("simulation-only"), "assessment context incomplete")
    require(scenarios["mode"] == "simulation", "scenarios must be simulation only")
    require(costs["currency"] == "INR" and costs["cost_unit"] == "paise" and costs["time_unit"] == "technician_minutes", "cost units mismatch")
    require(set(costs["operations"]) == OPERATIONS, "operation list mismatch")
    for op, values in costs["operations"].items():
        integer(values["cost_paise"], f"{op}.cost_paise")
        integer(values["technician_minutes"], f"{op}.technician_minutes")
    for profile in profiles.values():
        integer(profile["version"], f"{profile['id']} version", 1)
        synthetic(profile["provenance"], profile["id"])
        require(profile["evidence_ref"].startswith("SYN-V1-"), "board evidence ref missing")
        require(profile["ram_generation"] in {"DDR3", "DDR4"}, "unsupported board RAM generation")
        require(profile["ram_voltage_mv"] == (1500 if profile["ram_generation"] == "DDR3" else 1200), "board RAM voltage mismatch")
        for field in ("ram_slots", "max_per_slot_gib", "max_total_gib", "sata_ports", "bays_2_5_inch"):
            integer(profile[field], f"{profile['id']}.{field}", 1)
        require(profile["max_total_gib"] <= profile["ram_slots"] * profile["max_per_slot_gib"], "board RAM maximum inconsistent")
        require(profile["udimm_non_ecc_unbuffered"] is True and profile["mixed_modules_allowed"] is False, "unsupported board RAM layout")
        require(profile["allowed_module_counts"] and all(type(n) is int and 1 <= n <= profile["ram_slots"] for n in profile["allowed_module_counts"]), "invalid module counts")
        require(profile["approved_speeds_mt_s"] and all(type(n) is int and n > 0 for n in profile["approved_speeds_mt_s"]), "invalid board speeds")
        require(profile["sata_boot_supported"] in {True, False, None}, "invalid SATA boot support")
        require(profile["sata_data_available"] is True and profile["sata_power_available"] is True, "toy boards need stated SATA connections")
    for computer in computers.values():
        require(computer["owner_id"] == manifest["owner_id"], "computer owner mismatch")
        require(computer["board_profile_id"] in profiles, "computer board reference missing")
        require(computer["base_health"] in {"healthy", "faulty", "unknown"}, "invalid base health")
        synthetic(computer["provenance"], computer["asset_id"])
    evidence_refs = []
    for part in components.values():
        require(part["owner_id"] == manifest["owner_id"], "component owner mismatch")
        require(not part["location_asset_id"] or part["location_asset_id"] in computers, "component location reference missing")
        require(part["type"] in {"ram", "storage"}, "unsupported component type")
        require(part["health"] in {"healthy", "faulty", "unknown"}, "invalid component health")
        synthetic(part["provenance"], part["component_id"])
        require(part["evidence_ref"].startswith("SYN-V1-"), "component evidence ref missing")
        evidence_refs.append(part["evidence_ref"])
        if part["type"] == "ram":
            require(part["component_id"].startswith("RG-RAM-") and part["ram_generation"] in {"DDR3", "DDR4"}, "invalid RAM identity/generation")
            require(part["form_factor"] == "UDIMM" and part["ecc"] == part["buffered"] == "false", "unsupported RAM form")
            require(part["interface"] == part["capacity_gb"] == "", "RAM type-inapplicable fields must be empty")
            require(int(part["capacity_gib"]) > 0 and int(part["speed_mt_s"]) > 0, "invalid RAM capacity/speed")
            require(int(part["voltage_mv"]) == (1500 if part["ram_generation"] == "DDR3" else 1200), "RAM voltage mismatch")
        else:
            require(part["component_id"].startswith("RG-SSD-") and part["form_factor"] == "2.5-inch" and part["interface"] == "SATA", "unsupported storage")
            require(int(part["capacity_gb"]) > 0, "invalid storage capacity")
            require(all(part[field] == "" for field in ("ram_generation", "capacity_gib", "speed_mt_s", "voltage_mv", "ecc", "buffered")), "storage type-inapplicable fields must be empty")
        if part["location_asset_id"]:
            profile = profiles[computers[part["location_asset_id"]]["board_profile_id"]]
            # Installed hardware may be faulty/unknown, but its asserted physical form must fit known fields.
            if part["type"] == "ram":
                require(part["ram_generation"] == profile["ram_generation"] and int(part["voltage_mv"]) == profile["ram_voltage_mv"], "installed RAM contradicts board")
                require(int(part["speed_mt_s"]) in profile["approved_speeds_mt_s"], "installed RAM speed contradicts board")
    require(len(evidence_refs) == len(set(evidence_refs)), "duplicate component evidence reference")
    for asset_id, computer in computers.items():
        installed = [p for p in components.values() if p["location_asset_id"] == asset_id]
        profile = profiles[computer["board_profile_id"]]
        require(sum(p["type"] == "ram" for p in installed) <= profile["ram_slots"], "installed RAM exceeds slots")
        require(sum(p["type"] == "storage" for p in installed) <= profile["bays_2_5_inch"], "installed storage exceeds bays")
        installed_ram = [p for p in installed if p["type"] == "ram"]
        if installed_ram:
            require(len(installed_ram) in profile["allowed_module_counts"], "installed RAM module count disallowed")
            require(all(int(p["capacity_gib"]) <= profile["max_per_slot_gib"] for p in installed_ram), "installed RAM exceeds per-slot limit")
            require(sum(int(p["capacity_gib"]) for p in installed_ram) <= profile["max_total_gib"], "installed RAM exceeds total limit")
            require(profile["mixed_modules_allowed"] or len({(p["capacity_gib"], p["speed_mt_s"]) for p in installed_ram}) == 1, "installed mixed RAM disallowed")
        actual = blockers(computer, installed, profile)
        require(actual == manifest["initial_state"].get(asset_id), f"{asset_id}: blocker annotation differs: {actual}")
        require(actual, f"{asset_id}: already usable computer cannot count as recovered")
    require(set(manifest["initial_state"]) == set(computers), "initial state references mismatch")
    known = sum(any("faulty" in reason or "missing" in reason for reason in reasons) for reasons in manifest["initial_state"].values())
    unknown = len(computers) - known
    require(manifest["initial_usable_count"] == 0 and manifest["initial_unusable_count"] == known == 8 and
            manifest["initial_unknown_count"] == unknown == 4 and
            manifest["initial_not_certifiably_usable_count"] == len(computers), "initial usability count mismatch")
    return manifest, computers, components, profiles, costs["operations"], scenarios


def evaluate_plan(allocations: list[dict], computers: dict, components: dict, profiles: dict,
                  costs: dict, budget: int, minutes: int, failed: str | None = None) -> tuple[Counter, int, int]:
    used: set[str] = set()
    targets: set[str] = set()
    removed: set[str] = set()
    installed: set[str] = set()
    for allocation in allocations:
        target = allocation["target_asset_id"]
        require(target in computers and target not in targets, "duplicate/missing plan target")
        targets.add(target)
        computer = computers[target]
        profile = profiles[computer["board_profile_id"]]
        require(computer["base_health"] == "healthy" and profile_known(profile), "target base/profile ineligible")
        ram_ids = allocation["ram_component_ids"]
        final_ids = ram_ids + [allocation["storage_component_id"]]
        require(len(ram_ids) in profile["allowed_module_counts"] and len(final_ids) == len(set(final_ids)), "invalid final component layout")
        require(all(component_id in components for component_id in final_ids), "missing allocated part")
        require(all(component_id not in used for component_id in final_ids), "physical component allocated twice")
        used.update(final_ids)
        ram = [components[part_id] for part_id in ram_ids]
        storage = components[allocation["storage_component_id"]]
        require(all(p["type"] == "ram" for p in ram) and storage["type"] == "storage", "wrong part type in configuration")
        require(sum(int(p["capacity_gib"]) for p in ram) >= 8 and sum(int(p["capacity_gib"]) for p in ram) <= profile["max_total_gib"], "RAM target capacity invalid")
        require(len(ram) == 1 or (profile["mixed_modules_allowed"] or len({(p["capacity_gib"], p["speed_mt_s"]) for p in ram}) == 1), "mixed RAM modules unsupported")
        require(int(storage["capacity_gb"]) >= 240, "storage below 240 GB policy")
        for part in ram + [storage]:
            require(part["owner_id"] == computer["owner_id"], "cross-owner transfer")
            require(part["health"] == "healthy" and part["component_id"] != failed, "faulty/unknown/failed part allocated")
            require(compatible(part, profile), "incompatible or unknown board/part combination")
            if part["location_asset_id"] != target:
                installed.add(part["component_id"])
                if part["location_asset_id"]:
                    removed.add(part["component_id"])
        for part in components.values():
            if part["location_asset_id"] == target and part["component_id"] not in final_ids:
                removed.add(part["component_id"])
    counts = Counter({"prepare_target": len(targets), "verify_target": len(targets)})
    for part_id in removed:
        counts[f"remove_{components[part_id]['type']}"] += 1
    for part_id in installed:
        counts[f"install_{components[part_id]['type']}"] += 1
    for op in OPERATIONS:
        counts.setdefault(op, 0)
    total_cost = sum(counts[op] * costs[op]["cost_paise"] for op in OPERATIONS)
    total_minutes = sum(counts[op] * costs[op]["technician_minutes"] for op in OPERATIONS)
    require(total_cost <= budget and total_minutes <= minutes, "plan exceeds budget or technician minutes")
    return counts, total_cost, total_minutes


def tiny_options(target: str, pool: list[str], computers: dict, components: dict, profiles: dict) -> list[dict]:
    computer = computers[target]
    profile = profiles[computer["board_profile_id"]]
    if computer["base_health"] != "healthy" or not profile_known(profile):
        return []
    own = [p["component_id"] for p in components.values() if p["location_asset_id"] == target and p["health"] == "healthy"]
    choices = [components[p] for p in dict.fromkeys(own + pool) if components[p]["health"] == "healthy" and compatible(components[p], profile)]
    ram = [p for p in choices if p["type"] == "ram" and int(p["capacity_gib"]) >= 8]
    storage = [p for p in choices if p["type"] == "storage" and int(p["capacity_gb"]) >= 240]
    return [{"target_asset_id": target, "ram_component_ids": [r["component_id"]], "storage_component_id": s["component_id"]}
            for r in ram for s in storage]


def tiny_oracle(case: dict, computers: dict, components: dict, profiles: dict, costs: dict) -> tuple[int, int | None]:
    targets = case["target_asset_ids"]
    pool = case["candidate_component_ids"]
    require(len(targets) == len(set(targets)) and all(t in computers for t in targets), "tiny case target reference invalid")
    require(len(pool) == len(set(pool)) and all(p in components for p in pool), "tiny case part reference invalid")
    budget = integer(case["budget_paise"], "tiny budget")
    minutes = integer(case["technician_minutes"], "tiny minutes")
    options = [tiny_options(t, pool, computers, components, profiles) for t in targets]
    best = 0
    # Restricted one-RAM/one-storage exhaustive enumeration is a preparation oracle only.
    for selection in itertools.product(*[[None] + items for items in options]):
        allocations = [item for item in selection if item is not None]
        try:
            evaluate_plan(allocations, computers, components, profiles, costs, budget, minutes)
        except ValueError:
            continue
        best = max(best, len(allocations))
    greedy = None
    if "expected_greedy_recoveries" in case:
        chosen: list[dict] = []
        for target, items in sorted(zip(targets, options)):
            feasible = []
            for item in items:
                try:
                    _, cost, time = evaluate_plan(chosen + [item], computers, components, profiles, costs, budget, minutes)
                    ids = item["ram_component_ids"] + [item["storage_component_id"]]
                    transfers = sum(components[part_id]["location_asset_id"] != target for part_id in ids)
                    feasible.append((cost, time, transfers, ids, item))
                except ValueError:
                    pass
            if feasible:
                chosen.append(min(feasible, key=lambda x: (x[0], x[1], x[2], x[3]))[4])
        greedy = len(chosen)
    return best, greedy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    manifest, computers, components, profiles, costs, scenarios = validate_inventory(args.fixture)
    fleet = scenarios["main_fleet"]
    budget = integer(fleet["budget_paise"], "fleet budget")
    minutes = integer(fleet["technician_minutes"], "fleet technician minutes")
    failure = fleet["donor_failure"]
    failed = failure["component_id"]
    require(failed in components and failure["new_health"] == "faulty" and components[failed]["health"] == "healthy", "invalid donor failure")
    results = []
    for key, excluded in (("before_failure", None), ("after_failure", failed)):
        example = fleet[key]
        counts, cash, time = evaluate_plan(example["allocations"], computers, components, profiles, costs, budget, minutes, excluded)
        require(dict(counts) == example["expected_operation_counts"], f"{key}: operation counts differ")
        require((cash, time) == (example["expected_total_cost_paise"], example["expected_total_technician_minutes"]), f"{key}: resource totals differ")
        results.append((key, len(example["allocations"]), cash, time))
    require(any(failed in a["ram_component_ids"] and components[failed]["location_asset_id"] not in ("", a["target_asset_id"])
                for a in fleet["before_failure"]["allocations"]), "failed donor not transferred in before plan")
    require(all(failed not in a["ram_component_ids"] for a in fleet["after_failure"]["allocations"]), "failed donor retained after failure")
    ids = [case["id"] for case in scenarios["small_cases"]]
    require(len(ids) == len(set(ids)), "duplicate small-case ID")
    for case in scenarios["small_cases"]:
        best, greedy = tiny_oracle(case, computers, components, profiles, costs)
        require(best == case["expected_max_recoveries"], f"{case['id']}: expected max {case['expected_max_recoveries']}, enumerated {best}")
        if greedy is not None:
            require(greedy == case["expected_greedy_recoveries"], f"{case['id']}: greedy expectation differs")
        print(f"tiny {case['id']}: max={best}" + (f", greedy={greedy}" if greedy is not None else ""))
    print(f"PASS {manifest['fixture_id']}: {len(computers)} computers (0 usable, 8 known unusable, 4 uncertain), {len(components)} physical components")
    for name, count, cash, time in results:
        print(f"{name}: {count} feasible recovered candidates, {cash} paise (INR {cash / 100:.2f}), {time} technician minutes")
    print("Preparation oracle only; no production optimizer or main-fleet optimum claim.")


if __name__ == "__main__":
    main()
