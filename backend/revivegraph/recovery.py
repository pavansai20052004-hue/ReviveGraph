"""Persisted, simulation-only recovery lifecycle; no physical repair assertions.

The solver runs in FastAPI's worker thread, outside SQLite write transactions.
Every authorizing mutation rechecks the immutable plan against its context.
"""
import json
import sqlite3
import uuid
from typing import Literal

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from .domain import RULE_VERSION, usability
from .imports import Problem, dump, get_registration, now, sha

LIFECYCLE_VERSION = "recovery-lifecycle-v1"


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SolveBody(Body):
    fleet_id: str = "RG-DEMO-12"
    context_id: str = Field(default="demo", pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
    budget_paise: int = Field(default=250000, ge=0, le=100000000, strict=True)
    time_minutes: int = Field(default=330, ge=0, le=1000000, strict=True)


class FailureBody(Body):
    component_id: str


class DecisionBody(Body):
    decision: Literal["approve", "reject"]
    input_hash: str


class EvidenceBody(Body):
    evidence_ref: str = Field(min_length=1, max_length=2000)
    checks: list[str] = Field(max_length=20)


class VerifyBody(EvidenceBody):
    outcome: Literal["pass", "fail", "inconclusive"]


def identifier(prefix):
    return prefix + "_" + uuid.uuid4().hex


def audit(c, action, entity, actor, data):
    c.execute("INSERT INTO audit_events(action,entity_id,actor,occurred_at,data) VALUES (?,?,?,?,?)",
              (action, entity, actor, now(), dump(data)))


def replay(c, key, fingerprint):
    row = c.execute("SELECT * FROM recovery_requests WHERE key=?", (key,)).fetchone()
    if row:
        if row["request_hash"] != fingerprint:
            raise Problem(409, "IDEMPOTENCY_CONFLICT", "Reuse this key with its original actor, route and request, or use a new key.")
        return json.loads(row["response"])


def remember(c, key, fingerprint, result):
    c.execute("INSERT INTO recovery_requests VALUES (?,?,?)", (key, fingerprint, dump(result)))


def fingerprint(route, body, actor):
    return sha(dump({"route": route, "body": body, "actor": actor}))


def context(c, fleet_id, context_id):
    row = c.execute("SELECT * FROM recovery_contexts WHERE fleet_id=? AND id=?", (fleet_id, context_id)).fetchone()
    if not row:
        raise Problem(404, "CONTEXT_NOT_FOUND", "Calculate a recovery plan in this simulation context first.")
    return row


def snapshot(c, fleet_id, ctx, inventory):
    fleet = c.execute("SELECT * FROM fleets WHERE id=?", (fleet_id,)).fetchone()
    if not fleet:
        raise Problem(404, "FLEET_NOT_FOUND", "Import the fleet before calculating a plan.")
    if fleet["mode"] != "simulation":
        raise Problem(422, "PHYSICAL_EXECUTION_UNAVAILABLE", "Physical planning requires real board evidence and reviewed assessments; only simulation is implemented.")
    registration = get_registration(c, fleet["registration_id"])
    computers, components = inventory(c, fleet_id)
    locations = json.loads(ctx["locations"])
    for part in components:
        if part["component_id"] in locations:
            part["location_asset_id"] = locations[part["component_id"]]
    for computer in computers:
        computer["installed_components"] = [p for p in components if p["location_asset_id"] == computer["asset_id"]]
        computer["usability"] = usability(computer, computer["installed_components"], computer["profile"])
    from .optimizer import ENGINE_VERSION
    return {"computers": computers, "components": components, "mode": "simulation",
            "operation_costs": registration["operation_costs"],
            "failed_component_ids": json.loads(ctx["failed_ids"]),
            "fleet_id": fleet_id, "inventory_revision": fleet["revision"],
            "registration_hash": registration["registration_hash"],
            "file_hashes": registration["file_hashes"], "inspection_rule_version": RULE_VERSION,
            "engine_version": ENGINE_VERSION, "lifecycle_version": LIFECYCLE_VERSION,
            "context_id": ctx["id"], "context_revision": ctx["revision"]}


def read_plan(c, plan_id):
    row = c.execute("SELECT * FROM recovery_plans WHERE id=?", (plan_id,)).fetchone()
    if not row:
        raise Problem(404, "PLAN_NOT_FOUND", "Select an existing recovery plan.")
    return row, json.loads(row["data"])


def is_current(c, row):
    fleet = c.execute("SELECT revision FROM fleets WHERE id=?", (row["fleet_id"],)).fetchone()
    ctx = context(c, row["fleet_id"], row["context_id"])
    return (fleet["revision"] == row["inventory_revision"] and ctx["revision"] == row["context_revision"] and not ctx["paused"])


def orders(c, plan_id):
    result = []
    for row in c.execute("SELECT * FROM recovery_orders WHERE plan_id=? ORDER BY target_asset_id", (plan_id,)):
        steps = [{**json.loads(s["data"]), "id": s["id"], "status": s["status"]}
                 for s in c.execute("SELECT * FROM recovery_steps WHERE order_id=? ORDER BY position", (row["id"],))]
        verifications = [json.loads(v["data"]) for v in c.execute("SELECT * FROM recovery_verifications WHERE order_id=? ORDER BY rowid", (row["id"],))]
        result.append({**dict(row), "steps": steps, "verifications": verifications,
                       "verification": verifications[-1] if verifications else None, "mode": "simulation"})
    return result


def public_plan(c, plan_id):
    row, data = read_plan(c, plan_id)
    status = row["status"]
    if status not in ("paused", "rejected", "stale") and not is_current(c, row):
        status = "stale"
    decisions = [dict(r) for r in c.execute("SELECT * FROM recovery_decisions WHERE plan_id=? ORDER BY rowid", (plan_id,))]
    return {**data, "id": plan_id, "status": status, "created_at": row["created_at"],
            "work_orders": orders(c, plan_id), "decisions": decisions,
            "current": is_current(c, row), "synthetic": True}


def require_current(c, row, data, inventory, verify_inputs=False):
    if row["status"] not in ("validated", "approved") or not is_current(c, row):
        raise Problem(409, "STALE_PLAN", "This plan is stale, rejected or paused. Calculate a current plan and approve that exact revision.")
    from .optimizer import ENGINE_VERSION, validate_output
    if data["snapshot"]["engine_version"] != ENGINE_VERSION or data["snapshot"]["inspection_rule_version"] != RULE_VERSION:
        raise Problem(409, "ENGINE_VERSION_MISMATCH", "Recalculate using the current pinned engines.")
    try:
        if sha(dump(data["snapshot"])) != data["snapshot_hash"] or request_hash(data) != data["input_hash"]:
            raise ValueError("Stored inputs no longer match their pinned hashes")
        if sha(dump(data["result"])) != data["output_hash"]:
            raise ValueError("Stored output hash mismatch")
        checked = validate_output(data["snapshot"], data["result"]["allocations"], data["budget_paise"], data["time_minutes"])
        if checked["totals"] != data["result"]["totals"] or checked["operations"] != data["result"]["operations"]:
            raise ValueError("Stored operation/totals mismatch")
    except (ValueError, KeyError, TypeError) as exc:
        raise Problem(409, "PLAN_INVALID", "Independent validation failed; do not execute this plan.") from exc
    if verify_inputs:
        current = snapshot(c, row["fleet_id"], context(c, row["fleet_id"], row["context_id"]), inventory)
        if sha(dump(current)) != data["snapshot_hash"]:
            raise Problem(409, "STALE_PLAN", "Evidence, rules or simulation locations changed. Recalculate before approval.")


def request_hash(data):
    return sha(dump({"snapshot": data["snapshot"], "budget_paise": data["budget_paise"],
                     "time_minutes": data["time_minutes"], "scenario_id": data["scenario_id"]}))


def calculate(db, inventory, body, actor, key, parent=None):
    from .optimizer import solve, validate_output
    route = "solve" if parent is None else "replan:" + parent
    fp = fingerprint(route, body.model_dump(), actor)
    with db.connect() as c:
        c.execute("BEGIN IMMEDIATE")
        prior = replay(c, key, fp)
        if prior:
            return public_plan(c, prior["id"])
        fleet = c.execute("SELECT * FROM fleets WHERE id=?", (body.fleet_id,)).fetchone()
        if not fleet:
            raise Problem(404, "FLEET_NOT_FOUND", "Import the fleet before calculating a plan.")
        c.execute("INSERT OR IGNORE INTO recovery_contexts VALUES (?,?,?,0,'[]','{}',0)", (body.fleet_id, body.context_id, fleet["mode"]))
        ctx = context(c, body.fleet_id, body.context_id)
        if ctx["paused"]:
            raise Problem(409, "RECONCILIATION_REQUIRED", "Work started before failure. Review paused work and begin a separate simulation context; automatic reconciliation is not implemented.")
        if c.execute("SELECT 1 FROM recovery_reservations WHERE fleet_id=? AND context_id=? LIMIT 1", (body.fleet_id, body.context_id)).fetchone():
            raise Problem(409, "CONTEXT_RESERVED", "An approved plan reserves this execution context. Review that plan or choose a separate simulation context.")
        # Re-solving a running context would silently repeat operations. Require a
        # separate context for a fresh rehearsal, preserving completed transfers.
        if c.execute("SELECT 1 FROM recovery_steps s JOIN recovery_orders o ON o.id=s.order_id JOIN recovery_plans p ON p.id=o.plan_id WHERE p.fleet_id=? AND p.context_id=? AND s.status='done' LIMIT 1", (body.fleet_id, body.context_id)).fetchone():
            raise Problem(409, "EXECUTION_STARTED", "This rehearsal has started. Choose a new context for another rehearsal.")
        source = snapshot(c, body.fleet_id, ctx, inventory)
        c.commit()
    try:
        result = solve(source, body.budget_paise, body.time_minutes)
        checked = validate_output(source, result["allocations"], body.budget_paise, body.time_minutes)
        if checked["totals"] != result["totals"] or checked["operations"] != result["operations"]:
            raise ValueError("Solver output and independent validation differ")
    except ValueError as exc:
        raise Problem(422, "ALLOCATION_INVALID", str(exc)) from exc
    if result["solver"]["status"] not in ("OPTIMAL", "FEASIBLE"):
        raise Problem(409, "NO_VALIDATED_SOLUTION", "Solver did not produce a validated incumbent. Retry with smaller inputs.")
    data = {"fleet_id": body.fleet_id, "context_id": body.context_id, "mode": "simulation",
            "inventory_revision": source["inventory_revision"], "context_revision": source["context_revision"],
            "scenario_id": f"{body.fleet_id}:{body.context_id}:{source['context_revision']}",
            "parent_plan_id": parent, "budget_paise": body.budget_paise, "time_minutes": body.time_minutes,
            "snapshot": source, "snapshot_hash": sha(dump(source)), "result": result, "output_hash": sha(dump(result)),
            "validation": {"valid": True, "validator": "independent-allocation-check-v1"},
            "assumptions": ["Authored synthetic assertions and toy board profiles; simulation only.",
                            "Integer INR paise; single technician effort pool in minutes; no wages added.",
                            "No purchases; preparation includes handling and consumables; no environmental estimates."]}
    data["input_hash"] = request_hash(data)
    with db.connect() as c:
        c.execute("BEGIN IMMEDIATE")
        prior = replay(c, key, fp)
        if prior:
            return public_plan(c, prior["id"])
        current = snapshot(c, body.fleet_id, context(c, body.fleet_id, body.context_id), inventory)
        if sha(dump(current)) != data["snapshot_hash"]:
            raise Problem(409, "STALE_SNAPSHOT", "Inventory or scenario changed while solving. Retry the calculation.")
        if c.execute("SELECT 1 FROM recovery_reservations WHERE fleet_id=? AND context_id=? LIMIT 1", (body.fleet_id, body.context_id)).fetchone():
            raise Problem(409, "CONTEXT_RESERVED", "Another plan was approved while solving. Review that plan or use a new simulation context.")
        plan_id = identifier("plan")
        if parent:
            _, before = read_plan(c, parent)
            old = {a["target_asset_id"]: a for a in before["result"]["allocations"]}
            new = {a["target_asset_id"]: a for a in result["allocations"]}
            data["comparison"] = {"before_plan_id": parent, "after_plan_id": plan_id,
                "before_totals": before["result"]["totals"], "after_totals": result["totals"],
                "changed_targets": [{"target_asset_id": a, "before": old.get(a), "after": new.get(a)} for a in sorted(old.keys() | new.keys()) if old.get(a) != new.get(a)]}
        c.execute("INSERT INTO recovery_plans VALUES (?,?,?,?,?,?,?,?)", (plan_id, body.fleet_id, body.context_id, source["context_revision"], source["inventory_revision"], "validated", dump(data), now()))
        audit(c, "plan_validated", plan_id, actor, {"input_hash": data["input_hash"], "solver": result["solver"]})
        response = public_plan(c, plan_id)
        remember(c, key, fp, {"id": plan_id})
        c.commit()
        return response


CHECKS = {
    "prepare_target": ["simulation_workspace_ready", "power_isolation_simulated"],
    "remove_ram": ["component_id_checked", "extraction_simulated"],
    "remove_storage": ["component_id_checked", "data_handling_authorized", "extraction_simulated"],
    "install_ram": ["component_id_checked", "installation_simulated"],
    "install_storage": ["component_id_checked", "data_handling_authorized", "installation_simulated"],
    "verify_target": ["simulated_boot", "simulated_memory_check", "simulated_storage_check", "data_handling_checked"],
}


def valid_evidence(body, required, complete=True):
    if not body.evidence_ref.strip() or len(body.checks) != len(set(body.checks)) or not set(body.checks) <= set(required):
        raise Problem(422, "EVIDENCE_INVALID", "Supply a nonblank simulation evidence reference and distinct checklist IDs from this step.")
    if complete and set(body.checks) != set(required):
        raise Problem(422, "CHECKLIST_INCOMPLETE", "Complete every required checklist item before recording completion/pass.")


def install_routes(app, inventory, headers):
    db = app.state.db

    @app.post("/api/v1/plans")
    def create_plan(body: SolveBody, identity=Depends(headers)):
        return calculate(db, inventory, body, *identity)

    @app.get("/api/v1/plans")
    def list_plans(fleet_id: str = "RG-DEMO-12", limit: int = Query(50, ge=1, le=200)):
        with db.connect() as c:
            return {"items": [public_plan(c, r["id"]) for r in c.execute("SELECT id FROM recovery_plans WHERE fleet_id=? ORDER BY rowid DESC LIMIT ?", (fleet_id, limit))]}

    @app.get("/api/v1/plans/{plan_id}")
    def get_plan(plan_id: str):
        with db.connect() as c:
            return public_plan(c, plan_id)

    @app.post("/api/v1/plans/{plan_id}/failures")
    def fail(plan_id: str, body: FailureBody, identity=Depends(headers)):
        actor, key = identity
        fp = fingerprint("failure:" + plan_id, body.model_dump(), actor)
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            prior = replay(c, key, fp)
            if prior:
                if prior.get("paused"):
                    raise Problem(409, "RECONCILIATION_REQUIRED", "Failure is recorded; work remains paused. Start a separate rehearsal after reviewing progress.")
                if prior.get("pending"):
                    _, data = read_plan(c, plan_id)
                    c.commit()
                    return finish_failure(plan_id, key, fp, actor, data)
                return public_plan(c, prior["id"])
            row, data = read_plan(c, plan_id)
            require_current(c, row, data, inventory)
            selected = {p for a in data["result"]["allocations"] for p in a["ram_component_ids"] + [a["storage_component_id"]]}
            if body.component_id not in selected:
                raise Problem(422, "FAILURE_NOT_ALLOCATED", "Choose a component from this actual computed allocation.")
            ctx = context(c, row["fleet_id"], row["context_id"])
            failed = sorted(set(json.loads(ctx["failed_ids"])) | {body.component_id})
            started = bool(c.execute("SELECT 1 FROM recovery_steps s JOIN recovery_orders o ON o.id=s.order_id JOIN recovery_plans p ON p.id=o.plan_id WHERE p.fleet_id=? AND p.context_id=? AND s.status='done' LIMIT 1", (row["fleet_id"], row["context_id"])).fetchone())
            c.execute("UPDATE recovery_contexts SET failed_ids=?,revision=revision+1,paused=? WHERE fleet_id=? AND id=?", (dump(failed), int(started), row["fleet_id"], row["context_id"]))
            c.execute("INSERT INTO recovery_failures VALUES (?,?,?,?,?,?)", (identifier("failure"), plan_id, ctx["revision"] + 1, body.component_id, actor, now()))
            c.execute("UPDATE recovery_plans SET status=? WHERE fleet_id=? AND context_id=? AND status IN ('validated','approved')", ("paused" if started else "stale", row["fleet_id"], row["context_id"]))
            c.execute("UPDATE recovery_orders SET status='paused' WHERE status NOT IN ('verified_pass','verification_failed','verification_inconclusive') AND plan_id IN (SELECT id FROM recovery_plans WHERE fleet_id=? AND context_id=?)", (row["fleet_id"], row["context_id"]))
            c.execute("DELETE FROM recovery_reservations WHERE fleet_id=? AND context_id=?", (row["fleet_id"], row["context_id"]))
            audit(c, "simulated_failure", plan_id, actor, {"component_id": body.component_id, "context_revision": ctx["revision"] + 1, "work_paused": started})
            # Persist failure before solving. Retry recovers from a crash between
            # overlay creation and the revised plan without applying failure twice.
            remember(c, key, fp, {"pending": True, "paused": started, "parent": plan_id})
            c.commit()
        if started:
            raise Problem(409, "RECONCILIATION_REQUIRED", "Failure recorded and work paused. Completed simulation steps/locations are preserved. Automatic reconciliation is not implemented; use a separate rehearsal context.")
        return finish_failure(plan_id, key, fp, actor, data)

    def finish_failure(plan_id, key, fp, actor, data):
        revised = calculate(db, inventory, SolveBody(fleet_id=data["fleet_id"], context_id=data["context_id"], budget_paise=data["budget_paise"], time_minutes=data["time_minutes"]), actor, "replan-" + sha(key), parent=plan_id)
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("UPDATE recovery_requests SET response=? WHERE key=? AND request_hash=?", (dump({"id": revised["id"]}), key, fp))
            c.commit()
        return revised

    @app.post("/api/v1/plans/{plan_id}/decision")
    def decide(plan_id: str, body: DecisionBody, identity=Depends(headers)):
        actor, key = identity
        fp = fingerprint("decision:" + plan_id, body.model_dump(), actor)
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            prior = replay(c, key, fp)
            if prior:
                return public_plan(c, plan_id)
            row, data = read_plan(c, plan_id)
            require_current(c, row, data, inventory, verify_inputs=True)
            if body.input_hash != data["input_hash"] or request_hash(data) != data["input_hash"]:
                raise Problem(409, "PLAN_HASH_MISMATCH", "Approve or reject the exact displayed plan input hash.")
            if row["status"] != "validated":
                raise Problem(409, "DECISION_EXISTS", "This plan already has a decision. Calculate a new plan to change it.")
            status = "approved" if body.decision == "approve" else "rejected"
            try:
                if body.decision == "approve":
                    if c.execute("SELECT 1 FROM recovery_plans WHERE fleet_id=? AND context_id=? AND status='approved' AND id<>? LIMIT 1", (row["fleet_id"], row["context_id"], plan_id)).fetchone():
                        raise Problem(409, "RESERVATION_CONFLICT", "Only one approved execution plan is permitted per simulation context, including donor/displacement operations.")
                    for a in data["result"]["allocations"]:
                        subjects = [("target", a["target_asset_id"])] + [("component", p) for p in a["ram_component_ids"] + [a["storage_component_id"]]]
                        for kind, subject in subjects:
                            c.execute("INSERT INTO recovery_reservations VALUES (?,?,?,?,?,?)", (row["fleet_id"], "simulation", row["context_id"], kind, subject, plan_id))
            except sqlite3.IntegrityError as exc:
                raise Problem(409, "RESERVATION_CONFLICT", "A target or physical part is reserved by another approved plan in this context. Use a separate simulation context or review existing work.") from exc
            c.execute("INSERT INTO recovery_decisions VALUES (?,?,?,?,?,?)", (identifier("decision"), plan_id, body.decision, actor, now(), body.input_hash))
            c.execute("UPDATE recovery_plans SET status=? WHERE id=?", (status, plan_id))
            audit(c, "plan_" + status, plan_id, actor, {"input_hash": body.input_hash, "mode": "simulation"})
            response = public_plan(c, plan_id)
            remember(c, key, fp, {"id": plan_id})
            c.commit()
            return response

    @app.post("/api/v1/plans/{plan_id}/work-orders")
    def create_orders(plan_id: str, body: Body, identity=Depends(headers)):
        actor, key = identity
        fp = fingerprint("orders:" + plan_id, {}, actor)
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            prior = replay(c, key, fp)
            row, data = read_plan(c, plan_id)
            require_current(c, row, data, inventory)
            if row["status"] != "approved":
                raise Problem(409, "APPROVAL_REQUIRED", "Explicitly approve this exact validated plan before creating work orders.")
            existing = orders(c, plan_id)
            if existing:
                if not prior:
                    remember(c, key, fp, {"plan_id": plan_id})
                    c.commit()
                return {"items": existing}
            require_current(c, row, data, inventory, verify_inputs=True)
            required = {("target", a["target_asset_id"]) for a in data["result"]["allocations"]}
            required |= {("component", p) for a in data["result"]["allocations"] for p in a["ram_component_ids"] + [a["storage_component_id"]]}
            reserved = {(r["subject_type"], r["subject_id"]) for r in c.execute("SELECT * FROM recovery_reservations WHERE plan_id=?", (plan_id,))}
            if reserved != required:
                raise Problem(409, "RESERVATION_LOST", "Reservations no longer match this plan. Do not start work.")
            operations = data["result"]["operations"]
            target_ids = sorted({o["asset_id"] for o in operations if o["operation"] in ("prepare_target", "verify_target")})
            order_ids = {t: identifier("order") for t in target_ids}
            for t, order_id in order_ids.items():
                c.execute("INSERT INTO recovery_orders VALUES (?,?,?,'pending')", (order_id, plan_id, t))
            destinations = {p: a["target_asset_id"] for a in data["result"]["allocations"] for p in a["ram_component_ids"] + [a["storage_component_id"]]}
            prepared = {t: identifier("step") for t in target_ids}
            step_ids = [prepared[o["asset_id"]] if o["operation"] == "prepare_target" else identifier("step") for o in operations]
            removals = [step_ids[i] for i, o in enumerate(operations) if o["operation"].startswith("remove_")]
            staged = []
            for i, op in enumerate(operations):
                t = op["asset_id"] if op["asset_id"] in order_ids else destinations.get(op.get("component_id"))
                if not t or t not in order_ids:
                    raise Problem(409, "OPERATION_INVALID", "An operation has no traceable receiving target.")
                deps = []
                if op["operation"] != "prepare_target":
                    deps = [prepared[t]]
                if op["operation"].startswith("install_"):
                    deps += removals
                staged.append({**op, "id": step_ids[i], "target_asset_id": t, "depends_on": sorted(set(deps)), "required_checks": CHECKS[op["operation"]]})
            for step in staged:
                if step["operation"] == "verify_target":
                    step["depends_on"] = sorted(s["id"] for s in staged if s["target_asset_id"] == step["target_asset_id"] and s["id"] != step["id"])
            for i, step in enumerate(staged):
                c.execute("INSERT INTO recovery_steps VALUES (?,?,?,'pending',?)", (step["id"], order_ids[step["target_asset_id"]], i, dump(step)))
            audit(c, "work_orders_created", plan_id, actor, {"orders": order_ids, "mode": "simulation"})
            response = {"items": orders(c, plan_id)}
            if not prior:
                remember(c, key, fp, {"plan_id": plan_id})
            c.commit()
            return response

    def active_order(c, order_id):
        order = c.execute("SELECT * FROM recovery_orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            raise Problem(404, "ORDER_NOT_FOUND", "Select a persisted work order.")
        row, data = read_plan(c, order["plan_id"])
        require_current(c, row, data, inventory)
        if row["status"] != "approved" or order["status"] == "paused":
            raise Problem(409, "WORK_PAUSED", "Work requires a current approved plan and unpaused order.")
        return order, row, data

    def dependencies_done(c, step):
        if any(not (r := c.execute("SELECT status FROM recovery_steps WHERE id=?", (s,)).fetchone()) or r["status"] != "done" for s in step["depends_on"]):
            raise Problem(409, "DEPENDENCIES_INCOMPLETE", "Complete the listed prerequisite steps, including donor extraction in other orders.")

    @app.post("/api/v1/work-orders/{order_id}/steps/{step_id}")
    def complete_step(order_id: str, step_id: str, body: EvidenceBody, identity=Depends(headers)):
        actor, key = identity
        fp = fingerprint(f"step:{order_id}:{step_id}", body.model_dump(), actor)
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            prior = replay(c, key, fp)
            if prior:
                return prior
            order, plan, data = active_order(c, order_id)
            row = c.execute("SELECT * FROM recovery_steps WHERE id=? AND order_id=?", (step_id, order_id)).fetchone()
            if not row:
                raise Problem(404, "STEP_NOT_FOUND", "Select a step belonging to this order.")
            step = json.loads(row["data"])
            if step["operation"] == "verify_target":
                raise Problem(422, "VERIFICATION_REQUIRED", "Use the verification action with pass, fail or inconclusive outcome.")
            if row["status"] == "done":
                raise Problem(409, "STEP_ALREADY_RECORDED", "The original evidence is preserved. Retry its original idempotency key.")
            valid_evidence(body, step["required_checks"])
            dependencies_done(c, step)
            ctx = context(c, plan["fleet_id"], plan["context_id"])
            locations = json.loads(ctx["locations"])
            parts = {p["component_id"]: p for p in data["snapshot"]["components"]}
            component = step.get("component_id")
            if component:
                current = locations.get(component, parts[component]["location_asset_id"])
                expected = step["asset_id"] if step["operation"].startswith("remove_") else None
                if current != expected:
                    raise Problem(409, "LOCATION_CONFLICT", "Simulation location does not match this operation; pause and inspect work.")
                locations[component] = None if step["operation"].startswith("remove_") else step["asset_id"]
                c.execute("UPDATE recovery_contexts SET locations=? WHERE fleet_id=? AND id=?", (dump(locations), plan["fleet_id"], plan["context_id"]))
            step.update(evidence_ref=body.evidence_ref.strip(), checks=body.checks, actor=actor, completed_at=now(), evidence_kind="authored_simulation_record")
            c.execute("UPDATE recovery_steps SET status='done',data=? WHERE id=?", (dump(step), step_id))
            c.execute("UPDATE recovery_orders SET status='in_progress' WHERE id=?", (order_id,))
            audit(c, "simulated_step_completed", order_id, actor, {"step_id": step_id, **body.model_dump()})
            response = {"id": step_id, "status": "done", "mode": "simulation"}
            remember(c, key, fp, response)
            c.commit()
            return response

    @app.post("/api/v1/work-orders/{order_id}/verification")
    def verify(order_id: str, body: VerifyBody, identity=Depends(headers)):
        actor, key = identity
        fp = fingerprint("verify:" + order_id, body.model_dump(), actor)
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            prior = replay(c, key, fp)
            if prior:
                return prior
            order, plan, data = active_order(c, order_id)
            step_row = next((s for s in c.execute("SELECT * FROM recovery_steps WHERE order_id=?", (order_id,)) if json.loads(s["data"])["operation"] == "verify_target"), None)
            if not step_row:
                raise Problem(409, "VERIFICATION_STEP_MISSING", "This order has no verification step.")
            step = json.loads(step_row["data"])
            valid_evidence(body, step["required_checks"], complete=body.outcome == "pass")
            dependencies_done(c, step)
            # A pass must also agree with actual completed simulation locations.
            if body.outcome == "pass":
                ctx = context(c, plan["fleet_id"], plan["context_id"])
                locations = json.loads(ctx["locations"])
                expected = next(a for a in data["result"]["allocations"] if a["target_asset_id"] == order["target_asset_id"])
                ids = set(expected["ram_component_ids"] + [expected["storage_component_id"]])
                installed = {p["component_id"] for p in data["snapshot"]["components"] if locations.get(p["component_id"], p["location_asset_id"]) == order["target_asset_id"]}
                if installed != ids:
                    raise Problem(409, "FINAL_LOCATION_MISMATCH", "Installed simulated parts do not match the approved complete configuration.")
            record = {"id": identifier("verification"), "order_id": order_id, "outcome": body.outcome,
                      "mode": "simulation", "evidence_kind": "authored_simulation_record",
                      "evidence_ref": body.evidence_ref.strip(), "checks": body.checks, "actor": actor, "recorded_at": now()}
            c.execute("INSERT INTO recovery_verifications VALUES (?,?,?,?)", (record["id"], order_id, dump(record), record["recorded_at"]))
            c.execute("UPDATE recovery_steps SET status=?,data=? WHERE id=?", ("done" if body.outcome == "pass" else body.outcome, dump({**step, **record}), step_row["id"]))
            c.execute("UPDATE recovery_orders SET status=? WHERE id=?", ({"pass": "verified_pass", "fail": "verification_failed", "inconclusive": "verification_inconclusive"}[body.outcome], order_id))
            audit(c, "simulated_verification_recorded", order_id, actor, record)
            remember(c, key, fp, record)
            c.commit()
            return record

    @app.get("/api/v1/audit-events")
    def audit_events(fleet_id: str = "RG-DEMO-12", offset: int = Query(0, ge=0),
                     limit: int = Query(50, ge=1, le=200),
                     action: str | None = Query(None, max_length=100)):
        # Scope through relational ownership, never through user-supplied JSON.
        # Registrations can be shared by fleets and are deliberately excluded.
        scope = """WITH scoped_entities(id) AS (
            SELECT id FROM batches WHERE fleet_id=:fleet
            UNION SELECT id FROM computers WHERE fleet_id=:fleet
            UNION SELECT id FROM components WHERE fleet_id=:fleet
            UNION SELECT id FROM recovery_plans WHERE fleet_id=:fleet
            UNION SELECT o.id FROM recovery_orders o JOIN recovery_plans p
                ON p.id=o.plan_id WHERE p.fleet_id=:fleet
            UNION SELECT f.id FROM recovery_failures f JOIN recovery_plans p
                ON p.id=f.plan_id WHERE p.fleet_id=:fleet
            UNION SELECT v.id FROM recovery_verifications v JOIN recovery_orders o
                ON o.id=v.order_id JOIN recovery_plans p ON p.id=o.plan_id WHERE p.fleet_id=:fleet
        ) """
        where = " WHERE entity_id IN (SELECT id FROM scoped_entities) AND (:action IS NULL OR action=:action)"
        parameters = {"fleet": fleet_id, "action": action, "limit": limit, "offset": offset}
        with db.connect() as c:
            c.execute("BEGIN")
            total = c.execute(scope + "SELECT COUNT(*) FROM audit_events" + where, parameters).fetchone()[0]
            rows = c.execute(scope + "SELECT * FROM audit_events" + where + " ORDER BY id DESC LIMIT :limit OFFSET :offset", parameters).fetchall()
            return {"items": [{**dict(row), "data": json.loads(row["data"])} for row in rows],
                    "total": total, "offset": offset, "limit": limit}

    @app.get("/api/v1/plans/{plan_id}/report")
    def report(plan_id: str):
        with db.connect() as c:
            plan = public_plan(c, plan_id)
            ids = [plan_id] + [o["id"] for o in plan["work_orders"]]
            history_ids = [r["id"] for r in c.execute("SELECT id FROM recovery_plans WHERE fleet_id=? AND context_id=? ORDER BY rowid", (plan["fleet_id"], plan["context_id"]))]
            ids += history_ids
            events = [{**dict(r), "data": json.loads(r["data"])} for r in c.execute("SELECT * FROM audit_events ORDER BY id") if r["entity_id"] in ids]
            return {"report_version": "recovery-audit-v1", "generated_at": now(), "mode": "simulation",
                    "disclaimer": "Synthetic inputs and authored simulation checks; no physically verified repairs or environmental savings.",
                    "plan": plan, "history": [public_plan(c, p) for p in history_ids],
                    "failures": [dict(r) for r in c.execute("SELECT * FROM recovery_failures ORDER BY rowid") if r["plan_id"] in history_ids],
                    "audit_events": events, "physical_verified_repairs": 0}


def recovery_summary(c, fleet_id):
    latest = c.execute("SELECT id FROM recovery_plans WHERE fleet_id=? ORDER BY rowid DESC LIMIT 1", (fleet_id,)).fetchone()
    plans = c.execute("SELECT COUNT(*) FROM recovery_plans WHERE fleet_id=?", (fleet_id,)).fetchone()[0]
    rows = c.execute("SELECT o.status FROM recovery_orders o JOIN recovery_plans p ON p.id=o.plan_id WHERE p.fleet_id=?", (fleet_id,)).fetchall()
    recovery = {"plans": plans, "orders": len(rows), "simulated_passes": sum(r["status"] == "verified_pass" for r in rows), "physical_passes": 0}
    if not latest:
        return {"status": "Not calculated"}, recovery
    plan = public_plan(c, latest["id"])
    return {"status": plan["result"]["solver"]["status"], "plan_id": latest["id"], "plan_status": plan["status"], **plan["result"]["totals"]}, recovery
