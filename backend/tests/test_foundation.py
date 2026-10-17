import csv
import io
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from revivegraph.domain import eligibility, part_compatibility, ram_configuration
from revivegraph.main import create_app

FIXTURE = Path(__file__).resolve().parents[2] / "datasets" / "synthetic-v1"
HEADERS = {"X-Actor-ID": "test-operator", "Idempotency-Key": "test-key"}


@pytest.fixture
def context(tmp_path):
    app = create_app(tmp_path / "test.sqlite3", FIXTURE)
    client = TestClient(app)
    registration = client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS)
    assert registration.status_code == 200
    return app, client, registration.json()["id"]


def csv_text(name):
    return (FIXTURE / name).read_text(encoding="utf-8")


def edit_csv(name, edit):
    rows = list(csv.DictReader(io.StringIO(csv_text(name))))
    edit(rows)
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def preview(client, registration, computers=None, components=None, mode="simulation"):
    return client.post("/api/v1/imports/preview", data={"registration_id": registration, "fleet_id": "RG-DEMO-12", "mode": mode},
                       files={"computers_file": ("computers.csv", computers or (FIXTURE / "computers.csv").read_bytes()),
                              "components_file": ("components.csv", components or (FIXTURE / "components.csv").read_bytes())}, headers=HEADERS)


def commit(client, batch, key="commit-key"):
    return client.post(f"/api/v1/imports/{batch['batch_id']}/commit", json={"preview_hash": batch["preview_hash"], "expected_revision": batch["expected_revision"]}, headers={**HEADERS, "Idempotency-Key": key})


def imported(context):
    app, client, registration = context
    batch = preview(client, registration).json()
    result = commit(client, batch)
    assert result.status_code == 200, result.text
    return app, client, registration


def test_preview_has_no_inventory_or_assessment_writes(context):
    app, client, registration = context
    response = preview(client, registration)
    assert response.status_code == 200 and response.json()["valid"]
    assert response.json()["counts"] == {"computers": 12, "components": 31}
    assert client.get("/api/v1/state").json()["counts"]["computers"] == 0
    with app.state.db.connect() as connection:
        for table in ("fleets", "computers", "components", "assessments", "audit_events"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_import_retry_and_evidence_precision(context):
    _, client, registration = context
    batch = preview(client, registration).json()
    first = commit(client, batch)
    assert first.status_code == 200 and first.json()["revision"] == 1
    assert commit(client, batch).json()["revision"] == 1
    assert commit(client, batch, "different-key").json()["revision"] == 1
    assert preview(client, registration).json()["committed"]
    counts = client.get("/api/v1/state").json()["counts"]
    assert {k: counts[k] for k in ("computers", "components", "usable", "unusable", "unknown")} == {"computers": 12, "components": 31, "usable": 0, "unusable": 8, "unknown": 4}
    part = client.get("/api/v1/components/RG-RAM-07").json()
    evidence = part["assessment"]
    assert evidence["recorded_value"] == "2026-10-16" and evidence["recorded_precision"] == "date"
    assert evidence["assessment_kind"] == "authored_synthetic_assertion"
    assert evidence["imported_at"].endswith("+00:00") and evidence["imported_by"] == "test-operator"
    assert evidence["human_reviewer"] is None and evidence["human_reviewed"] is False
    assert part["origin_asset_id"] == part["location_asset_id"] == "RG-PC-11"
    base = client.get("/api/v1/computers/RG-PC-01").json()["assessment"]
    assert base["evidence_ref"] is None


@pytest.mark.parametrize("kind,field,value,code", [
    ("computers", "board_profile_id", "MISSING", "PROFILE_NOT_REGISTERED"),
    ("components", "location_asset_id", "MISSING", "LOCATION_NOT_IN_BATCH"),
    ("components", "owner_id", "OTHER", "OWNER_MISMATCH"),
    ("components", "capacity_gib", "-1", "POSITIVE_INTEGER"),
    ("components", "component_id", "RG-RAM-02", "DUPLICATE_ID"),
    ("computers", "asset_id", "RG-PC-02", "DUPLICATE_ID"),
])
def test_invalid_rows_cannot_commit(context, kind, field, value, code):
    _, client, registration = context
    changed = edit_csv(kind + ".csv", lambda rows: rows[0].update({field: value}))
    response = preview(client, registration, **{kind: changed})
    assert response.status_code == 200
    batch = response.json()
    assert not batch["valid"]
    expected_row = 3 if code == "DUPLICATE_ID" else 2
    assert any(error["code"] == code and error["row"] == expected_row and error["field"] == field for error in batch["errors"])
    assert commit(client, batch).status_code == 422
    assert client.get("/api/v1/state").json()["counts"]["components"] == 0


def test_atomic_insert_failure_and_safe_retry(context):
    app, client, registration = context
    batch = preview(client, registration).json()
    with app.state.db.connect() as connection:
        connection.execute("CREATE TRIGGER injected_failure BEFORE INSERT ON components WHEN NEW.id='RG-RAM-02' BEGIN SELECT RAISE(ABORT,'injected test failure'); END")
        connection.commit()
    failed = commit(client, batch)
    assert failed.status_code == 409 and failed.json()["error"]["code"] == "IMPORT_CONFLICT"
    with app.state.db.connect() as connection:
        for table in ("fleets", "computers", "components", "assessments", "audit_events", "commit_keys"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert connection.execute("SELECT committed_revision FROM batches").fetchone()[0] is None
        connection.execute("DROP TRIGGER injected_failure")
        connection.commit()
    assert commit(client, batch).status_code == 200


def test_database_reopen_persists_inventory_and_committed_retry(context):
    app, client, registration = context
    batch = preview(client, registration).json()
    assert commit(client, batch).status_code == 200
    restarted = TestClient(create_app(app.state.db.path, FIXTURE))
    assert restarted.get("/api/v1/state").json()["counts"]["components"] == 31
    assert restarted.get("/api/v1/fixture-registrations").json()["items"][0]["id"] == registration
    assert restarted.get("/api/v1/components/RG-RAM-07").json()["assessment"]["recorded_precision"] == "date"
    assert commit(restarted, batch).json()["revision"] == 1


def test_changed_csv_does_not_inherit_historical_context(context):
    _, client, registration = context
    changed = edit_csv("components.csv", lambda rows: rows[0].update({"evidence_ref": "NEW-AUTHORED-ASSERTION"}))
    batch = preview(client, registration, components=changed).json()
    assert commit(client, batch).status_code == 200
    evidence = client.get("/api/v1/components/RG-RAM-01").json()["assessment"]
    assert evidence["recorded_value"] is None and evidence["recorded_precision"] == "unknown"
    assert evidence["supplied_author_label"] is None and evidence["source"] is None


def test_registration_hash_conflict_and_missing_sidecar(tmp_path):
    fixture = tmp_path / "fixture"
    shutil.copytree(FIXTURE, fixture)
    client = TestClient(create_app(tmp_path / "test.sqlite3", fixture))
    first = client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS)
    assert first.status_code == 200
    assert client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).json()["id"] == first.json()["id"]
    costs = json.loads((fixture / "operation_costs.json").read_text())
    costs["operations"]["prepare_target"]["cost_paise"] += 1
    (fixture / "operation_costs.json").write_text(json.dumps(costs))
    assert client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).status_code == 409
    (fixture / "board_profiles.json").unlink()
    assert client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).status_code == 422


def test_compatibility_separates_health_and_physical_eligibility(context):
    _, client, _ = imported(context)
    rows = client.get("/api/v1/compatibility", params={"target_asset_id": "RG-PC-04"}).json()["items"]
    unknown_health = next(p for p in rows if p["component_id"] == "RG-RAM-04")
    assert unknown_health["hardware"]["decision"] == "compatible" and not unknown_health["eligibility"]["eligible"]
    assert unknown_health["eligibility"]["reasons"][0]["code"] == "HEALTH_UNKNOWN"
    mismatch = client.get("/api/v1/compatibility", params={"target_asset_id": "RG-PC-06"}).json()["items"]
    assert next(p for p in mismatch if p["component_id"] == "RG-RAM-11")["hardware"]["decision"] == "incompatible"
    unknown = client.get("/api/v1/compatibility", params={"target_asset_id": "RG-PC-09"}).json()["items"]
    assert next(p for p in unknown if p["component_id"] == "RG-SSD-06")["hardware"]["decision"] == "unknown"
    physical = client.get("/api/v1/compatibility", params={"target_asset_id": "RG-PC-04", "mode": "physical"}).json()["items"]
    good = next(p for p in physical if p["component_id"] == "RG-RAM-07")
    assert good["hardware"]["decision"] == "compatible" and not good["eligibility"]["eligible"]
    assert "SYNTHETIC_PHYSICAL_EXCLUDED" in {r["code"] for r in good["eligibility"]["reasons"]}


def test_synthetic_import_into_physical_mode_is_rejected(context):
    _, client, registration = context
    batch = preview(client, registration, mode="physical").json()
    assert not batch["valid"] and any(e["code"] == "SYNTHETIC_PHYSICAL_EXCLUDED" for e in batch["errors"])


def test_existing_id_conflict_and_hash_mismatch(context):
    _, client, registration = imported(context)
    changed = edit_csv("components.csv", lambda rows: rows[0].update({"evidence_ref": "CHANGED"}))
    batch = preview(client, registration, components=changed).json()
    assert any(e["code"] == "EXISTING_ID" for e in batch["errors"])
    response = client.post(f"/api/v1/imports/{batch['batch_id']}/commit", json={"preview_hash": "wrong", "expected_revision": 1}, headers=HEADERS)
    assert response.status_code == 409


def test_stale_preview_can_be_refreshed(context):
    _, client, registration = context
    first = preview(client, registration).json()
    computers = edit_csv("computers.csv", lambda rows: [row.update({"asset_id": row["asset_id"].replace("RG-PC", "ALT-PC")}) for row in rows])
    components = edit_csv("components.csv", lambda rows: [row.update({"component_id": "ALT-" + row["component_id"], "location_asset_id": row["location_asset_id"].replace("RG-PC", "ALT-PC")}) for row in rows])
    second = preview(client, registration, computers, components).json()
    assert second["valid"]
    assert commit(client, first).status_code == 200
    assert commit(client, second, "second-key").json()["error"]["code"] == "STALE_PREVIEW"
    refreshed = preview(client, registration, computers, components).json()
    assert refreshed["expected_revision"] == 1
    assert commit(client, refreshed, "second-key").json()["revision"] == 2


def test_complete_configuration_slots_capacities_and_mixed_modules(context):
    _, client, _ = imported(context)
    body = {"target_asset_id": "RG-PC-04", "ram_component_ids": ["RG-RAM-07", "RG-RAM-15"], "storage_component_id": "RG-SSD-05"}
    check = client.post("/api/v1/compatibility/configuration", json=body).json()
    assert not check["eligible_configuration"] and check["ram"]["decision"] == "incompatible"
    body["target_asset_id"] = "RG-PC-02"
    body["ram_component_ids"] = ["RG-RAM-11", "RG-RAM-15"]
    check = client.post("/api/v1/compatibility/configuration", json=body).json()
    assert check["ram"]["decision"] == "incompatible"
    body["ram_component_ids"] = ["RG-RAM-07", "RG-RAM-15"]
    assert client.post("/api/v1/compatibility/configuration", json=body).json()["eligible_configuration"]
    body["ram_component_ids"] = ["RG-RAM-07", "RG-RAM-07"]
    assert client.post("/api/v1/compatibility/configuration", json=body).status_code == 422


def test_rule_failures_dominate_unknown_fields_and_ownership(context):
    _, client, _ = imported(context)
    target = client.get("/api/v1/computers/RG-PC-06").json()
    part = client.get("/api/v1/components/RG-RAM-11").json()
    part["voltage_mv"] = None
    assert part_compatibility(part, target["profile"])["decision"] == "incompatible"
    part["ram_generation"] = "DDR3"
    part["speed_mt_s"] = 1600
    part["capacity_gib"] = 16
    codes = {r["code"] for r in part_compatibility(part, target["profile"])["reasons"]}
    assert "RAM_PER_SLOT_CAPACITY" in codes
    part["owner_id"] = "OTHER"
    check = eligibility(part, target, "simulation", {"decision": "compatible"}, part["assessment"], reserved=True)
    assert {r["code"] for r in check["reasons"]} == {"OWNER_MISMATCH", "RESERVED"}


def test_preparation_allocations_are_not_served(context):
    _, client, _ = context
    assert client.get("/api/v1/bundled-fixture/scenarios.json").status_code == 404
    assert client.get("/api/v1/plans").status_code == 404
    assert client.get("/api/v1/state").json()["optimization"]["status"] == "Not calculated"


def test_unreviewed_physical_assertions_never_become_usable(context):
    _, client, registration = context
    computers = edit_csv("computers.csv", lambda rows: [row.update({"base_health": "healthy", "provenance": "physical:unreviewed-import-claim"}) for row in rows])
    components = edit_csv("components.csv", lambda rows: [row.update({"health": "healthy", "provenance": "physical:unreviewed-import-claim"}) for row in rows])
    batch = preview(client, registration, computers, components, mode="physical").json()
    assert batch["valid"]
    assert commit(client, batch).status_code == 200
    assert client.get("/api/v1/state").json()["counts"]["usable"] == 0
    evidence = client.get("/api/v1/computers/RG-PC-01").json()["assessment"]
    assert evidence["assessment_kind"] == "unreviewed_physical_assertion" and evidence["recorded_precision"] == "unknown"
    for mode in (None, "simulation", "physical"):
        params = {"target_asset_id": "RG-PC-01"}
        if mode:
            params["mode"] = mode
        check = client.get("/api/v1/compatibility", params=params).json()["items"][0]
        assert not check["eligibility"]["eligible"]
        assert "HUMAN_REVIEW_REQUIRED" in {r["code"] for r in check["eligibility"]["reasons"]}


def test_rule_version_pin_fails_closed_when_engine_changes(context, monkeypatch):
    app, client, registration = imported(context)
    assert client.get("/api/v1/fixture-registrations").json()["items"][0]["inspection_rule_version"] == "desktop-inspection-v1"
    monkeypatch.setattr("revivegraph.main.RULE_VERSION", "future-v2")
    response = client.get("/api/v1/computers")
    assert response.status_code == 409 and response.json()["error"]["code"] == "RULE_VERSION_MISMATCH"


@pytest.mark.parametrize("field,value,code", [("form_factor", "SODIMM", "RAM_FORM"), ("voltage_mv", 1500, "RAM_VOLTAGE"), ("ecc", True, "RAM_ECC"), ("buffered", True, "RAM_BUFFERED")])
def test_ram_decisive_fields(context, field, value, code):
    _, client, _ = imported(context)
    part = client.get("/api/v1/components/RG-RAM-07").json()
    profile = client.get("/api/v1/computers/RG-PC-04").json()["profile"]
    part[field] = value
    check = part_compatibility(part, profile)
    assert check["decision"] == "incompatible" and code in {r["code"] for r in check["reasons"]}
    part[field] = None
    assert part_compatibility(part, profile)["decision"] == "unknown"


def test_sata_known_disqualifier_dominates_unknown(context):
    _, client, _ = imported(context)
    part = client.get("/api/v1/components/RG-SSD-06").json()
    profile = client.get("/api/v1/computers/RG-PC-09").json()["profile"]
    assert part_compatibility(part, profile)["decision"] == "unknown"
    part["interface"] = "NVMe"
    check = part_compatibility(part, profile)
    assert check["decision"] == "incompatible" and "STORAGE_INTERFACE" in {r["code"] for r in check["reasons"]}


def test_actual_backend_process_restart(tmp_path):
    import os
    import socket
    import subprocess
    import sys
    import time
    import httpx

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "REVIVEGRAPH_DB": str(tmp_path / "restart.sqlite3")}
    command = [sys.executable, "-m", "uvicorn", "revivegraph.main:create_app", "--factory", "--app-dir", str(FIXTURE.parents[1] / "backend"), "--host", "127.0.0.1", "--port", str(port)]

    def start():
        process = subprocess.Popen(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        for _ in range(100):
            try:
                if httpx.get(base + "/api/v1/health", timeout=.2).status_code == 200:
                    return process
            except httpx.HTTPError:
                pass
            time.sleep(.05)
        process.terminate()
        process.wait(timeout=5)
        pytest.fail("Backend did not start for restart validation")

    process = start()
    try:
        client = httpx.Client(base_url=base, timeout=10)
        registration = client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).json()["id"]
        batch = preview(client, registration).json()
        assert commit(client, batch).status_code == 200
        process.terminate()
        process.wait(timeout=5)
        process = start()
        state = client.get("/api/v1/state").json()
        assert state["revision"] == 1 and state["counts"]["computers"] == 12 and state["counts"]["components"] == 31
        assert commit(client, batch).json()["revision"] == 1
        client.close()
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_concurrent_identical_commits_only_import_once(context):
    from concurrent.futures import ThreadPoolExecutor

    app, client, registration = context
    batch = preview(client, registration).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda key: commit(TestClient(app), batch, key), ("parallel-a", "parallel-b")))
    assert [response.status_code for response in results] == [200, 200]
    assert [response.json()["revision"] for response in results] == [1, 1]
    with app.state.db.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM assessments").fetchone()[0] == 43
        assert connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] == 1


def test_commit_key_and_stored_hash_conflicts_fail_closed(context):
    app, client, registration = context
    batch = preview(client, registration).json()
    with app.state.db.connect() as connection:
        row = connection.execute("SELECT payload FROM batches WHERE id=?", (batch["batch_id"],)).fetchone()
        original = row[0]
        payload = json.loads(original)
        payload["texts"]["computers.csv"] += "\n"
        connection.execute("UPDATE batches SET payload=? WHERE id=?", (json.dumps(payload), batch["batch_id"]))
        connection.commit()
    response = commit(client, batch)
    assert response.status_code == 409 and response.json()["error"]["code"] == "BATCH_CONTENT_CONFLICT"
    with app.state.db.connect() as connection:
        connection.execute("UPDATE batches SET payload=? WHERE id=?", (original, batch["batch_id"]))
        connection.commit()
    assert commit(client, batch).status_code == 200
    response = client.post(f"/api/v1/imports/{batch['batch_id']}/commit", json={"preview_hash": batch["preview_hash"], "expected_revision": 99}, headers={**HEADERS, "Idempotency-Key": "commit-key"})
    assert response.status_code == 409 and response.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_conflicting_profile_version_is_rejected(tmp_path):
    fixture = tmp_path / "fixture"
    shutil.copytree(FIXTURE, fixture)
    client = TestClient(create_app(tmp_path / "test.sqlite3", fixture))
    assert client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS).status_code == 200
    manifest = json.loads((fixture / "manifest.json").read_text())
    manifest["fixture_version"] = 2
    (fixture / "manifest.json").write_text(json.dumps(manifest))
    boards = json.loads((fixture / "board_profiles.json").read_text())
    boards["profiles"][0]["max_total_gib"] = 8
    (fixture / "board_profiles.json").write_text(json.dumps(boards))
    response = client.post("/api/v1/fixture-registrations", json={}, headers=HEADERS)
    assert response.status_code == 409 and response.json()["error"]["code"] == "PROFILE_VERSION_CONFLICT"
