"""Versioned JSON boundary shared by local and remote CPU execution."""
import hashlib
import json

from .domain import RULE_VERSION
from .optimizer import ENGINE_VERSION, VALIDATOR_VERSION, greedy_baseline, validate_output

PROTOCOL = "revivegraph-cpu-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def request(snapshot, budget_paise, time_minutes, source_hash):
    if snapshot.get("mode") != "simulation":
        raise ValueError("Remote execution currently accepts synthetic simulation snapshots only.")
    for value in (budget_paise, time_minutes):
        if type(value) is not int or not 0 <= value <= 10**12:
            raise ValueError("Resource limits must be nonnegative integers.")
    return {"protocol": PROTOCOL, "engine_version": ENGINE_VERSION, "rule_version": RULE_VERSION,
            "validator_version": VALIDATOR_VERSION, "source_hash": source_hash,
            "snapshot": snapshot, "budget_paise": budget_paise, "time_minutes": time_minutes}


def accept(payload, response):
    """Reconstruct allocations, operations, totals and baseline on this laptop.

    Remote solver proof metadata is reported by the worker, not independently
    re-proven here. Feasibility and accounting are independently checked here.
    """
    if response["protocol"] != PROTOCOL or response["input_hash"] != digest(payload):
        raise ValueError("Remote response protocol or input hash mismatch.")
    if response["source_hash"] != payload["source_hash"]:
        raise ValueError("Remote source hash mismatch.")
    result = response["result"]
    if response["output_hash"] != digest(result):
        raise ValueError("Remote output hash mismatch.")
    solver = result["solver"]
    if (solver["status"] not in ("OPTIMAL", "FEASIBLE") or solver["engine_version"] != ENGINE_VERSION
            or solver["inspection_rule_version"] != RULE_VERSION or solver["ortools_version"] != "9.15.6755"):
        raise ValueError("Remote solver status or pinned version is unsupported.")
    checked = validate_output(payload["snapshot"], result["allocations"], payload["budget_paise"], payload["time_minutes"])
    if any(digest(checked[k]) != digest(result[k]) for k in ("totals", "operations", "validator_version", "valid")):
        raise ValueError("Remote allocation accounting differs from independent validation.")
    baseline = greedy_baseline(payload["snapshot"], payload["budget_paise"], payload["time_minutes"])
    if digest(baseline) != digest(result["baseline"]):
        raise ValueError("Remote greedy baseline differs from local reconstruction.")
    return result
