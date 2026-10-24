"""Opt-in Nodus CPU adapter; local execution remains dependency-independent."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from datetime import datetime, timezone
import uuid

from .execution_protocol import accept, canonical, digest, request
from .imports import Problem

ROOT = Path(__file__).resolve().parents[2]
FILES = ("__init__.py", "domain.py", "optimizer.py", "execution_protocol.py", "nodus_worker.py")


def prepare(directory, snapshot, budget, minutes):
    """Build a strict allowlist, never upload the checkout wholesale."""
    package = directory / "revivegraph"
    package.mkdir()
    for name in FILES:
        shutil.copyfile(Path(__file__).parent / name, package / name)
    shutil.copyfile(ROOT / "backend/nodus-worker.lock.txt", directory / "requirements.txt")
    source = {str(p.relative_to(directory)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(directory.rglob("*")) if p.is_file()}
    (directory / "source-manifest.json").write_text(canonical(source), encoding="utf-8")
    payload = request(snapshot, budget, minutes, digest(source))
    (directory / "input.json").write_text(canonical(payload), encoding="utf-8")
    return payload


def sanitize(text):
    text = str(text)
    if os.environ.get("NODUS_API_KEY"):
        text = text.replace(os.environ["NODUS_API_KEY"], "[REDACTED]")
    text = re.sub(r'''(?i)(bearer\s+|(?:api[_-]?key|token|authorization)["']?\s*[:=]\s*["']?)[^\s"'}]+''', r"\1[REDACTED]", text)
    return re.sub(r"https?://[^\s\"<>]+", "[URL REDACTED]", text)[:65536]


def execute(snapshot, budget, minutes, provider="local", *, sdk=None, evidence_root=None, run_key=None):
    if provider == "local":
        from .optimizer import solve
        return solve(snapshot, budget, minutes), {"provider": "local", "adapter_version": "cpu-adapter-v1"}
    if provider != "nodus":
        raise ValueError("Unknown execution provider.")
    if os.environ.get("REVIVEGRAPH_NODUS_ENABLED") != "1":
        raise Problem(503, "NODUS_DISABLED", "Enable Nodus explicitly after signing in and confirming event credit.")
    if sdk is None:
        try:
            import nodus as sdk
        except ImportError as exc:
            raise Problem(503, "NODUS_SDK_MISSING", "Install backend/requirements-nodus.lock.txt, then sign in with nodus login.") from exc
    evidence = Path(evidence_root or ROOT / "data/nodus-runs") / (hashlib.sha256(run_key.encode()).hexdigest() if run_key else uuid.uuid4().hex)
    try:
        evidence.mkdir(parents=True)
    except FileExistsError as exc:
        # A timeout/disconnect may have created a billable job. Never submit a
        # second job automatically for the same idempotency identity.
        raise Problem(409, "NODUS_ATTEMPT_EXISTS", "A Nodus attempt already exists for this request. Inspect its receipt/job before using a new key; retries cannot spend twice automatically.") from exc
    receipt = {"provider": "nodus", "adapter_version": "cpu-adapter-v1", "accepted": False,
               "created_at": datetime.now(timezone.utc).isoformat(), "cpu": 1, "memory": "2Gi",
               "max_cost_usd": "0.10", "job_timeout": "5m", "client_wait_timeout_seconds": 360,
               "job_id": None, "usage": None}

    def save():
        (evidence / "receipt.json").write_text(canonical(receipt), encoding="utf-8")

    def collect(job):
        try:
            status = job.status()
            for field in ("phase", "startTime", "completionTime", "cost", "unitMetrics"):
                value = status.get(field)
                if value is not None:
                    receipt[field] = json.loads(sanitize(canonical(value)))
            receipt["usage"] = receipt.get("unitMetrics")
        except Exception as exc:
            receipt["status_collection_error"] = type(exc).__name__
        try:
            # Bound retained log bytes even if the provider has a large log.
            lines = ""
            for line in job.logs(follow=False):
                lines += line
                if len(lines) >= 65536:
                    break
            safe_logs = sanitize(lines)
            (evidence / "logs.txt").write_text(safe_logs, encoding="utf-8")
            # Render task disks are ephemeral. Forward the same bounded,
            # sanitized excerpt so the caller can retain it with the receipt.
            receipt["log_excerpt"] = {"text": safe_logs, "sanitized": True, "max_characters": 65536,
                "sha256": hashlib.sha256(safe_logs.encode("utf-8")).hexdigest()}
        except Exception as exc:
            receipt["log_collection_error"] = type(exc).__name__

    save()
    job = None
    try:
        with tempfile.TemporaryDirectory(prefix="revivegraph-nodus-") as temp:
            source = Path(temp)
            payload = prepare(source, snapshot, budget, minutes)
            receipt.update(input_hash=digest(payload), source_hash=payload["source_hash"])
            (evidence / "input.json").write_text(canonical(payload), encoding="utf-8")
            save()
            job = sdk.Job.run(image="nodus/python:3.12", source=source,
                command=["sh", "-c", "python -m pip install --disable-pip-version-check --no-cache-dir --retries 0 --timeout 20 -r requirements.txt && python -m revivegraph.nodus_worker input.json /nodus/outputs/result.json"],
                cpu=1, memory="2Gi", timeout="5m", max_cost=0.10,
                outputs={"result": "/nodus/outputs/result.json"})
            receipt["job_id"] = job.name
            save()  # Preserve handle before waiting; never automatically resubmit.
            job.wait(timeout=360)
            collect(job)
            path = evidence / "downloaded-result.json"
            job.outputs["result"].download(path)
            if path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError("Remote output exceeds 4 MiB.")
            raw = path.read_bytes()
            receipt["download_sha256"] = hashlib.sha256(raw).hexdigest()
            response = json.loads(raw)
            result = accept(payload, response)
            receipt.update(accepted=True, output_hash=response["output_hash"],
                           validation="local independent allocation, accounting and baseline reconstruction",
                           solver_proof="reported by pinned remote worker, not re-proven locally")
            save()
            return result, receipt
    except Exception as exc:
        receipt["error_type"] = type(exc).__name__
        receipt["error_message"] = sanitize(str(exc))
        if job is not None:
            collect(job)
            try:
                job.cancel()
                receipt["cancel_requested"] = True
            except Exception:
                receipt["cancel_requested"] = False
        save()
        raise Problem(502, "NODUS_CALCULATION_FAILED", f"Nodus calculation was not accepted ({type(exc).__name__}). No local fallback was substituted; inspect data/nodus-runs receipt and account job status before retrying.") from exc
