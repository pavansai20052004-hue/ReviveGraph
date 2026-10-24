"""Deterministic recovery stages shared by local execution and Render tasks.

This local runner is explicitly not a hosted Render run. No stage can approve,
reserve, create work, alter physical evidence or record verification.
"""
import copy
from datetime import datetime, timezone
import uuid

from .domain import RULE_VERSION
from .execution_protocol import accept, canonical, digest, request
from .optimizer import ENGINE_VERSION, generate_configurations, validate_output

VERSION = "recovery-workflow-v1"
STAGES = ("validate_input", "execute", "validate_result", "generate_audit")
MAX_INPUT_BYTES = 4 * 1024 * 1024


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_request(snapshot, budget, minutes, provider="local", run_key=None):
    if provider not in ("local", "nodus"):
        raise ValueError("Workflow execution must be local or nodus.")
    payload = request(snapshot, budget, minutes, "workflow-validation-v1")
    return {"protocol": VERSION, "payload": payload, "provider": provider,
            "run_key": run_key, "run_id": uuid.uuid4().hex}


def _step(state, name, operation):
    completed = len(state.get("stages", []))
    if completed >= len(STAGES) or name != STAGES[completed]:
        raise ValueError("Workflow stage order is invalid.")
    data = copy.deepcopy(state)
    started = timestamp()
    before = digest(data)
    data = operation(data)
    data.setdefault("stages", []).append({"stage": name, "status": "passed", "started_at": started,
                                         "finished_at": timestamp(), "input_hash": before,
                                         "output_hash": digest(data)})
    return data


def validate_input(value):
    def validate(data):
        if data.get("protocol") != VERSION or data.get("provider") not in ("local", "nodus"):
            raise ValueError("Unsupported workflow request.")
        if len(canonical(data).encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError("Workflow input exceeds 4 MiB.")
        payload = data["payload"]
        source = payload["snapshot"]
        if request(source, payload["budget_paise"], payload["time_minutes"], payload["source_hash"]) != payload:
            raise ValueError("Workflow input contract mismatch.")
        if source.get("engine_version", ENGINE_VERSION) != ENGINE_VERSION or source.get("inspection_rule_version", RULE_VERSION) != RULE_VERSION:
            raise ValueError("Workflow inputs reference unsupported rule or engine versions.")
        if not isinstance(source.get("computers"), list) or not isinstance(source.get("components"), list):
            raise ValueError("Workflow requires computer and component arrays.")
        if len(source["computers"]) > 1000 or len(source["components"]) > 1000:
            raise ValueError("Workflow fleet exceeds the supported import boundary.")
        validate_output(source, [], payload["budget_paise"], payload["time_minutes"])
        # Enumerating bounded, deterministic configurations catches profile,
        # evidence and compatibility errors before a paid execution is requested.
        data["candidate_count"] = len(generate_configurations(source))
        data["request_hash"] = digest(payload)
        return data
    return _step(value, "validate_input", validate)


def execute_plan(value, executor=None):
    def execute(data):
        if digest(data["payload"]) != data["request_hash"]:
            raise ValueError("Workflow input changed after validation.")
        if executor is None:
            from .execution import execute as adapter
        else:
            adapter = executor
        payload = data["payload"]
        result, evidence = adapter(copy.deepcopy(payload["snapshot"]), payload["budget_paise"], payload["time_minutes"],
                                   data["provider"], run_key=data.get("run_key"))
        if evidence.get("provider") != data["provider"]:
            raise ValueError("Execution provider differs from the requested provider; fallback is forbidden.")
        data["result"], data["execution"] = result, evidence
        return data
    return _step(value, "execute", execute)


def validate_result(value):
    def validate(data):
        payload = data["payload"]
        if digest(payload) != data["request_hash"]:
            raise ValueError("Workflow input changed while executing.")
        result = data["result"]
        response = {"protocol": payload["protocol"], "input_hash": digest(payload),
                    "source_hash": payload["source_hash"], "output_hash": digest(result), "result": result}
        accept(payload, response)
        data["result_hash"] = digest(result)
        return data
    return _step(value, "validate_result", validate)


def generate_audit(value):
    def generate(data):
        if digest(data["result"]) != data["result_hash"] or digest(data["payload"]) != data["request_hash"]:
            raise ValueError("Validated workflow inputs or result changed before audit generation.")
        data["artifact"] = {"report_version": "workflow-execution-audit-v1", "run_id": data["run_id"],
            "generated_at": timestamp(), "request_hash": data["request_hash"], "result_hash": data["result_hash"],
            "snapshot_hash": digest(data["payload"]["snapshot"]), "provider": data["provider"],
            "job_id": data["execution"].get("job_id"), "solver_status": data["result"]["solver"]["status"],
            "totals": copy.deepcopy(data["result"]["totals"]), "physical_repairs": 0,
            "human_approval": False, "simulation_only": True,
            "disclaimer": "Computed synthetic plan. This workflow does not approve work or verify physical repairs."}
        return data
    return _step(value, "generate_audit", generate)


def finish(value, orchestrator="local-pipeline", task_run_id=None):
    if [step["stage"] for step in value["stages"]] != list(STAGES):
        raise ValueError("Workflow did not finish every required stage.")
    # Check again at the return boundary; downstream persistence must still check
    # that its original database snapshot and reservations have not changed.
    if digest(value["result"]) != value["result_hash"] or digest(value["payload"]) != value["request_hash"]:
        raise ValueError("Workflow result changed after audit generation.")
    artifact = value["artifact"]
    if (artifact["request_hash"] != value["request_hash"] or artifact["result_hash"] != value["result_hash"]
            or artifact["snapshot_hash"] != digest(value["payload"]["snapshot"])
            or artifact["run_id"] != value["run_id"] or artifact["provider"] != value["provider"]
            or artifact["job_id"] != value["execution"].get("job_id")
            or artifact["solver_status"] != value["result"]["solver"]["status"]
            or artifact["report_version"] != "workflow-execution-audit-v1"
            or artifact["totals"] != value["result"]["totals"] or artifact["physical_repairs"] != 0
            or artifact["human_approval"] is not False or artifact["simulation_only"] is not True):
        raise ValueError("Workflow audit is inconsistent with the validated calculation.")
    metadata = copy.deepcopy(value["execution"])
    metadata["workflow"] = {"version": VERSION, "orchestrator": orchestrator,
        "run_id": value["run_id"], "task_run_id": task_run_id, "stages": value["stages"],
        "artifact": value["artifact"], "artifact_hash": digest(value["artifact"])}
    return value["result"], metadata


def calculate(snapshot, budget, minutes, provider="local", *, run_key=None, executor=None):
    """Run all four real local stages and return the existing adapter tuple."""
    state = validate_input(new_request(snapshot, budget, minutes, provider, run_key))
    state = execute_plan(state, executor)
    state = validate_result(state)
    state = generate_audit(state)
    return finish(state)
