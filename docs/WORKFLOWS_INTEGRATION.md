# Recovery workflow integration — 24 October 2026

This is onsite implementation added to the disclosed foundation. It does not
implement approval, work orders, reconciliation or physical verification. Those
remain responsibilities of the application's existing recovery lifecycle.

## What actually runs

`backend/revivegraph/workflow.py` is a working, in-process pipeline:

1. Validate the versioned synthetic snapshot, resource limits, references,
   component locations and bounded deterministic configuration generation.
2. Execute the selected existing CPU adapter (`local` or explicitly enabled
   `nodus`), with no silent provider fallback.
3. Independently reconstruct allocation eligibility, component exclusivity,
   operation ledger, costs, minutes and greedy baseline with the pinned rules.
4. Generate a compact audit artifact with input/output/snapshot hashes, actual
   stage timestamps, reported solver status and explicit simulation boundaries.

The function accepts `(snapshot, budget_paise, time_minutes, provider="local",
run_key=...)` and returns `(result, execution_metadata)`, matching the existing
execution adapter contract. Its workflow orchestrator is **`local-pipeline`**.
It neither imports the Render SDK nor claims a hosted Render run. The caller
must still recheck database revision and reservations before saving a plan.

The audit always records `physical_repairs: 0`, `human_approval: false` and
`simulation_only: true`. This artifact describes one calculation, not the later
full lifecycle audit or a technician's decision. Solver optimality is reported
by the solver; independent validation establishes feasibility and accounting.

## Render task source and trigger adapter

`workflows/main.py` uses the actual optional Render Python SDK 1.4.0. It registers
`recover` plus `validate_input`, `execute_plan`, `validate_result`, and
`generate_audit` child tasks. The root invokes each child using `TaskContext.run`.
Every task and the default policy explicitly have **zero retries**. The paid
Nodus stage cannot be automatically replayed by these task policies.

`backend/revivegraph/workflow_render.py` is a hosted trigger adapter with the same
calculation signature. It is disabled unless configured explicitly:

```powershell
$env:REVIVEGRAPH_RENDER_ENABLED = "1"
$env:REVIVEGRAPH_RENDER_TASK = "<actual-deployed-workflow-slug>/recover"
# Set RENDER_API_KEY securely in the backend environment; never in browser code.
```

These are instructions for a future authorized deployment, not a record of one.
The adapter reads the project's `settings()` reader, including the ignored
root `.env.onsite` file, with explicit process environment values taking
precedence. It does not mutate global process environment variables.
No Render workflow has been deployed or called in the cloud for this integration.
No Render usage or cost is invented. Local receipts leave usage `null` when the
task API has not supplied it. The adapter refuses local-development routing
variables so local server responses cannot accidentally be labelled hosted.

On an enabled hosted request, the adapter validates before submission, creates an
exclusive attempt receipt, submits once with a hashed SDK idempotency key and
polls the task. It applies a scoped 15-second SDK HTTP timeout, a maximum
1,200-second polling deadline and best-effort root cancellation on failure.
The owned HTTP transport explicitly uses zero retries, in addition to the
zero-retry task policies and the caller's conservative attempt guard.
The polling deadline can be exceeded by an in-flight HTTP call and cleanup.
A failed/uncertain attempt is never automatically resubmitted. Inspect its
receipt and remote status before choosing a new request identity.

The downloaded envelope must match the original immutable input and provider.
The laptop reconstructs all four stage hashes, checks timestamp ordering,
independently validates allocations/accounting/baseline again and checks audit
consistency before accepting a result. Hashes establish envelope consistency;
they are not a cryptographic attestation of remote execution or an optimality
proof. The workflow payload's `source_hash` is a protocol marker; Nodus separately
retains its actual uploaded solver bundle hash in the underlying receipt.

Sanitized attempt receipts and calculation artifacts go under ignored
`data/render-workflow-runs/<hashed-request-identity>/`. They retain task ID,
status, actual timestamps, input/output/artifact hashes, successful stage trace
and error class. Provider error bodies, API keys and arbitrary remote logs are
not copied into these receipts. Render cloud log retrieval and usage collection
remain unimplemented. Existing Nodus adapter evidence remains separate.

The existing Nodus collector now also returns its same bounded sanitized log
excerpt and SHA-256 inside its receipt. This preserves the excerpt across an
ephemeral Render worker. The Render client checks its length/hash and saves
`provider-evidence.json` alongside its own receipt and audit artifact. The
original Nodus `logs.txt` behavior is preserved. Render platform logs are a
separate, still unimplemented retrieval path.

## Optional dependencies and startup

The original application lockfile is unchanged. Install the optional SDK with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-render.lock.txt
```

The separate lock pins Render 1.4.0 and its additional transitive packages and
includes the existing core lock. If the hosted task will select Nodus, install
`backend/requirements-nodus.lock.txt` too and configure Nodus credentials on its
worker. Only the uploaded strict solver bundle is sent to Nodus; do not upload
the repository or credentials wholesale. Keep Nodus disabled until account
activation, credit and spending permission are confirmed.

The optional task entrypoint is `python workflows/main.py` from the repository
root. It requires the Render workflow runtime or official local task server;
running it as a plain script is not an HTTP application server. No deployment
manifest has been applied. A concrete preparation-only Blueprint and deployment
recipe are provided in `workflows/render.yaml` and `workflows/README.md`, based
on the current official workflow schema. They pin Python 3.14.7, both optional
SDK locks and the existing solver; keep automatic deployment and Nodus disabled.

Official references checked on 24 October 2026:

- [Render Python Workflows SDK](https://render.com/docs/workflows-sdk-python)
  documents task definitions, task chaining, retry/timeout options, trigger,
  polling and cancellation methods. Inspection of installed SDK 1.4.0 also
  confirmed its idempotency-key parameter and required retry wait argument.
- [Local development](https://render.com/docs/workflows-local-development)
  requires Render CLI 2.12.0 or later. Its task server runs on port 8120 and loses
  in-memory logs/results at shutdown. The Render CLI was not available on this
  laptop during this work; a real CLI task-server run remains unverified.

## Validation actually executed

On 24 October 2026:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_workflows.py backend/tests/test_nodus.py -q
.\.venv\Scripts\python.exe -m pip check
```

Result: **50 checks passed** (33 workflow checks and 17 existing Nodus checks),
with one pre-existing FastAPI/httpx
deprecation warning; dependency consistency check reported **No broken
requirements found**. Tests use temporary synthetic imports and do not open the
normal database. They cover the real local solver pipeline, invalid input before
execution, provider mismatch, allocation/accounting/baseline tampering, stage
order, changed inputs/audit, no retry on execution failure, downloaded envelope
reconstruction, timeout/cancellation, attempt reuse prevention and local-routing
exclusion. API checks confirm default local trace persistence, disabled hosted
execution writing no plan, mocked hosted metadata reaching the audit and failure
replanning inheriting the selected orchestration. The added log-forwarding case
checks bounded redaction, receipt hash and client-side evidence persistence
through mocked Nodus and Render transports. Actual SDK task registration and
its root/child functions were run
in-process using a test context; actual SDK HTTP serialization/parsing was
checked with `httpx.MockTransport`.

**Mocks and in-process task execution are not Render cloud evidence.** The SDK
was actually installed and inspected; no credential, task slug, deployed service,
hosted run, cloud logs, billed usage or full local CLI task-server run was
verified. A future authorized hosted run remains the required integration gate.
