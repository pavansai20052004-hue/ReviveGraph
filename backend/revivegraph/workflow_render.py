"""Opt-in Render task client. No hosted task is started on the default path."""
import copy
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import time

from . import workflow
from .execution_protocol import accept, canonical, digest
from .imports import Problem
from .settings import settings

ROOT = Path(__file__).resolve().parents[2]


def validate_download(initial, returned):
    """Reconstruct each stage hash and independently check final feasibility.

    Hash consistency is integrity evidence, not a remote optimality proof or
    evidence that any technician approved or repaired a physical computer.
    """
    for key in ("protocol", "payload", "provider", "run_key", "run_id"):
        if returned.get(key) != initial.get(key):
            raise ValueError("Render workflow returned a different request identity.")
    if len(canonical(returned).encode("utf-8")) > 8 * 1024 * 1024:
        raise ValueError("Render workflow result envelope exceeds 8 MiB.")
    verified_input = workflow.validate_input(initial)
    if returned["request_hash"] != verified_input["request_hash"] or returned["candidate_count"] != verified_input["candidate_count"]:
        raise ValueError("Render workflow input validation differs from local validation.")
    payload = initial["payload"]
    result = returned["result"]
    accept(payload, {"protocol": payload["protocol"], "input_hash": digest(payload),
                    "source_hash": payload["source_hash"], "output_hash": returned["result_hash"], "result": result})
    if returned["execution"].get("provider") != initial["provider"]:
        raise ValueError("Render workflow silently changed execution provider.")
    excerpt = returned["execution"].get("log_excerpt")
    if excerpt is not None:
        if (excerpt.get("sanitized") is not True or not isinstance(excerpt.get("text"), str)
                or len(excerpt["text"]) > 65536
                or excerpt.get("sha256") != hashlib.sha256(excerpt["text"].encode("utf-8")).hexdigest()):
            raise ValueError("Render workflow provider log excerpt hash or boundary is invalid.")
    stages = returned["stages"]
    if len(stages) != len(workflow.STAGES):
        raise ValueError("Render workflow has an incomplete stage trace.")
    reconstruction = copy.deepcopy(initial)
    fields = (("candidate_count", "request_hash"), ("result", "execution"), ("result_hash",), ("artifact",))
    previous = None
    for name, step, added in zip(workflow.STAGES, stages, fields):
        start, end = datetime.fromisoformat(step["started_at"]), datetime.fromisoformat(step["finished_at"])
        if (step["stage"] != name or step["status"] != "passed" or start.utcoffset() is None
                or end.utcoffset() is None or start > end or (previous is not None and start < previous)):
            raise ValueError("Render workflow stage status or chronology is invalid.")
        previous = end
        if step["input_hash"] != digest(reconstruction):
            raise ValueError("Render workflow stage input hash mismatch.")
        reconstruction.update({key: copy.deepcopy(returned[key]) for key in added})
        reconstruction.setdefault("stages", [])
        if step["output_hash"] != digest(reconstruction):
            raise ValueError("Render workflow stage output hash mismatch.")
        reconstruction.setdefault("stages", []).append(copy.deepcopy(step))
    if reconstruction != returned:
        raise ValueError("Render workflow envelope has unexpected or changed fields.")
    return workflow.finish(returned, "render-workflows")


def calculate(snapshot, budget, minutes, provider="local", *, run_key=None, client=None,
              evidence_root=None, timeout_seconds=1200, poll_seconds=2, clock=time.monotonic, sleep=time.sleep):
    """Submit once, poll with a deadline, then verify downloaded stage results.

    The polling deadline does not replace the SDK's own HTTP request timeout.
    Failed/uncertain submissions are never automatically retried.
    """
    cfg = settings()
    if cfg.get("REVIVEGRAPH_RENDER_ENABLED") != "1":
        raise Problem(503, "RENDER_DISABLED", "Render execution is disabled. Configure and explicitly enable a deployed workflow first.")
    slug = cfg.get("REVIVEGRAPH_RENDER_TASK", "")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+/recover", slug):
        raise Problem(503, "RENDER_TASK_MISSING", "Set REVIVEGRAPH_RENDER_TASK to the deployed workflow-slug/recover task.")
    if any(os.environ.get(name) for name in ("RENDER_TASKS_URL", "RENDER_LOCAL_DEV_URL", "RENDER_USE_LOCAL_DEV")):
        raise Problem(503, "RENDER_LOCAL_SERVER_UNSUPPORTED", "This adapter labels hosted runs only; unset RENDER_TASKS_URL or use the explicitly local pipeline.")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 1200:
        raise ValueError("Render polling deadline must be between 1 and 1200 seconds.")
    if not isinstance(poll_seconds, (int, float)) or not 0 < poll_seconds <= 10:
        raise ValueError("Render polling interval must be greater than zero and at most ten seconds.")
    initial = workflow.new_request(snapshot, budget, minutes, provider, run_key)
    workflow.validate_input(initial)  # Reject invalid requests before any paid task.
    owned_http = None
    if client is None:
        if not cfg.get("RENDER_API_KEY"):
            raise Problem(503, "RENDER_KEY_MISSING", "Configure RENDER_API_KEY on the backend; do not paste it into the browser.")
        try:
            from render import Render
        except ImportError as exc:
            raise Problem(503, "RENDER_SDK_MISSING", "Install backend/requirements-render.lock.txt.") from exc
        client = Render(token=cfg["RENDER_API_KEY"])
        # SDK 1.4.0 exposes its generated API client. Its default timeout is
        # unbounded; explicitly scope a 15-second HTTP timeout to this client.
        import httpx
        from render.version import get_user_agent
        owned_http = httpx.Client(base_url="https://api.render.com/v1", timeout=15,
            headers={"Authorization": "Bearer " + cfg["RENDER_API_KEY"], "User-Agent": get_user_agent()},
            transport=httpx.HTTPTransport(retries=0), follow_redirects=False)
        client.client.internal.set_httpx_client(owned_http)
    identity = hashlib.sha256((run_key or initial["run_id"]).encode()).hexdigest()
    directory = Path(evidence_root or ROOT / "data/render-workflow-runs") / identity
    try:
        directory.mkdir(parents=True)
    except FileExistsError as exc:
        if owned_http is not None:
            owned_http.close()
        raise Problem(409, "RENDER_ATTEMPT_EXISTS", "A workflow attempt exists for this request. Inspect its receipt before starting another run.") from exc
    receipt = {"orchestrator": "render-workflows", "workflow_version": workflow.VERSION,
               "request_hash": digest(initial["payload"]), "submitted_at": workflow.timestamp(),
               "accepted": False, "task_run_id": None, "retry_policy": "never automatically resubmit",
               "usage": None, "usage_note": "No usage value was supplied by this SDK response."}
    def save():
        (directory / "receipt.json").write_text(canonical(receipt), encoding="utf-8")
    save()
    try:
        deadline = clock() + timeout_seconds
        started = client.workflows.start_task(slug, {"value": initial}, idempotency_key="revivegraph-" + identity)
        receipt["task_run_id"] = started.id
        save()
        while True:
            details = client.workflows.get_task_run(started.id)
            receipt["status"] = details.status
            save()
            if details.status == "completed":
                values = details.results
                if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], dict):
                    raise ValueError("Render task must return one workflow state object.")
                result, execution = validate_download(initial, values[0])
                execution["workflow"]["task_run_id"] = started.id
                provider_evidence = values[0]["execution"]
                (directory / "provider-evidence.json").write_text(canonical(provider_evidence), encoding="utf-8")
                receipt.update(accepted=True, finished_at=workflow.timestamp(), result_hash=digest(result),
                               artifact_hash=execution["workflow"]["artifact_hash"],
                               provider_evidence_hash=digest(provider_evidence),
                               stage_trace=execution["workflow"]["stages"])
                save()
                (directory / "artifact.json").write_text(canonical(execution["workflow"]["artifact"]), encoding="utf-8")
                return result, execution
            if details.status in ("failed", "canceled", "cancelled"):
                raise ValueError("Render task terminated without a validated result.")
            if clock() >= deadline:
                raise TimeoutError("Render workflow polling deadline exceeded.")
            sleep(min(poll_seconds, max(0, deadline - clock())))
    except Exception as exc:
        receipt.update(accepted=False, error_type=type(exc).__name__, finished_at=workflow.timestamp())
        if receipt["task_run_id"]:
            try:
                client.workflows.cancel_task_run(receipt["task_run_id"])
                receipt["cancellation_requested"] = True
            except Exception as cancellation:
                receipt["cancellation_error_type"] = type(cancellation).__name__
        save()
        raise Problem(502, "RENDER_EXECUTION_FAILED", "Render execution failed or its downloaded result was rejected. Inspect the sanitized local receipt before retrying.") from exc
    finally:
        if owned_http is not None:
            owned_http.close()
