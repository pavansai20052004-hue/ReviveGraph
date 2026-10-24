"""Workflow checks use temporary fixture imports, never the normal database."""
import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_optimizer import snapshot, restricted
from test_recovery import env, post, plan, allocated_ids
from revivegraph import workflow
from revivegraph import workflow_render
from revivegraph.execution_protocol import digest
from revivegraph.imports import Problem
from revivegraph.optimizer import solve


@pytest.fixture
def tiny(snapshot):
    return restricted(snapshot, ["RG-PC-02", "RG-PC-04"], ["RG-RAM-15", "RG-RAM-16"])


def test_local_actual_chain_and_audit(tiny):
    before = copy.deepcopy(tiny)
    result, execution = workflow.calculate(tiny, 58000, 82, run_key="workflow-local-test")
    assert tiny == before
    assert result["totals"]["usable_final"] == 2
    assert result["baseline"]["totals"]["usable_final"] == 1
    assert execution["provider"] == "local"
    trace = execution["workflow"]
    assert trace["orchestrator"] == "local-pipeline"
    assert trace["task_run_id"] is None
    assert [s["stage"] for s in trace["stages"]] == list(workflow.STAGES)
    assert all(s["status"] == "passed" and s["started_at"] <= s["finished_at"]
               and len(s["input_hash"]) == len(s["output_hash"]) == 64 for s in trace["stages"])
    artifact = trace["artifact"]
    assert trace["artifact_hash"] == digest(artifact)
    assert artifact["result_hash"] == digest(result)
    assert artifact["physical_repairs"] == 0
    assert artifact["human_approval"] is False
    assert artifact["simulation_only"] is True


@pytest.mark.parametrize("kind", ["resources", "reference", "physical", "version"])
def test_invalid_input_never_executes(tiny, kind):
    calls = []
    budget = 58000
    if kind == "resources":
        budget = True
    elif kind == "reference":
        tiny["components"][0]["location_asset_id"] = "MISSING"
    elif kind == "physical":
        tiny["mode"] = "physical"
    else:
        tiny["inspection_rule_version"] = "unknown-rule"
    with pytest.raises(ValueError):
        workflow.calculate(tiny, budget, 82, executor=lambda *a, **k: calls.append(a))
    assert calls == []


@pytest.mark.parametrize("kind", ["totals", "allocation", "baseline", "solver_version", "provider"])
def test_transport_tampering_fails_closed(tiny, kind):
    calls = []
    def transport(source, budget, minutes, provider, **kw):
        calls.append(kw)
        result = solve(source, budget, minutes)
        if kind == "totals":
            result["totals"]["cost_paise"] = 0
        elif kind == "allocation":
            result["allocations"].append(copy.deepcopy(result["allocations"][0]))
        elif kind == "baseline":
            result["baseline"]["totals"]["usable_final"] = 500
        elif kind == "solver_version":
            result["solver"]["engine_version"] = "unapproved"
        return result, {"provider": "local" if kind == "provider" else "nodus", "job_id": "mock-only"}
    with pytest.raises(ValueError):
        workflow.calculate(tiny, 58000, 82, "nodus", run_key="mock-request", executor=transport)
    assert len(calls) == 1


def test_paid_execution_failure_has_no_retry(tiny):
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(kwargs)
        raise RuntimeError("mock transport unavailable")
    with pytest.raises(RuntimeError, match="mock transport unavailable"):
        workflow.calculate(tiny, 58000, 82, "nodus", run_key="failed-mock", executor=unavailable)
    assert len(calls) == 1


def test_stage_order_and_changed_input_are_blocked(tiny):
    initial = workflow.new_request(tiny, 58000, 82)
    with pytest.raises(ValueError, match="order"):
        workflow.execute_plan(initial)
    state = workflow.validate_input(initial)
    state["payload"]["budget_paise"] = 999999
    with pytest.raises(ValueError, match="changed"):
        workflow.execute_plan(state)


def test_final_boundary_blocks_audit_change(tiny):
    state = workflow.validate_input(workflow.new_request(tiny, 58000, 82))
    state = workflow.execute_plan(state)
    state = workflow.validate_result(state)
    state = workflow.generate_audit(state)
    with pytest.raises(ValueError, match="order"):
        workflow.generate_audit(state)
    state["artifact"]["physical_repairs"] = 2
    with pytest.raises(ValueError, match="audit"):
        workflow.finish(state)


def test_real_render_sdk_task_registration(tiny):
    pytest.importorskip("render")
    entry = Path(__file__).resolve().parents[2] / "workflows" / "main.py"
    spec = importlib.util.spec_from_file_location("revivegraph_workflow_tasks", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.app is not None
    # Actual decorator import/register validation. No Render server or cloud call.
    assert module.recover.name == "recover"
    tasks = module.app._registry._tasks
    assert set(tasks) == {"validate_input", "execute_plan", "validate_result", "generate_audit", "recover"}
    assert all(task.options.retry.max_retries == 0 for task in tasks.values())
    class InProcessContext:
        async def run(self, task, value):
            return task.func(self, value)
    state = asyncio.run(module.recover.func(InProcessContext(), workflow.new_request(tiny, 58000, 82)))
    assert state["result"]["totals"]["usable_final"] == 2


def completed_state(initial, executor=None):
    state = workflow.validate_input(initial)
    state = workflow.execute_plan(state, executor)
    state = workflow.validate_result(state)
    return workflow.generate_audit(state)


def test_download_revalidates_actual_chain(tiny):
    initial = workflow.new_request(tiny, 58000, 82)
    state = completed_state(initial)
    result, execution = workflow_render.validate_download(initial, state)
    assert result["totals"]["usable_final"] == 2
    assert execution["workflow"]["orchestrator"] == "render-workflows"


@pytest.mark.parametrize("kind", ["input", "result", "trace", "audit", "extra"])
def test_download_rejects_tampering(tiny, kind):
    initial = workflow.new_request(tiny, 58000, 82)
    state = completed_state(initial)
    if kind == "input":
        state["payload"]["budget_paise"] = 999999
    elif kind == "result":
        state["result"]["totals"]["cost_paise"] = 0
    elif kind == "trace":
        state["stages"][0]["output_hash"] = "0" * 64
    elif kind == "audit":
        state["artifact"]["human_approval"] = True
    else:
        state["unexpected"] = "not in contract"
    with pytest.raises(ValueError):
        workflow_render.validate_download(initial, state)


class FakeWorkflows:
    """SDK-shaped transport, never a Render or Nodus cloud call."""
    def __init__(self, status="completed", tamper=False, executor=None):
        self.status, self.tamper = status, tamper
        self.executor = executor
        self.starts = self.cancels = 0

    def start_task(self, slug, data, *, idempotency_key=None):
        self.starts += 1
        assert idempotency_key.startswith("revivegraph-")
        self.state = completed_state(data["value"], self.executor)
        if self.tamper:
            self.state["artifact"]["physical_repairs"] = 1
        return SimpleNamespace(id="trn-mock-only", status="pending")

    def get_task_run(self, identity):
        return SimpleNamespace(status=self.status, results=[self.state], error=None)

    def cancel_task_run(self, identity):
        self.cancels += 1


def enable_render(monkeypatch):
    monkeypatch.setenv("REVIVEGRAPH_RENDER_ENABLED", "1")
    monkeypatch.setenv("REVIVEGRAPH_RENDER_TASK", "mock-only/recover")
    monkeypatch.delenv("RENDER_TASKS_URL", raising=False)


def test_mock_render_transport_receipt_and_retry_guard(tiny, tmp_path, monkeypatch):
    enable_render(monkeypatch)
    transport = FakeWorkflows()
    result, execution = workflow_render.calculate(tiny, 58000, 82, run_key="sdk-mock", evidence_root=tmp_path,
                                                   client=SimpleNamespace(workflows=transport))
    assert result["totals"]["usable_final"] == 2
    assert execution["workflow"]["task_run_id"] == "trn-mock-only"
    receipt_path = next(tmp_path.rglob("receipt.json"))
    receipt = json.loads(receipt_path.read_text())
    assert receipt["accepted"] is True
    assert receipt["result_hash"] == digest(result)
    assert receipt["usage"] is None
    assert next(tmp_path.rglob("artifact.json")).exists()
    with pytest.raises(Problem) as duplicate:
        workflow_render.calculate(tiny, 58000, 82, run_key="sdk-mock", evidence_root=tmp_path,
                                  client=SimpleNamespace(workflows=transport))
    assert duplicate.value.code == "RENDER_ATTEMPT_EXISTS"
    assert transport.starts == 1


@pytest.mark.parametrize("kind", ["tamper", "failed", "timeout"])
def test_mock_render_failures_cancel_without_retry(tiny, tmp_path, monkeypatch, kind):
    enable_render(monkeypatch)
    transport = FakeWorkflows(status="failed" if kind == "failed" else "running" if kind == "timeout" else "completed",
                              tamper=kind == "tamper")
    ticks = iter([0, 2])
    with pytest.raises(Problem) as rejected:
        workflow_render.calculate(tiny, 58000, 82, run_key=kind, evidence_root=tmp_path,
            client=SimpleNamespace(workflows=transport), timeout_seconds=1, clock=lambda: next(ticks), sleep=lambda _: None)
    assert rejected.value.code == "RENDER_EXECUTION_FAILED"
    assert transport.starts == transport.cancels == 1
    receipt = json.loads(next(tmp_path.rglob("receipt.json")).read_text())
    assert receipt["accepted"] is False
    assert receipt["error_type"] == ("TimeoutError" if kind == "timeout" else "ValueError")


def test_render_explicit_enable_required(tiny, monkeypatch):
    monkeypatch.setenv("REVIVEGRAPH_RENDER_ENABLED", "0")
    with pytest.raises(Problem) as disabled:
        workflow_render.calculate(tiny, 58000, 82)
    assert disabled.value.code == "RENDER_DISABLED"


@pytest.mark.parametrize("variable", ["RENDER_TASKS_URL", "RENDER_LOCAL_DEV_URL", "RENDER_USE_LOCAL_DEV"])
def test_render_local_routing_cannot_be_called_hosted(tiny, monkeypatch, variable):
    enable_render(monkeypatch)
    monkeypatch.setenv(variable, "http://localhost:8120" if variable != "RENDER_USE_LOCAL_DEV" else "1")
    with pytest.raises(Problem) as blocked:
        workflow_render.calculate(tiny, 58000, 82)
    assert blocked.value.code == "RENDER_LOCAL_SERVER_UNSUPPORTED"


def test_real_render_sdk_with_mock_http_transport(tiny, tmp_path, monkeypatch):
    render = pytest.importorskip("render")
    import httpx
    enable_render(monkeypatch)
    requests, state = [], {}
    def respond(request):
        requests.append(request)
        common = {"id": "trn-mock-http", "taskId": "tsk-mock-http", "parentTaskRunId": "",
                  "rootTaskRunId": "trn-mock-http", "retries": 0, "attempts": []}
        if request.method == "POST":
            body = json.loads(request.content)
            assert body["task"] == "mock-only/recover"
            assert body["idempotencyKey"].startswith("revivegraph-")
            state["value"] = completed_state(body["input"]["value"])
            return httpx.Response(202, json={**common, "status": "pending"})
        assert request.method == "GET"
        return httpx.Response(200, json={**common, "status": "completed", "input": [], "results": [state["value"]]})
    transport_config = []
    def mock_transport(**kwargs):
        transport_config.append(kwargs)
        return httpx.MockTransport(respond)
    monkeypatch.setattr(httpx, "HTTPTransport", mock_transport)
    monkeypatch.setattr(workflow_render, "settings", lambda: {
        "REVIVEGRAPH_RENDER_ENABLED": "1", "REVIVEGRAPH_RENDER_TASK": "mock-only/recover",
        "RENDER_API_KEY": "mock-token-never-sent"})
    result, execution = workflow_render.calculate(tiny, 58000, 82, run_key="real-sdk-mock-http", evidence_root=tmp_path)
    assert [req.method for req in requests] == ["POST", "GET"]
    assert transport_config == [{"retries": 0}]
    assert requests[0].extensions["timeout"]["read"] == 15
    assert result["totals"]["usable_final"] == 2
    assert execution["workflow"]["task_run_id"] == "trn-mock-http"
    receipt = next(tmp_path.rglob("receipt.json")).read_text()
    assert "mock-token-never-sent" not in receipt


def test_api_default_plan_persists_local_workflow_trace(env):
    app, client, _ = env
    calculated = plan(client, "workflow-api-local")
    trace = calculated["execution"]["workflow"]
    assert trace["orchestrator"] == "local-pipeline"
    assert trace["artifact"]["physical_repairs"] == 0
    saved = client.get(f"/api/v1/plans/{calculated['id']}").json()
    assert saved["execution"] == calculated["execution"]
    with app.state.db.connect() as connection:
        event = connection.execute("SELECT data FROM audit_events WHERE action='plan_validated' AND entity_id=?",
                                   (calculated["id"],)).fetchone()
    assert json.loads(event["data"])["execution"]["workflow"]["artifact_hash"] == trace["artifact_hash"]


def test_api_disabled_render_creates_no_plan(env, monkeypatch):
    app, client, _ = env
    monkeypatch.setenv("REVIVEGRAPH_RENDER_ENABLED", "0")
    with app.state.db.connect() as connection:
        before = connection.execute("SELECT COUNT(*) FROM recovery_plans").fetchone()[0]
    response = post(client, "/plans", {"context_id": "workflow-api-disabled", "orchestration": "render"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RENDER_DISABLED"
    with app.state.db.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM recovery_plans").fetchone()[0] == before


def test_api_mock_hosted_execution_persists_and_failure_inherits_render(env, monkeypatch):
    app, client, _ = env
    calls = []
    def hosted_mock(source, budget, minutes, provider="local", *, run_key=None):
        calls.append((provider, run_key))
        result, execution = workflow.calculate(source, budget, minutes, provider, run_key=run_key)
        execution["workflow"]["orchestrator"] = "render-workflows"
        execution["workflow"]["task_run_id"] = "trn-test-double-only-" + str(len(calls))
        return result, execution
    monkeypatch.setattr(workflow_render, "calculate", hosted_mock)
    original = plan(client, "workflow-api-hosted-mock", orchestration="render")
    assert original["execution"]["workflow"]["task_run_id"] == "trn-test-double-only-1"
    locations = {row["component_id"]: row["location_asset_id"]
                 for row in client.get("/api/v1/components").json()["items"]}
    donor = next(part for allocation in original["result"]["allocations"]
                 for part in allocation["ram_component_ids"] + [allocation["storage_component_id"]]
                 if locations[part] and locations[part] != allocation["target_asset_id"])
    response = post(client, f"/plans/{original['id']}/failures", {"component_id": donor})
    assert response.status_code == 200, response.text
    revised = response.json()
    assert len(calls) == 2 and all(provider == "local" for provider, _ in calls)
    assert revised["execution"]["workflow"]["orchestrator"] == "render-workflows"
    assert revised["execution"]["workflow"]["task_run_id"] == "trn-test-double-only-2"
    assert donor not in allocated_ids(revised)
    with app.state.db.connect() as connection:
        events = connection.execute("SELECT data FROM audit_events WHERE action='plan_validated' AND entity_id=?",
                                    (revised["id"],)).fetchall()
    assert len(events) == 1
    assert json.loads(events[0]["data"])["execution"]["workflow"]["task_run_id"] == "trn-test-double-only-2"


def test_nodus_log_excerpt_survives_mock_render_worker(tiny, tmp_path, monkeypatch):
    from test_nodus import fake_sdk
    from revivegraph.execution import execute
    enable_render(monkeypatch)
    monkeypatch.setenv("REVIVEGRAPH_NODUS_ENABLED", "1")
    monkeypatch.setenv("NODUS_API_KEY", "mock-credential-to-redact")
    def output(payload):
        result = solve(payload["snapshot"], payload["budget_paise"], payload["time_minutes"])
        return {"protocol": payload["protocol"], "input_hash": digest(payload), "source_hash": payload["source_hash"],
                "output_hash": digest(result), "result": result}
    sdk, calls = fake_sdk(output)
    monkeypatch.setattr(sdk.Job, "logs", lambda self, **kwargs: [
        "test-only remote log mock-credential-to-redact Bearer mock-token https://example.com/private?signature=test\n" + "x" * 70000])
    def executor(source, budget, minutes, provider, **kwargs):
        return execute(source, budget, minutes, provider, sdk=sdk, evidence_root=tmp_path / "nodus", **kwargs)
    transport = FakeWorkflows(executor=executor)
    result, execution = workflow_render.calculate(tiny, 58000, 82, "nodus", run_key="mock-log-forwarding",
        client=SimpleNamespace(workflows=transport), evidence_root=tmp_path / "render")
    retained = json.loads(next((tmp_path / "render").rglob("provider-evidence.json")).read_text())
    excerpt = retained["log_excerpt"]
    assert excerpt == execution["log_excerpt"]
    assert excerpt["sanitized"] is True and len(excerpt["text"]) <= 65536
    assert "mock-credential-to-redact" not in excerpt["text"] and "mock-token" not in excerpt["text"]
    assert "signature=test" not in excerpt["text"]
    assert excerpt["sha256"] == hashlib.sha256(excerpt["text"].encode()).hexdigest()
    assert next((tmp_path / "nodus").rglob("logs.txt")).read_text() == excerpt["text"]
    receipt = json.loads(next((tmp_path / "render").rglob("receipt.json")).read_text())
    assert receipt["provider_evidence_hash"] == digest(retained)
    assert result["totals"]["usable_final"] == 2 and len(calls) == 1
