"""Interrupted synthetic work requires explicit review, remaining resources and new approval."""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from revivegraph import workflow
from revivegraph.main import create_app
from test_recovery import env, plan, post, work, decision, allocated_ids, complete_ready_steps


def record(client, order, step):
    response = post(client, f"/work-orders/{order['id']}/steps/{step['id']}", {
        "checks": step["required_checks"], "evidence_ref": "synthetic:automated-continuation:" + step["id"]})
    assert response.status_code == 200, response.text


def interrupted(client, stage="removals", **limits):
    p = plan(client, **limits)
    items = work(client, p)
    done, spent = set(), []
    pending = [(o, s) for o in items for s in o["steps"] if s["operation"] != "verify_target"]
    while pending:
        ready = next(((o, s) for o, s in pending if set(s["depends_on"]) <= done
                      and (stage != "removals" or not s["operation"].startswith("install_"))), None)
        if not ready:
            break
        order, step = ready
        record(client, order, step)
        done.add(step["id"]); spent.append(step); pending.remove(ready)
    donor = next(op for op in p["result"]["operations"] if op["operation"].startswith("remove_")
                 and op.get("target_asset_id") and op["asset_id"] != op["target_asset_id"])
    response = post(client, f"/plans/{p['id']}/failures", {"component_id": donor["component_id"]})
    assert response.status_code == 409 and response.json()["error"]["code"] == "RECONCILIATION_REQUIRED", response.text
    preview = client.get(f"/api/v1/plans/{p['id']}/reconciliation-preview")
    assert preview.status_code == 200, preview.text
    return p, items, spent, donor["component_id"], preview.json()


def review(preview):
    return {"source_state_hash": preview["source_state_hash"], "reviewed": True,
            "evidence_ref": "synthetic:automated-reconciliation-review"}


def reconcile(client, p, preview, key="reconcile-reviewed"):
    response = post(client, f"/plans/{p['id']}/reconcile", review(preview), key)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("stage", ["removals", "installed"])
def test_continuation_preserves_locations_and_charges_remaining_work(env, stage):
    app, client, path = env
    physical = client.get("/api/v1/components").json()
    p, items, spent, failed, preview = interrupted(client, stage)
    assert preview["consumed"] == {"cost_paise": sum(s["cost_paise"] for s in spent),
                                   "technician_minutes": sum(s["technician_minutes"] for s in spent)}
    after = reconcile(client, p, preview)
    assert after["context_id"] != p["context_id"] and after["parent_plan_id"] == p["id"]
    assert after["status"] == "validated" and after["decisions"] == []
    assert failed not in allocated_ids(after)
    assert after["execution"]["provider"] == "local"
    assert after["budget_paise"] + preview["consumed"]["cost_paise"] == p["budget_paise"]
    assert after["time_minutes"] + preview["consumed"]["technician_minutes"] == p["time_minutes"]
    assert after["resource_accounting"]["cumulative_projected"]["cost_paise"] <= p["budget_paise"]
    assert after["resource_accounting"]["cumulative_projected"]["technician_minutes"] <= p["time_minutes"]
    assert {x["component_id"]: x["location_asset_id"] for x in after["snapshot"]["components"]} == preview["locations"]
    old_removals = {s["component_id"] for s in spent if s["operation"].startswith("remove_")}
    new_removals = {s["component_id"] for s in after["result"]["operations"] if s["operation"].startswith("remove_")}
    if stage == "removals":
        assert not old_removals & new_removals
    if stage == "installed":
        assert {s["asset_id"] for s in after["result"]["operations"] if s["operation"] == "verify_target"} == {a["target_asset_id"] for a in after["result"]["allocations"]}
    assert decision(client, p).status_code == 409
    assert post(client, f"/plans/{after['id']}/work-orders", {}).status_code == 409
    assert reconcile(client, p, preview)["id"] == after["id"]
    assert post(client, f"/plans/{p['id']}/reconcile", review(preview), "different-review").status_code == 409
    # Fresh approval, prerequisite-ordered residual work and authored verification.
    new_orders = work(client, after)
    done = set()
    pending = [(o, s) for o in new_orders for s in o["steps"] if s["operation"] != "verify_target"]
    while pending:
        ready = next(((o, s) for o, s in pending if set(s["depends_on"]) <= done), None)
        assert ready
        record(client, *ready); done.add(ready[1]["id"]); pending.remove(ready)
    client = TestClient(create_app(path))
    for order in new_orders:
        step = next(s for s in order["steps"] if s["operation"] == "verify_target")
        assert post(client, f"/work-orders/{order['id']}/verification", {"outcome": "pass", "checks": step["required_checks"], "evidence_ref": "synthetic:automated-residual-verification"}).status_code == 200
    saved = client.get(f"/api/v1/plans/{p['id']}").json()
    assert saved["status"] == "paused"
    assert {s["id"] for o in saved["work_orders"] for s in o["steps"] if s["status"] == "done"} == {s["id"] for s in spent}
    report = client.get(f"/api/v1/plans/{after['id']}/report").json()
    assert {p["id"], after["id"]} <= {h["id"] for h in report["history"]}
    assert any(e["action"] == "simulation_reconciliation_reviewed" for e in report["audit_events"])
    assert report["physical_verified_repairs"] == 0
    assert client.get("/api/v1/components").json() == physical


def test_reconciliation_review_guards_and_crash_retry(env, monkeypatch):
    app, client, _ = env
    p, _, _, _, preview = interrupted(client)
    route = f"/plans/{p['id']}/reconcile"
    assert post(client, route, {**review(preview), "reviewed": False}).status_code == 422
    assert post(client, route, {**review(preview), "source_state_hash": "0" * 64}).status_code == 409
    original = workflow.calculate
    monkeypatch.setattr(workflow, "calculate", lambda *a, **k: (_ for _ in ()).throw(ValueError("test solve interruption")))
    response = post(client, route, review(preview), "retry-after-failure")
    assert response.status_code == 422
    with app.state.db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM recovery_reconciliations").fetchone()[0] == 1
    monkeypatch.setattr(workflow, "calculate", original)
    resumed = reconcile(client, p, preview, "retry-after-failure")
    assert resumed["status"] == "validated"


def test_competing_reconciliation_requests_create_one_continuation(env):
    app, client, _ = env
    p, _, _, _, preview = interrupted(client)
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda key: post(client, f"/plans/{p['id']}/reconcile", review(preview), key), ["review-a", "review-b"]))
    assert sorted(r.status_code for r in responses) == [200, 409]
    with app.state.db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM recovery_reconciliations").fetchone()[0] == 1


def test_continuation_tampering_and_budget_override_fail_closed(env):
    app, client, _ = env
    p, _, _, _, preview = interrupted(client)
    child = reconcile(client, p, preview)
    assert post(client, "/plans", {"context_id": child["context_id"], "budget_paise": 1000000}).status_code == 409
    with app.state.db.connect() as c:
        row = c.execute("SELECT id,data FROM recovery_reconciliations").fetchone()
        value = json.loads(row["data"]); value["consumed"]["cost_paise"] = 0
        c.execute("UPDATE recovery_reconciliations SET data=? WHERE id=?", (json.dumps(value), row["id"]))
        c.commit()
    assert decision(client, child).status_code == 409


def test_unused_looser_plan_cannot_expand_executed_resource_limits(env):
    _, client, _ = env
    unused = plan(client, budget_paise=1000000, time_minutes=1000)
    p, _, _, _, preview = interrupted(client)
    assert preview["original_limits"] == {"budget_paise": 250000, "time_minutes": 330}
    response = client.get(f"/api/v1/plans/{unused['id']}/reconciliation-preview")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXECUTION_PLAN_REQUIRED"


def test_repeated_continuation_preserves_ancestor_verification_and_spend(env):
    _, client, _ = env
    p, _, _, _, preview = interrupted(client, "installed")
    child = reconcile(client, p, preview)
    items = work(client, child)
    order = items[0]
    preparation = next(s for s in order["steps"] if s["operation"] == "prepare_target")
    record(client, order, preparation)
    failed = child["result"]["allocations"][0]["storage_component_id"]
    assert post(client, f"/plans/{child['id']}/failures", {"component_id": failed}).status_code == 409
    next_preview = client.get(f"/api/v1/plans/{child['id']}/reconciliation-preview").json()
    assert set(next_preview["verification_required_asset_ids"]) >= set(preview["verification_required_asset_ids"])
    assert next_preview["consumed"]["cost_paise"] == preview["consumed"]["cost_paise"] + preparation["cost_paise"]
    final = reconcile(client, child, next_preview, "second-reviewed-continuation")
    selected = {a["target_asset_id"] for a in final["result"]["allocations"]}
    verifies = {s["asset_id"] for s in final["result"]["operations"] if s["operation"] == "verify_target"}
    assert selected <= verifies
    report = client.get(f"/api/v1/plans/{final['id']}/report").json()
    assert {p["id"], child["id"], final["id"]} <= {h["id"] for h in report["history"]}


def test_each_failed_or_inconclusive_verification_attempt_is_charged(env):
    _, client, _ = env
    p = plan(client, budget_paise=500000, time_minutes=800)
    items = work(client, p)
    complete_ready_steps(client, items)
    order = items[0]
    verify = next(s for s in order["steps"] if s["operation"] == "verify_target")
    for outcome in ("fail", "inconclusive"):
        response = post(client, f"/work-orders/{order['id']}/verification", {"outcome": outcome, "checks": [], "evidence_ref": "synthetic:automated-attempt:" + outcome})
        assert response.status_code == 200, response.text
    failed = p["result"]["allocations"][0]["storage_component_id"]
    assert post(client, f"/plans/{p['id']}/failures", {"component_id": failed}).status_code == 409
    preview = client.get(f"/api/v1/plans/{p['id']}/reconciliation-preview").json()
    operations = [s for s in p["result"]["operations"] if s["operation"] != "verify_target"]
    assert preview["consumed"]["cost_paise"] == sum(s["cost_paise"] for s in operations) + 2 * verify["cost_paise"]
    assert len([s for s in preview["consumed_operations"] if s["operation"] == "verify_target"]) == 2


def test_verification_retry_cannot_exceed_exact_plan_resource_boundary(env):
    _, client, _ = env
    p = plan(client, budget_paise=215000, time_minutes=299)
    assert p["result"]["totals"]["technician_minutes"] == 299
    items = work(client, p)
    complete_ready_steps(client, items)
    order = items[0]
    route = f"/work-orders/{order['id']}/verification"
    body = {"outcome": "fail", "checks": [], "evidence_ref": "synthetic:exact-boundary-attempt"}
    assert post(client, route, body).status_code == 200
    result = post(client, route, body)
    assert result.status_code == 409 and result.json()["error"]["code"] == "VERIFICATION_RESOURCES_EXHAUSTED"
    saved = client.get(f"/api/v1/plans/{p['id']}").json()
    assert len(saved["work_orders"][0]["verifications"]) == 1
