"""Fleet-scoped audit queries are read-only and never inspect normal inventory."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from revivegraph.main import create_app

FIXTURE = Path(__file__).resolve().parents[2] / "datasets" / "synthetic-v1"
HEADERS = {"X-Actor-ID": "audit-test", "Idempotency-Key": "audit-import"}


@pytest.fixture
def env(tmp_path):
    app = create_app(tmp_path / "audit.sqlite3")
    client = TestClient(app)
    registration = client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).json()["id"]
    batch = client.post("/api/v1/imports/preview", data={"registration_id": registration}, files={
        "computers_file": ("computers.csv", (FIXTURE / "computers.csv").read_bytes()),
        "components_file": ("components.csv", (FIXTURE / "components.csv").read_bytes())}, headers=HEADERS).json()
    assert client.post(f"/api/v1/imports/{batch['batch_id']}/commit", json={
        "preview_hash": batch["preview_hash"], "expected_revision": 0}, headers=HEADERS).status_code == 200
    with app.state.db.connect() as c:
        # A second fleet sharing the immutable registration must not leak events.
        c.execute("INSERT INTO fleets VALUES ('OTHER-FLEET','RG-INST-01','simulation',?,0)", (registration,))
        c.execute("INSERT INTO recovery_plans VALUES ('other-plan','OTHER-FLEET','demo',0,0,'validated','{}','2026-10-20T00:00:00+00:00')")
        c.execute("INSERT INTO audit_events(action,entity_id,actor,occurred_at,data) VALUES ('plan_validated','other-plan','other-actor','2026-10-20T00:00:00+00:00','{\"private\":true}')")
        for n, action in enumerate(("evidence_inspected", "evidence_inspected", "component_selected")):
            c.execute("INSERT INTO audit_events(action,entity_id,actor,occurred_at,data) VALUES (?,?,?,?,?)",
                      (action, "RG-PC-01" if n < 2 else "RG-RAM-01", "audit-test", "2026-10-20T00:00:00+00:00", json.dumps({"sequence": n})))
        c.commit()
    return app, client


def test_audit_scope_pagination_and_json(env):
    _, client = env
    response = client.get("/api/v1/audit-events?limit=2")
    assert response.status_code == 200
    first = response.json()
    assert first["total"] == 4 and len(first["items"]) == 2
    assert first["items"][0]["action"] == "component_selected"
    assert first["items"][0]["data"] == {"sequence": 2}
    second = client.get("/api/v1/audit-events?offset=2&limit=2").json()
    assert len(second["items"]) == 2
    assert {r["id"] for r in first["items"]}.isdisjoint({r["id"] for r in second["items"]})
    all_items = first["items"] + second["items"]
    assert [r["id"] for r in all_items] == sorted((r["id"] for r in all_items), reverse=True)
    assert all(r["actor"] != "other-actor" for r in all_items)


def test_audit_exact_action_filter_and_unknown_scope(env):
    _, client = env
    result = client.get("/api/v1/audit-events?action=evidence_inspected").json()
    assert result["total"] == 2 and all(r["action"] == "evidence_inspected" for r in result["items"])
    assert client.get("/api/v1/audit-events?fleet_id=DOES-NOT-EXIST").json()["total"] == 0
    assert client.get("/api/v1/audit-events?action=%27%20OR%201=1--").json()["items"] == []
    other = client.get("/api/v1/audit-events?fleet_id=OTHER-FLEET").json()
    assert other["total"] == 1 and other["items"][0]["actor"] == "other-actor"


def test_audit_reads_do_not_write(env):
    app, client = env
    def snapshot():
        with app.state.db.connect() as c:
            return list(c.iterdump())
    before = snapshot()
    for query in ("", "?offset=1&limit=1", "?action=inventory_imported", "?fleet_id=OTHER-FLEET"):
        assert client.get("/api/v1/audit-events" + query).status_code == 200
    assert snapshot() == before


@pytest.mark.parametrize("query", ["?limit=0", "?limit=201", "?offset=-1"])
def test_audit_bounds(env, query):
    _, client = env
    assert client.get("/api/v1/audit-events" + query).status_code == 422
