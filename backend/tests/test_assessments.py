"""Explicit synthetic authoring only; isolated databases and no hardware claims."""
import json
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from revivegraph.main import create_app
from test_recovery import env, plan, post, work


def body(client, kind="component", subject="RG-RAM-04", **changes):
    current = client.get(f"/api/v1/assessments/{kind}/{subject}").json()
    return {"health": "unknown", "expected_revision": client.get("/api/v1/state").json()["revision"],
            "expected_assessment_id": current["current_assessment_id"],
            "source": "test-authored synthetic scenario", "evidence_ref": "synthetic:test-authoring",
            "simulation_only": True, **changes}


def test_append_only_authoring_invalidates_plan_and_survives_restart(env):
    app, client, path = env
    saved = plan(client)
    with app.state.db.connect() as c:
        original = dict(c.execute("SELECT * FROM components WHERE id='RG-RAM-04'").fetchone())
    request = body(client, health="healthy")
    result = post(client, "/assessments/component/RG-RAM-04", request, "author-once")
    assert result.status_code == 200, result.text
    value = result.json()
    assert value["assessment"]["human_reviewed"] is False
    assert value["assessment"]["human_reviewer"] is None
    assert value["assessment"]["recorded_precision"] == "datetime"
    assert value["assessment"]["supplied_author_label"] == "test-human"
    assert client.get(f"/api/v1/plans/{saved['id']}").json()["status"] == "stale"
    assert post(client, "/assessments/component/RG-RAM-04", request, "author-once").json() == value
    client = TestClient(create_app(path))
    part = client.get("/api/v1/components/RG-RAM-04").json()
    assert part["health"] == "healthy"
    history = client.get("/api/v1/assessments/component/RG-RAM-04").json()
    assert len(history["items"]) == 2
    assert history["current_assessment_id"] == value["id"]
    assert history["items"][1]["parent_assessment_id"] == original["assessment_id"]
    with app.state.db.connect() as c:
        assert c.execute("SELECT data FROM components WHERE id='RG-RAM-04'").fetchone()[0] == original["data"]
    physical = client.get("/api/v1/compatibility?target_asset_id=RG-PC-04&mode=physical").json()
    assert all(not p["eligibility"]["eligible"] for p in physical["items"])


def test_unknown_assertion_still_blocks_and_competing_authors_cas(env):
    _, client, _ = env
    request = body(client, subject="RG-RAM-01")
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda key: post(client, "/assessments/component/RG-RAM-01", request, key), ["author-a", "author-b"]))
    assert sorted(r.status_code for r in responses) == [200, 409]
    edge = next(e for e in client.get("/api/v1/compatibility?target_asset_id=RG-PC-01").json()["items"] if e["component_id"] == "RG-RAM-01")
    assert edge["hardware"]["decision"] == "compatible"
    assert edge["eligibility"]["eligible"] is False


def test_guard_approved_fleet_and_invalid_claims(env):
    _, client, _ = env
    request = body(client)
    assert post(client, "/assessments/component/RG-RAM-04", {**request, "human_reviewed": True}).status_code == 422
    assert post(client, "/assessments/component/RG-RAM-04", {**request, "simulation_only": False}).status_code == 422
    assert post(client, "/assessments/component/RG-RAM-04", {**request, "evidence_ref": "physical:fake"}).status_code == 422
    assert post(client, "/assessments/component/RG-RAM-04", {**request, "expected_assessment_id": "wrong"}).status_code == 409
    work(client, plan(client))
    assert post(client, "/assessments/component/RG-RAM-04", request).status_code == 409


def test_computer_base_assertion_is_effective_without_import_rewrite(env):
    app, client, _ = env
    request = body(client, "computer", "RG-PC-04", health="faulty")
    response = post(client, "/assessments/computer/RG-PC-04", request)
    assert response.status_code == 200, response.text
    computer = client.get("/api/v1/computers/RG-PC-04").json()
    assert computer["base_health"] == "faulty"
    assert computer["usability"]["classification"] == "unusable"
    with app.state.db.connect() as c:
        original = json.loads(c.execute("SELECT data FROM computers WHERE id='RG-PC-04'").fetchone()[0])
        assert original["base_health"] != "faulty"
