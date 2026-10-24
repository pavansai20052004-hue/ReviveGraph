"""One explicitly requested remote synthetic calculation, isolated from normal data.

Requires Nodus login, event credit and REVIVEGRAPH_NODUS_ENABLED=1.
Does not approve plans or create work/verification evidence.
"""
import argparse
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; never reuse a prior run")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "data"):
        parser.error("Choose a new directory inside this project's ignored data/ directory.")
    output.mkdir(parents=True, exist_ok=False)
    from fastapi.testclient import TestClient
    from revivegraph.main import create_app
    from revivegraph.execution_protocol import canonical
    app = create_app(output / "isolated.sqlite3")
    with TestClient(app) as client:
        def post(route, **kwargs):
            response = client.post("/api/v1" + route, headers={"X-Actor-ID": "onsite-nodus-calculation-automated",
                "Idempotency-Key": uuid.uuid4().hex}, **kwargs)
            response.raise_for_status()
            return response.json()
        registration = post("/fixture-registrations", json={})
        fixture = ROOT / "datasets/synthetic-v1"
        batch = post("/imports/preview", data={"registration_id": registration["id"]}, files={
            "computers_file": ("computers.csv", (fixture / "computers.csv").read_bytes()),
            "components_file": ("components.csv", (fixture / "components.csv").read_bytes())})
        if not batch["valid"] or batch["counts"] != {"computers": 12, "components": 31}:
            raise ValueError("Expected synthetic fixture did not validate.")
        post(f"/imports/{batch['batch_id']}/commit", json={"preview_hash": batch["preview_hash"], "expected_revision": 0})
        plan = post("/plans", json={"execution": "nodus", "context_id": "onsite-nodus",
                                    "budget_paise": 250000, "time_minutes": 330})
        report = client.get(f"/api/v1/plans/{plan['id']}/report")
        report.raise_for_status()
        (output / "plan.json").write_text(canonical(plan), encoding="utf-8")
        (output / "audit.json").write_text(canonical(report.json()), encoding="utf-8")
        print(canonical({"plan_id": plan["id"], "execution": plan["execution"],
                         "totals": plan["result"]["totals"], "solver": plan["result"]["solver"]["status"]}))


if __name__ == "__main__":
    main()
