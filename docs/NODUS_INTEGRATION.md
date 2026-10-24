# Nodus CPU execution — onsite increment, 24 October 2026

The disclosed `configuration-cpsat-v1` solver, local independent validator, fixture, inventory importer and recovery lifecycle already existed before the event. This increment adds a transport boundary; it does not claim to invent or reimplement those features onsite. The native Figma design and all pre-event records remain unchanged.

## Smallest integrated boundary

The existing `POST /api/v1/plans` accepts optional `execution: "local" | "nodus"`; omission retains local CPU. Idempotency fingerprints include this field. There is no database migration. Saved plans and their audit exports gain an `execution` object. Old plans without it are displayed as local CPU. Failure replanning inherits the parent's provider; a remote replan is another paid job, not an automatic free fallback. Post-start reconciliation and renewed approval are not part of this increment.

The Optimizer exposes an explicit execution choice, identifies persisted local/Nodus results and shows the remote job ID. Nodus requires a server-side opt-in environment variable in addition to the request selection. Local execution does not import the optional Nodus SDK. This remains an unauthenticated localhost application; do not expose its spending-capable endpoints to the public internet.

Nodus Jobs were chosen over warm Functions because this first bounded calculation needs no deployed service or idle workers. The worker invokes the same production solver; `scenarios.json`, the preparation oracle, handwritten allocations, SQLite databases, Git history, credentials and environment files are never uploaded. A temporary allowlist contains five Python package files, pinned solver dependencies, a source manifest and the exact synthetic request snapshot. This first remote boundary is simulation-only.

## Trust and evidence

Protocol `revivegraph-cpu-v1` pins engine, inspection rule, validator and source SHA-256 identities. It hashes canonical UTF-8 JSON input/output. The worker checks uploaded source file hashes. After the SDK's documented download integrity check, the laptop checks response hashes/version pins, rebuilds allocation eligibility, one-use constraints, the complete operation ledger and hard budget/time totals, and recomputes the same-input greedy baseline. Only a valid FEASIBLE/OPTIMAL incumbent can enter the existing persistence flow, which rereads the snapshot and reservations before saving. Remote optimum/proof metadata is **reported by the pinned worker**, not mathematically re-proven by this transport validator.

Each attempt writes ignored `data/nodus-runs/<request-identity>/receipt.json` before submission and records the handle immediately after creation. A repeated attempt for that request is blocked even after an ambiguous failure; no automatic paid resubmission and no silent local fallback. Inspect the recorded job before choosing a new key. This is a conservative attempt guard, not a durable distributed job queue or automatic recovery service. If the process dies after acceptance but before persistence, manual job/result reconciliation is required.

Configured limits are **one CPU, 2 GiB RAM, US$0.10 maximum per job, five-minute job timeout and 360-second client wait**. Source upload/create, provider HTTP retries and evidence collection occur outside that wait; it is not an end-to-end request deadline. The frontend allows seven minutes before its own request timeout; that timeout does not prove the remote job stopped. A provider cost-limit suspension is handled by the bounded wait and cancellation path. User authorization covers one initial real calculation using event credits. The app's later remote calculations require deliberate operator actions and available account credits. INR repair assumptions and USD compute spend are separate quantities. The original solver's aggregate search limit remains 60 seconds. Remote dependency installation happens inside the job and requires package-registry egress; the existing laptop's local demo still works independently of Nodus.

Receipts retain job ID, canonical input/source/output/download hashes, available safe provider usage/cost fields and sanitized log text. Null usage means not reported, never zero cost. URLs, including signed download URLs, and obvious token fields are redacted. Account keys are read by the provider SDK, never put in the uploaded source or receipt. Generated evidence stays ignored; publish only reviewed sanitized extracts later. A provider timeout/cancel does not prove no billable work happened; inspect its account record.

## Setup and one calculation

Install the separately locked optional SDK into the existing project environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-nodus.lock.txt
.\.venv\Scripts\nodus.exe login
.\.venv\Scripts\nodus.exe whoami
```

Confirm the selected organization has event credit and that no paid top-up/auto-recharge is required or enabled on your behalf. Account login, redemption or account review must be completed by the participant; do not paste credentials into chat.

For a new isolated calculation (no approval or verification is authored):

```powershell
$env:REVIVEGRAPH_NODUS_ENABLED = '1'
.\.venv\Scripts\python.exe scripts\calculate_nodus.py --output data\onsite-nodus-first
```

For normal UI use, set the opt-in in the backend terminal before starting the existing backend, import into your chosen simulation database, choose Nodus CPU in Optimizer and calculate. Leave Local laptop CPU selected for ordinary offline operation. Never use the original synthetic fixture as an output location.

## Official references inspected

- [Install and login](https://nodus-compute.ai/docs/getting-started/install/): official package is **nodus-compute**, imported as `nodus`; it includes the Windows CLI. The unrelated PyPI package named `nodus` was not installed.
- [Python Jobs guide](https://nodus-compute.ai/docs/guides/python/jobs/): source upload, CPU/memory requests, timeout, maximum cost, logs and downloaded outputs.
- [Job SDK reference](https://nodus-compute.ai/docs/reference/python/nodus-job/): `Job.run`, `wait(timeout=...)`, `status`, `logs`, `cancel` and output integrity checking.

Agent37 explanations and Render Workflows orchestration remain the next integrations. They must consume validated plan data and retain this deterministic boundary; neither is implemented by adding the Nodus adapter.


## Onsite workflow continuation — 24 October 2026

Calculations now run through the four-stage pipeline described in
WORKFLOWS_INTEGRATION.md. CPU provider and orchestrator remain separate. The
same bounded sanitized Nodus log excerpt/hash is included in its receipt and can
be retained by the laptop after a Render run, alongside provider IDs/hashes and
actual supplied usage. This has been checked with transport doubles; no Nodus
job was submitted. Render log retrieval and usage collection are separate,
unimplemented provider features. A per-job US$0.10 Nodus cap does not cover
Render orchestration charges or authorize further jobs after the initial run.
