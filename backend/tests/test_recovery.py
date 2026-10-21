"""Isolated lifecycle acceptance tests; no access to the user's normal database."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from revivegraph.db import Database, SCHEMA
from revivegraph.main import create_app
from revivegraph.imports import dump

FIXTURE = Path(__file__).resolve().parents[2] / "datasets/synthetic-v1"


@pytest.fixture
def env(tmp_path):
    path = tmp_path / "recovery.sqlite3"
    app = create_app(path)
    client = TestClient(app)
    reg = post(client, "/fixture-registrations", {}).json()["id"]
    batch = client.post("/api/v1/imports/preview", data={"registration_id": reg}, files={
        "computers_file": ("computers.csv", (FIXTURE / "computers.csv").read_bytes()),
        "components_file": ("components.csv", (FIXTURE / "components.csv").read_bytes())},
        headers=headers("preview")).json()
    response = post(client, f"/imports/{batch['batch_id']}/commit", {"preview_hash": batch["preview_hash"], "expected_revision": 0})
    assert response.status_code == 200, response.text
    return app, client, path


def headers(key):
    return {"X-Actor-ID": "test-human", "Idempotency-Key": key}


def post(client, path, data, key=None):
    import uuid
    return client.post("/api/v1" + path, json=data, headers=headers(key or uuid.uuid4().hex))


def plan(client, context="demo", **kwargs):
    response = post(client, "/plans", {"context_id": context, **kwargs})
    assert response.status_code == 200, response.text
    return response.json()


def decision(client, p, value="approve", key=None):
    return post(client, f"/plans/{p['id']}/decision", {"input_hash": p["input_hash"], "decision": value}, key)


def allocated_ids(p):
    return [x for a in p["result"]["allocations"] for x in a["ram_component_ids"] + [a["storage_component_id"]]]


def work(client, p):
    assert decision(client, p).status_code == 200
    response = post(client, f"/plans/{p['id']}/work-orders", {})
    assert response.status_code == 200, response.text
    return response.json()["items"]


def complete_ready_steps(client, items):
    completed = set()
    pending = [(o, s) for o in items for s in o["steps"] if s["operation"] != "verify_target"]
    while pending:
        ready = next(((o, s) for o, s in pending if set(s["depends_on"]) <= completed), None)
        assert ready, "Dependency cycle in generated work"
        order, step = ready
        response = post(client, f"/work-orders/{order['id']}/steps/{step['id']}", {
            "checks": step["required_checks"], "evidence_ref": f"synthetic:test-step:{step['id']}"})
        assert response.status_code == 200, response.text
        completed.add(step["id"])
        pending.remove(ready)


def test_solve_failure_history_stale_approval_no_physical_writes(env):
    app, client, _ = env
    before = client.get("/api/v1/components").json()
    p = plan(client)
    assert p["validation"]["valid"] and p["result"]["totals"]["usable_final"] > 0
    assert post(client, f"/plans/{p['id']}/work-orders", {}).status_code == 409
    locations = {x["component_id"]: x["location_asset_id"] for x in before["items"]}
    donor = next(x for a in p["result"]["allocations"] for x in a["ram_component_ids"] + [a["storage_component_id"]] if locations[x] and locations[x] != a["target_asset_id"])
    revised = post(client, f"/plans/{p['id']}/failures", {"component_id": donor}, "failure")
    assert revised.status_code == 200, revised.text
    revised = revised.json()
    assert donor not in allocated_ids(revised) and revised["parent_plan_id"] == p["id"]
    assert revised["comparison"]["before_totals"] == p["result"]["totals"]
    assert post(client, f"/plans/{p['id']}/failures", {"component_id": donor}, "failure").json()["id"] == revised["id"]
    original = client.get(f"/api/v1/plans/{p['id']}").json()
    assert original["result"] == p["result"] and original["status"] == "stale"
    assert decision(client, p).status_code == 409
    assert client.get("/api/v1/components").json() == before


def test_approval_concurrency_atomic_reservations_idempotency(env):
    app, client, _ = env
    p1, p2 = plan(client), plan(client)
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda p: decision(client, p), [p1, p2]))
    assert sorted(r.status_code for r in responses) == [200, 409]
    winner = p1 if responses[0].status_code == 200 else p2
    with app.state.db.connect() as c:
        rows = c.execute("SELECT * FROM recovery_reservations").fetchall()
        assert {r["plan_id"] for r in rows} == {winner["id"]}
        assert len(rows) == len(allocated_ids(winner)) + len(winner["result"]["allocations"])
        assert c.execute("SELECT count(*) FROM recovery_decisions").fetchone()[0] == 1
    p3 = plan(client, "independent")
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda _: decision(client, p3, key="same-approval"), range(2)))
    assert all(r.status_code == 200 for r in responses)
    assert decision(client, p3, "reject", "same-approval").status_code == 409
    assert plan_response(client, "independent").status_code == 409


def plan_response(client, context):
    return post(client, "/plans", {"context_id": context})


def test_rejection_no_reservations_and_tamper_refused(env):
    app, client, _ = env
    p = plan(client)
    assert decision(client, p, "reject").status_code == 200
    assert post(client, f"/plans/{p['id']}/work-orders", {}).status_code == 409
    with app.state.db.connect() as c:
        assert c.execute("SELECT count(*) FROM recovery_reservations").fetchone()[0] == 0
    p = plan(client)
    with app.state.db.connect() as c:
        row = c.execute("SELECT data FROM recovery_plans WHERE id=?", (p["id"],)).fetchone()
        data = json.loads(row[0]); data["result"]["totals"]["cost_paise"] += 1
        c.execute("UPDATE recovery_plans SET data=? WHERE id=?", (dump(data), p["id"])); c.commit()
    assert decision(client, p).json()["error"]["code"] == "PLAN_INVALID"


def test_order_dependencies_retry_restart_verification_and_report(env):
    app, client, path = env
    p = plan(client)
    items = work(client, p)
    assert post(client, f"/plans/{p['id']}/work-orders", {}, "orders-retry").json()["items"] == items
    # New retry key is bound even if orders already existed.
    assert post(client, "/plans", {}, "orders-retry").status_code == 409
    target = items[0]
    verify_step = next(s for s in target["steps"] if s["operation"] == "verify_target")
    response = post(client, f"/work-orders/{target['id']}/verification", {"outcome": "pass", "checks": verify_step["required_checks"], "evidence_ref": "synthetic:premature"})
    assert response.status_code == 409
    complete_ready_steps(client, items)
    restarted = TestClient(create_app(path))
    persisted = restarted.get(f"/api/v1/plans/{p['id']}").json()
    assert all(s["status"] == "done" for o in persisted["work_orders"] for s in o["steps"] if s["operation"] != "verify_target")
    assert post(restarted, f"/work-orders/{target['id']}/verification", {"outcome": "pass", "checks": [], "evidence_ref": "synthetic:missing"}).status_code == 422
    first = post(restarted, f"/work-orders/{target['id']}/verification", {"outcome": "pass", "checks": verify_step["required_checks"], "evidence_ref": "synthetic:checked"}, "verify-retry")
    assert first.status_code == 200, first.text
    assert post(restarted, f"/work-orders/{target['id']}/verification", {"outcome": "pass", "checks": verify_step["required_checks"], "evidence_ref": "synthetic:checked"}, "verify-retry").json() == first.json()
    summary = restarted.get("/api/v1/state").json()["recovery"]
    assert summary["simulated_passes"] == 1 and summary["physical_passes"] == 0
    report = restarted.get(f"/api/v1/plans/{p['id']}/report").json()
    assert report["plan"]["snapshot"]["operation_costs"]["provenance"].startswith("synthetic:")
    assert report["plan"]["decisions"] and report["audit_events"] and report["physical_verified_repairs"] == 0
    assert restarted.get("/api/v1/state").json()["counts"]["usable"] == 0


@pytest.mark.parametrize("outcome", ["fail", "inconclusive"])
def test_failed_inconclusive_not_passes(env, outcome):
    _, client, _ = env
    p = plan(client)
    items = work(client, p)
    complete_ready_steps(client, items)
    response = post(client, f"/work-orders/{items[0]['id']}/verification", {"outcome": outcome, "checks": [], "evidence_ref": "synthetic:unresolved"})
    assert response.status_code == 200
    assert client.get("/api/v1/state").json()["recovery"]["simulated_passes"] == 0


def test_post_start_failure_pauses_preserves_progress_and_locations(env):
    app, client, _ = env
    p = plan(client)
    items = work(client, p)
    first = next(s for s in items[0]["steps"] if not s["depends_on"])
    data = {"checks": first["required_checks"], "evidence_ref": "synthetic:started"}
    path = f"/work-orders/{items[0]['id']}/steps/{first['id']}"
    assert post(client, path, data, "step-retry").status_code == 200
    assert post(client, path, data, "step-retry").status_code == 200
    assert post(client, path, {**data, "evidence_ref": "different"}, "step-retry").status_code == 409
    # Record a real simulated removal, so preserving scenario locations is tested.
    ready_removal = next(s for s in items[0]["steps"] if s["operation"].startswith("remove_") and set(s["depends_on"]) <= {first["id"]})
    assert post(client, f"/work-orders/{items[0]['id']}/steps/{ready_removal['id']}", {
        "checks": ready_removal["required_checks"], "evidence_ref": "synthetic:removed"}).status_code == 200
    with app.state.db.connect() as c:
        location_overlay = c.execute("SELECT locations FROM recovery_contexts").fetchone()[0]
        assert json.loads(location_overlay)[ready_removal["component_id"]] is None
    response = post(client, f"/plans/{p['id']}/failures", {"component_id": allocated_ids(p)[0]}, "started-failure")
    assert response.status_code == 409 and response.json()["error"]["code"] == "RECONCILIATION_REQUIRED"
    assert post(client, f"/plans/{p['id']}/failures", {"component_id": allocated_ids(p)[0]}, "started-failure").status_code == 409
    current = client.get(f"/api/v1/plans/{p['id']}").json()
    assert current["status"] == "paused" and all(o["status"] == "paused" for o in current["work_orders"])
    assert next(s for s in current["work_orders"][0]["steps"] if s["id"] == first["id"])["status"] == "done"
    assert plan_response(client, "demo").status_code == 409
    with app.state.db.connect() as c:
        assert c.execute("SELECT locations FROM recovery_contexts").fetchone()[0] == location_overlay
    assert client.get("/api/v1/components").json()["items"][0]["location_asset_id"] == p["snapshot"]["components"][0]["location_asset_id"]


def test_inventory_revision_change_refuses_approval(env):
    app, client, _ = env
    p = plan(client)
    with app.state.db.connect() as c:
        c.execute("UPDATE fleets SET revision=revision+1"); c.commit()
    assert decision(client, p).status_code == 409
    assert client.get(f"/api/v1/plans/{p['id']}").json()["status"] == "stale"


def test_safe_v1_migration(tmp_path):
    import sqlite3
    path = tmp_path / "old.sqlite3"
    c = sqlite3.connect(path)
    c.executescript(SCHEMA + "\nPRAGMA user_version=1;")
    c.execute("INSERT INTO audit_events(action,entity_id,actor,occurred_at,data) VALUES ('old','old','old','old','{}')"); c.commit(); c.close()
    db = Database(path)
    with db.connect() as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == 2
        assert c.execute("SELECT action FROM audit_events").fetchone()[0] == "old"
        assert c.execute("SELECT count(*) FROM recovery_plans").fetchone()[0] == 0


def test_failure_crash_retry_does_not_duplicate_overlay_or_plan(env, monkeypatch):
    import revivegraph.optimizer as engine
    app, client, _ = env
    p = plan(client)
    original = engine.solve
    def crash(*args, **kwargs):
        raise RuntimeError("simulated solver interruption after failure commit")
    monkeypatch.setattr(engine, "solve", crash)
    with pytest.raises(RuntimeError, match="interruption"):
        post(client, f"/plans/{p['id']}/failures", {"component_id": allocated_ids(p)[0]}, "crash-failure")
    monkeypatch.setattr(engine, "solve", original)
    retry = post(client, f"/plans/{p['id']}/failures", {"component_id": allocated_ids(p)[0]}, "crash-failure")
    assert retry.status_code == 200, retry.text
    again = post(client, f"/plans/{p['id']}/failures", {"component_id": allocated_ids(p)[0]}, "crash-failure")
    assert again.json()["id"] == retry.json()["id"]
    with app.state.db.connect() as c:
        assert c.execute("SELECT revision FROM recovery_contexts").fetchone()[0] == 1
        assert c.execute("SELECT count(*) FROM recovery_failures").fetchone()[0] == 1
        assert c.execute("SELECT count(*) FROM recovery_plans").fetchone()[0] == 2


@pytest.mark.parametrize("race", ["inventory", "approval"])
def test_change_during_solve_refuses_persistence(env, monkeypatch, race):
    import revivegraph.optimizer as engine
    app, client, _ = env
    first = plan(client)
    original = engine.solve
    def change(*args):
        if race == "inventory":
            with app.state.db.connect() as c:
                c.execute("UPDATE fleets SET revision=revision+1"); c.commit()
        else:
            assert decision(client, first).status_code == 200
        return original(*args)
    monkeypatch.setattr(engine, "solve", change)
    response = plan_response(client, "demo")
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == ("STALE_SNAPSHOT" if race == "inventory" else "CONTEXT_RESERVED")
    with app.state.db.connect() as c:
        assert c.execute("SELECT count(*) FROM recovery_plans").fetchone()[0] == 1


def test_failure_no_spare_yields_proven_zero_with_no_fake_orders(env):
    app, client, _ = env
    # A deliberately restricted test database, not edits to synthetic-v1 files:
    # PC05 can use only its retained RAM05 and stock SSD06.
    with app.state.db.connect() as c:
        for r in c.execute("SELECT * FROM computers").fetchall():
            data = json.loads(r["data"])
            data["base_health"] = "healthy" if r["id"] == "RG-PC-05" else "faulty"
            c.execute("UPDATE computers SET data=? WHERE id=?", (dump(data), r["id"]))
        for r in c.execute("SELECT * FROM components").fetchall():
            data = json.loads(r["data"])
            data["health"] = "healthy" if r["id"] in ("RG-RAM-05", "RG-SSD-06") else "faulty"
            c.execute("UPDATE components SET data=? WHERE id=?", (dump(data), r["id"]))
        c.execute("UPDATE fleets SET revision=revision+1"); c.commit()
    p = plan(client)
    assert p["result"]["totals"]["usable_final"] == 1
    response = post(client, f"/plans/{p['id']}/failures", {"component_id": "RG-SSD-06"})
    assert response.status_code == 200, response.text
    p = response.json()
    assert p["result"]["solver"]["status"] == "OPTIMAL"
    assert p["result"]["totals"]["usable_final"] == 0
    assert work(client, p) == []
    assert client.get("/api/v1/state").json()["recovery"]["physical_passes"] == 0
