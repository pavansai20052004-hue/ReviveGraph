# Render deployment checkpoint — 24 October 2026

**Status: prepared and authenticated; hosted deployment blocked by required
payment information. No workflow service or cloud task run was created.**
The participant confirmed that billing cannot be added now and requested
preserving the preparation. Do not keep retrying creation or replace this with
a different service type while claiming Render Workflows success.

## Actual completed preparation

- Render connector connected and workspace `My Workspace`
  (`tea-d69gif86fj8s73ciknig`) read successfully. The connector currently exposes
  services/logs but no workflow creation/task-trigger capabilities; the official
  CLI was used for workflow-specific operations.
- Official portable Render CLI **2.31.0** downloaded into ignored
  `data/render-readiness/`. Its ZIP SHA-256 matched the digest published on the
  official GitHub release. Browser/device login succeeded. Credentials remain in
  Render's own user configuration, not the repository or evidence.
- `workflows/render.yaml` passed both current published JSON-schema validation
  and authenticated `render blueprints validate` against the selected workspace.
  The returned plan was valid and named exactly one workflow:
  `revivegraph-recovery-workflow`. Validation did not deploy it.
- An isolated actual fixture import/local calculation measured all four child
  argument envelopes: 88,786; 89,198; 102,490; and 102,869 UTF-8 bytes. Final
  envelope: 103,898 bytes. All are below Render's documented 4 MB task-argument
  limit. These measurements are local preparation evidence, not cloud execution.
- Source review included **138 project files / 5,076,148 bytes**. Credentials,
  databases, environments, node_modules, generated runtime outputs and Git
  internals were excluded. The 47 changed files were inspected before commit.
- The participant explicitly authorized a private repository upload, deployment
  and one Render CPU test with a US$0.30 budget, leaving Nodus and automatic
  deployment disabled. That superseded the earlier no-push restriction for this
  specific private upload.
- New **private** repository:
  [pavansai20052004-hue/ReviveGraph](https://github.com/pavansai20052004-hue/ReviveGraph).
  Reviewed source committed/pushed as
  `f3102aa425abd5aa6cc45e3acc097838b2694f8a`. Prior local history, tags and archives
  were preserved. Original disclosed starting commit remains
  `8232884a0115e1626ec03991caf6c815ae177486`.

## Actual blockers

The single authorized `render workflows create` attempt returned:

> HTTP 402: Payment information is required to complete this request.

It directed the account owner to [Render Billing](https://dashboard.render.com/billing).
The participant subsequently said they cannot add billing and asked to preserve
the prepared deployment. No billing details, subscription, top-up or paid task
was submitted. A following workflow listing remained empty. API/SDK billing
usage is unavailable because no cloud run occurred.

A real CLI-local task-server attempt also failed before registration on this
Windows laptop:

```text
Error: GetFileAttributesEx /tmp: The system cannot find the file specified.
```

The official CLI's Unix-socket preparation uses `/tmp`. No global filesystem or
SDK patch was made to hide that failure. WSL reported
`REGDB_E_CLASSNOTREG`; Docker's Linux engine pipe was unavailable. The existing
in-process/SDK transport tests and real local calculation remain valid, but do
not establish a passing Render CLI local lifecycle or Linux deployment.

## Prepared service settings

| Setting | Value |
| --- | --- |
| Workspace | My Workspace / `tea-d69gif86fj8s73ciknig` |
| Repository | Private `pavansai20052004-hue/ReviveGraph`, branch `main` |
| Service name | `revivegraph-recovery-workflow` |
| Runtime / region | Python 3.14.7 / Singapore |
| Build | `python -m pip install --disable-pip-version-check -r backend/requirements-render.lock.txt -r backend/requirements-nodus.lock.txt` |
| Start | `python workflows/main.py` |
| Automatic deploy | Off |
| Nodus | Disabled |
| Compute | `flex`, zero configured retries on root/all four children |

The US$0.30 authorization was for one test, not a recurring service subscription.
Render's API provides no hard per-run dollar-cap field. Actual compute/retention
billing is separate from the previously approved Nodus and Adaption work.

## Resume after account billing is available

Reconfirm current account/source/price state before the deferred external action;
do not silently turn this checkpoint into an automatic retry. CLI credentials
can expire; rerun `render login` only if needed. The portable CLI stays under
`data/render-readiness/render.exe` and is not a committed dependency.

```powershell
$env:DO_NOT_TRACK = '1'
.\data\render-readiness\render.exe workspace set tea-d69gif86fj8s73ciknig -o json
.\data\render-readiness\render.exe blueprints validate workflows/render.yaml `
  --workspace tea-d69gif86fj8s73ciknig -o json
```

Check `render workflows list -o json` first to avoid creating a duplicate. When
the participant resumes deployment, the prepared creation command is:

```powershell
.\data\render-readiness\render.exe workflows create `
  --name revivegraph-recovery-workflow `
  --repo https://github.com/pavansai20052004-hue/ReviveGraph `
  --branch main --runtime python --region singapore `
  --build-command 'python -m pip install --disable-pip-version-check -r backend/requirements-render.lock.txt -r backend/requirements-nodus.lock.txt' `
  --run-command 'python workflows/main.py' --auto-deploy-trigger off `
  --env-var PYTHON_VERSION=3.14.7 --env-var PYTHONUNBUFFERED=1 `
  --env-var REVIVEGRAPH_NODUS_ENABLED=0 -o json --confirm
```

Keep the failed-attempt receipt. Never delete it to disguise a resubmission.
Once creation/build really succeeds, inspect the deployed Git commit and all
five registered task definitions/retry policies. Only then start the single
deferred calculation using the actual task slug. No task slug or workflow ID
has been invented in the current application configuration.

The locally prepared input is `data/render-readiness/task-input.json`, a single
positional workflow argument from an isolated real fixture calculation. It is
synthetic and contains no credentials. The future first test must use CPU
execution `local` inside Render; it is not a Nodus result. Download the run's
actual result, independently validate it through
`workflow_render.validate_download`, retain real task IDs/stage hashes/audit
and inspect actual usage. Wire the real slug/key into the backend only after
this gate. Preserve all existing approval and physical-verification boundaries.

## Evidence

Sanitized status is versioned in `docs/evidence/render-readiness-20261024.json`.
Generated review ZIP, exact file/hash manifest, CLI release receipt, schema and
semantic validation, task input and payload measurements remain under ignored
`data/render-readiness/`. The source-only ZIP requires dependency installation;
it is not an offline dependency bundle. Earlier archives/receipts are untouched.

This task changed no application behavior and did not rerun the already-passing
50 workflow/Nodus or 52 Adaption/assistant checks. It exercised the newly
available CLI/account/schema paths and the necessary isolated payload check.
Native Linux dependency installation, actual task-server execution, hosted
registration/calculation, cloud logs and real billing remain unverified.


## Recheck — 25 October 2026

The current Blueprint explicitly includes the now-public repository URL and main
branch. Authenticated semantic validation returned valid=true with one planned
workflow. Installed SDK remains render 1.4.0. Full backend workflow regressions
pass within the 176-test suite. No creation, deployment or paid execution was
retried; the recorded billing stop and Windows task-server limitation remain.
This is preparation/source validation only, not hosted integration completion.
