"""Explicit reviewed continuation of interrupted synthetic work; no physical writes."""
import json
from .imports import Problem, dump, now, sha

POLICY = "reviewed-simulation-continuation-v1"


def lineage(c, fleet_id, context_id):
    row = c.execute("SELECT * FROM recovery_reconciliations WHERE fleet_id=? AND target_context_id=?", (fleet_id, context_id)).fetchone()
    if not row:
        return None
    data = json.loads(row["data"])
    if sha(dump({k:v for k,v in data.items() if k != "lineage_hash"})) != data.get("lineage_hash"):
        raise Problem(409, "RECONCILIATION_INVALID", "Continuation accounting no longer matches its pinned hash.")
    return data


def checked_plan(data):
    from . import recovery as life
    from .optimizer import validate_output
    try:
        if (sha(dump(data["snapshot"])) != data["snapshot_hash"]
                or life.request_hash(data) != data["input_hash"]
                or sha(dump(data["result"])) != data["output_hash"]):
            raise ValueError("Plan identity changed")
        checked = validate_output(data["snapshot"], data["result"]["allocations"], data["budget_paise"], data["time_minutes"])
        if checked["totals"] != data["result"]["totals"] or checked["operations"] != data["result"]["operations"]:
            raise ValueError("Operation accounting changed")
    except (ValueError, KeyError, TypeError) as exc:
        raise Problem(409, "RECONCILIATION_INVALID", "Paused work cannot be reconciled because its pinned plan is invalid.") from exc


def checkpoint(c, inventory, plan_id):
    from . import recovery as life
    row, data = life.read_plan(c, plan_id)
    ctx = life.context(c, row["fleet_id"], row["context_id"])
    if row["status"] != "paused" or not ctx["paused"]:
        raise Problem(409, "RECONCILIATION_NOT_REQUIRED", "Select the paused plan whose execution was interrupted by a failure.")
    executed = c.execute("SELECT 1 FROM recovery_steps s JOIN recovery_orders o ON o.id=s.order_id WHERE o.plan_id=? AND s.status='done' LIMIT 1", (plan_id,)).fetchone()
    approved = c.execute("SELECT 1 FROM recovery_decisions WHERE plan_id=? AND decision='approve' AND input_hash=? LIMIT 1", (plan_id, data["input_hash"])).fetchone()
    if not executed or not approved:
        raise Problem(409, "EXECUTION_PLAN_REQUIRED", "Select the approved paused plan that actually recorded work. An unused plan cannot define continuation limits.")
    checked_plan(data)
    current = life.snapshot(c, row["fleet_id"], ctx, inventory)
    if current["inventory_revision"] != row["inventory_revision"]:
        raise Problem(409, "STALE_INVENTORY", "Inventory changed since this work started; reconcile outside this synthetic continuation before proceeding.")
    earlier = lineage(c, row["fleet_id"], row["context_id"])
    spent = list(earlier["consumed_operations"]) if earlier else []
    ceilings = earlier["original_limits"] if earlier else {"budget_paise": data["budget_paise"], "time_minutes": data["time_minutes"]}
    for p in c.execute("SELECT id,data FROM recovery_plans WHERE fleet_id=? AND context_id=? ORDER BY rowid", (row["fleet_id"], row["context_id"])):
        saved = json.loads(p["data"])
        items = life.orders(c, p["id"])
        if not items:
            continue
        checked_plan(saved)
        expected = saved["result"]["operations"]
        for order in items:
            for step in order["steps"]:
                fields = ("operation", "asset_id", "component_id", "cost_paise", "technician_minutes")
                operation = next((op for op in expected if all(op.get(k) == step.get(k) for k in fields)), None)
                if operation is None:
                    raise Problem(409, "RECONCILIATION_INVALID", "A saved work step differs from its approved operation ledger.")
                if step["operation"] == "verify_target":
                    for verification in order["verifications"]:
                        spent.append({**operation, "plan_id":p["id"], "step_id":step["id"], "verification_id":verification["id"], "outcome":verification["outcome"], "evidence_ref":verification["evidence_ref"], "actor":verification["actor"], "recorded_at":verification["recorded_at"]})
                elif step["status"] == "done":
                    if step.get("evidence_kind") != "authored_simulation_record" or not step.get("evidence_ref"):
                        raise Problem(409, "RECONCILIATION_INVALID", "Completed work has no authored simulation evidence.")
                    spent.append({**operation, "plan_id":p["id"], "step_id":step["id"], "evidence_ref":step["evidence_ref"], "actor":step["actor"], "recorded_at":step["completed_at"]})
    spent_cash = sum(s["cost_paise"] for s in spent)
    spent_time = sum(s["technician_minutes"] for s in spent)
    if spent_cash > ceilings["budget_paise"] or spent_time > ceilings["time_minutes"]:
        raise Problem(409, "RESOURCES_EXHAUSTED", "Recorded operation attempts already exceed the original limits; this continuation cannot authorize more work.")
    required = sorted(set(earlier["verification_required_asset_ids"] if earlier else [])
                      | {a["target_asset_id"] for a in data["result"]["allocations"]})
    result = {"policy_version": POLICY, "mode":"simulation", "synthetic":True,
        "source_plan_id":plan_id, "source_context_id":row["context_id"], "source_revision":ctx["revision"],
        "fleet_id":row["fleet_id"], "inventory_revision":current["inventory_revision"],
        "source_input_hash":data["input_hash"], "source_output_hash":data["output_hash"],
        "current_snapshot_hash":sha(dump(current)),
        "locations":{p["component_id"]:p["location_asset_id"] for p in current["components"]},
        "failed_component_ids":current["failed_component_ids"], "verification_required_asset_ids":required,
        "consumed_operations":spent, "original_limits":ceilings,
        "consumed":{"cost_paise":spent_cash,"technician_minutes":spent_time},
        "remaining_limits":{"budget_paise":ceilings["budget_paise"]-spent_cash,"time_minutes":ceilings["time_minutes"]-spent_time},
        "preparation_policy":"Fresh preparation and verification are conservatively charged for interrupted targets. Completed component movements are represented by current scenario locations, never replayed.",
        "counting_policy":"Newly recovered uses the authored health/usability baseline in this snapshot before scenario failure exclusions. Do not add recovery counts across revisions or contexts."}
    result["source_state_hash"] = sha(dump(result))
    link = c.execute("SELECT target_plan_id,target_context_id FROM recovery_reconciliations WHERE fleet_id=? AND source_context_id=? AND source_revision=?", (row["fleet_id"], row["context_id"], ctx["revision"])).fetchone()
    if link:
        result["continuation_plan_id"] = link["target_plan_id"]
        result["continuation_context_id"] = link["target_context_id"]
    return result


def preview(db, inventory, plan_id):
    with db.connect() as c:
        c.execute("BEGIN")
        return checkpoint(c, inventory, plan_id)


def begin(db, inventory, plan_id, body, actor, key, calculate):
    from . import recovery as life
    fp = life.fingerprint("reconcile:"+plan_id, body.model_dump(), actor)
    if not body.reviewed or not body.evidence_ref.strip():
        raise Problem(422,"RECONCILIATION_REVIEW_REQUIRED","Review preserved locations, failed parts, completed evidence and remaining resources, then supply authored simulation evidence.")
    with db.connect() as c:
        c.execute("BEGIN IMMEDIATE")
        prior = life.replay(c,key,fp)
        if prior:
            link = c.execute("SELECT * FROM recovery_reconciliations WHERE id=?",(prior["reconciliation_id"],)).fetchone()
            if link["target_plan_id"]:
                return life.public_plan(c,link["target_plan_id"])
            evidence = lineage(c,link["fleet_id"],link["target_context_id"])
        else:
            state = checkpoint(c,inventory,plan_id)
            if state["source_state_hash"] != body.source_state_hash:
                raise Problem(409,"RECONCILIATION_CHANGED","Paused work or evidence changed. Refresh and review the reconciliation preview again.")
            existing = c.execute("SELECT * FROM recovery_reconciliations WHERE fleet_id=? AND source_context_id=? AND source_revision=?",(state["fleet_id"],state["source_context_id"],state["source_revision"])).fetchone()
            if existing:
                raise Problem(409,"RECONCILIATION_EXISTS","This paused revision already has a continuation. Select its saved plan or retry the original request key.")
            target_context = "continue_"+life.identifier("ctx")[4:]
            evidence = {**state,"target_context_id":target_context,"reviewed":True,"review_evidence_ref":body.evidence_ref.strip(),"review_actor":actor,"reviewed_at":now()}
            evidence["lineage_hash"] = sha(dump(evidence))
            link_id=life.identifier("reconciliation")
            c.execute("INSERT INTO recovery_contexts VALUES (?,?,?,0,?,?,0)",(state["fleet_id"],target_context,"simulation",dump(state["failed_component_ids"]),dump(state["locations"])))
            c.execute("INSERT INTO recovery_reconciliations VALUES (?,?,?,?,?,?,NULL,?,?,?)",(link_id,state["fleet_id"],state["source_context_id"],state["source_revision"],plan_id,target_context,dump(evidence),actor,now()))
            life.audit(c,"simulation_reconciliation_reviewed",plan_id,actor,{"reconciliation_id":link_id,**evidence})
            life.remember(c,key,fp,{"reconciliation_id":link_id})
            link=c.execute("SELECT * FROM recovery_reconciliations WHERE id=?",(link_id,)).fetchone()
        c.commit()
    limits=evidence["remaining_limits"]
    result=calculate(db,inventory,life.SolveBody(fleet_id=link["fleet_id"],context_id=link["target_context_id"],budget_paise=limits["budget_paise"],time_minutes=limits["time_minutes"],execution="local",orchestration="local"),link["actor"],"continuation-"+link["id"],parent=link["source_plan_id"])
    with db.connect() as c:
        c.execute("BEGIN IMMEDIATE")
        c.execute("UPDATE recovery_reconciliations SET target_plan_id=? WHERE id=? AND target_plan_id IS NULL",(result["id"],link["id"]))
        c.commit()
    return result
