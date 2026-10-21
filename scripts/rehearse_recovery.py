r"""Reproducible acceptance rehearsal using a temporary database, never normal data.

Run: .venv\Scripts\python.exe scripts\rehearse_recovery.py --output data\recovery-rehearsal.json
Approval/check evidence here is automated test input, not a technician action.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from revivegraph.main import create_app


def rehearse():
    with tempfile.TemporaryDirectory(prefix="revivegraph-rehearsal-") as folder:
        database = Path(folder) / "isolated.sqlite3"
        client = TestClient(create_app(database))

        def post(route, body=None, **kwargs):
            response = client.post("/api/v1" + route, headers={"X-Actor-ID": "automated-rehearsal",
                "Idempotency-Key": uuid.uuid4().hex}, **({"json": body} if body is not None else kwargs))
            response.raise_for_status()
            return response.json()

        registration = post("/fixture-registrations", {})
        batch = post("/imports/preview", data={"registration_id": registration["id"]}, files={
            "computers_file": ("computers.csv", (ROOT / "datasets/synthetic-v1/computers.csv").read_bytes()),
            "components_file": ("components.csv", (ROOT / "datasets/synthetic-v1/components.csv").read_bytes())})
        assert client.get("/api/v1/state").json()["counts"]["computers"] == 0
        post(f"/imports/{batch['batch_id']}/commit", {"preview_hash": batch["preview_hash"], "expected_revision": 0})
        initial = client.get("/api/v1/state").json()
        before = post("/plans", {"budget_paise": 250000, "time_minutes": 330, "context_id": "rehearsal"})
        donor = next(o for o in before["result"]["operations"] if o["operation"].startswith("remove_") and o["target_asset_id"] and o["asset_id"] != o["target_asset_id"])
        after = post(f"/plans/{before['id']}/failures", {"component_id": donor["component_id"]})
        assert client.get(f"/api/v1/plans/{before['id']}").json()["status"] == "stale"
        post(f"/plans/{after['id']}/decision", {"decision": "approve", "input_hash": after["input_hash"]})
        items = post(f"/plans/{after['id']}/work-orders", {})["items"]
        done = set()
        pending = [(o, s) for o in items for s in o["steps"] if s["operation"] != "verify_target"]
        while pending:
            ready = next(((o, s) for o, s in pending if set(s["depends_on"]) <= done), None)
            assert ready, "Work dependency cycle"
            order, step = ready
            post(f"/work-orders/{order['id']}/steps/{step['id']}", {"checks": step["required_checks"],
                "evidence_ref": "synthetic:automated-rehearsal:" + step["id"]})
            done.add(step["id"])
            pending.remove(ready)
        # Recreate backend from the same temporary DB before verification.
        client = TestClient(create_app(database))
        for order in items:
            check = next(s for s in order["steps"] if s["operation"] == "verify_target")
            post(f"/work-orders/{order['id']}/verification", {"outcome": "pass", "checks": check["required_checks"],
                "evidence_ref": "synthetic:automated-rehearsal:" + order["id"]})
        final = client.get("/api/v1/state").json()
        assert final["counts"] == initial["counts"]
        assert final["recovery"]["physical_passes"] == 0
        report = client.get(f"/api/v1/plans/{after['id']}/report").json()
        return {"kind": "executed-synthetic-acceptance-rehearsal", "preparation_date": "2026-10-20",
                "approval_identity": "automated-rehearsal (test input; not technician approval)",
                "initial_counts": initial["counts"], "donor_failure": donor,
                "before_result": before["result"], "after_result": after["result"],
                "operation_counts": dict(Counter(o["operation"] for o in after["result"]["operations"])),
                "final_recovery_counts": final["recovery"], "audit_report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to((ROOT / "datasets").resolve()):
        parser.error("Rehearsal output cannot overwrite original datasets.")
    receipt = rehearse()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        parser.error("Output already exists; choose another file to preserve earlier evidence.")
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "initial_counts": receipt["initial_counts"],
                      "before": receipt["before_result"]["totals"], "after": receipt["after_result"]["totals"],
                      "failed_component": receipt["donor_failure"]["component_id"],
                      "solver": receipt["after_result"]["solver"]["status"],
                      "operation_counts": receipt["operation_counts"], "recorded_simulation": receipt["final_recovery_counts"]}, indent=2))
