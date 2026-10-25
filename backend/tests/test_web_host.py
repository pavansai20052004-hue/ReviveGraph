from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from revivegraph.web import create_web_app


def test_web_host_requires_build_before_creating_database(tmp_path):
    database = tmp_path / "isolated.sqlite3"
    with pytest.raises(RuntimeError, match="Build the frontend"):
        create_web_app(database, tmp_path / "missing")
    assert not database.exists()


def test_same_origin_web_host_keeps_api_and_fixture_import_working(tmp_path):
    static = tmp_path / "dist"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text('<html><div id="root">ReviveGraph</div></html>')
    (static / "assets" / "app.js").write_text("console.log('web host')")
    client = TestClient(create_web_app(tmp_path / "isolated.sqlite3", static))
    assert client.get("/").headers["content-type"].startswith("text/html")
    assert "ReviveGraph" in client.get("/").text
    assert "web host" in client.get("/assets/app.js").text
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/api/v1/nonexistent").status_code == 404
    assert client.get("/assets/../../.env.onsite").status_code == 404
    assert client.get("/.env.onsite").status_code == 404
    headers = {"X-Actor-ID": "automated-host-test", "Idempotency-Key": "register"}
    registration = client.post("/api/v1/fixture-registrations", json={}, headers=headers)
    assert registration.status_code == 200
    fixture = Path(__file__).resolve().parents[2] / "datasets" / "synthetic-v1"
    preview = client.post("/api/v1/imports/preview", headers={**headers, "Idempotency-Key": "preview"},
                          data={"registration_id": registration.json()["id"], "fleet_id": "RG-DEMO-12", "mode": "simulation"},
                          files={"computers_file": ("computers.csv", (fixture / "computers.csv").read_bytes()),
                                 "components_file": ("components.csv", (fixture / "components.csv").read_bytes())})
    assert preview.status_code == 200
    batch = preview.json()
    assert batch["valid"] and batch["counts"] == {"computers": 12, "components": 31}
    counts = client.get("/api/v1/state").json()["counts"]
    assert (counts["computers"], counts["components"]) == (0, 0)
    committed = client.post(f"/api/v1/imports/{batch['batch_id']}/commit",
                            headers={**headers, "Idempotency-Key": "commit"},
                            json={"preview_hash": batch["preview_hash"], "expected_revision": batch["expected_revision"]})
    assert committed.status_code == 200
    counts = client.get("/api/v1/state").json()["counts"]
    assert (counts["computers"], counts["components"]) == (12, 31)
