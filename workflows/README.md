# Prepared Render workflow service

This folder contains source and a deployment recipe. It has **not** been pushed,
deployed or run on Render. `render.yaml` uses JSON syntax, which is valid YAML,
and declares a native `workflow` service supported by the official Blueprint
schema. Keeping the file here prevents an automatic root-level deployment.

Use the repository root as the service root: tasks import the existing backend,
and Nodus bundles source from `backend/`. Do not set `rootDir: workflows`.

| Setting | Prepared value |
| --- | --- |
| Source | The reviewed ReviveGraph Git commit, after a separately authorized push |
| Runtime | Native Python, pinned `PYTHON_VERSION=3.14.7` |
| Region | `singapore`, a preparation choice to review before creating the service |
| Build | `python -m pip install --disable-pip-version-check -r backend/requirements-render.lock.txt -r backend/requirements-nodus.lock.txt` |
| Start | `python workflows/main.py` |
| Auto deploy | Off |
| Task compute | `flex`, defined in `main.py`, not a service `plan` field |
| Automatic retries | Zero for root and all four children |
| Worker Nodus | Disabled until account activation, credentials and credit are verified |

Core locks retain OR-Tools `9.15.6755`; the optional Render lock pins SDK `1.4.0`;
the Nodus lock pins SDK `1.0.27`. Native Linux installation has not been tested.
The Python pin matches this laptop's verified interpreter; Render's build is a
separate gate. The source archive is not an offline dependency bundle.

After explicit push/deployment/spending authorization:

1. Connect the reviewed repository in the Render Dashboard and choose **New →
   Workflow**, Python 3, the region/build/start settings above. Alternatively,
   create a Blueprint using `workflows/render.yaml` as its custom file path.
   The linked source must include the backend, these task definitions and locks.
2. Review the chosen region and service name before creation. Keep automatic
   deployment off. Creating/registering the workflow and task runs are separate
   external actions; no such action has been performed here.
3. Inspect the build log and task list. Require exactly `recover`,
   `validate_input`, `execute_plan`, `validate_result`, and `generate_audit` and
   verify zero retries before any Nodus execution. Do not use a web service or
   add an HTTP health check; workflow task instances do not expose a port.
4. For the initial Render-only smoke test, leave Nodus disabled and request
   execution `local` through orchestration `render`. This runs the same CPU
   solver inside Render's task instance. It is **not** a Nodus result.
5. Copy the actual `workflow-slug/recover` task slug into the laptop's ignored
   `.env.onsite` as `REVIVEGRAPH_RENDER_TASK`. Add a backend-only `RENDER_API_KEY`
   and enable `REVIVEGRAPH_RENDER_ENABLED=1`. Do not commit credentials. Restart
   the backend and calculate using a fresh isolated simulation context.
6. Check task ID, four stage hashes, independently validated result and audit
   artifact. Inspect the account's real usage before claiming cost or credits.
7. Only after Nodus account activation: securely configure the worker's
   `NODUS_API_KEY` in Render Environment and set `REVIVEGRAPH_NODUS_ENABLED=1`.
   Do not copy a local login cache or `.env.onsite` into source. Confirm the
   account's credits and explicit spending cap before selecting execution
   `nodus`. The existing adapter caps a job at US$0.10, 1 CPU, 2 GiB and five
   remote minutes. Render orchestration has its own separate billed usage.

The API client records an attempt before submission and supplies an idempotency
key; it does not automatically repeat paid work. If a request fails, first check
the local receipt, Render task state and Nodus job state. A Render cancellation
is best effort and does not prove an external Nodus job was canceled. Do not
delete attempt receipts merely to retry.

Official references, checked 24 October 2026:

- [First workflow](https://render.com/docs/workflows-tutorial) describes linked
  Git source, native Python build/start configuration, registration and task runs.
- [Blueprint fields](https://render.com/docs/blueprint-spec) and the
  [published schema](https://render.com/schema/render.yaml.json) support
  `type: workflow`, native Python, required region/start command, environment
  variables and disabled automatic deployment; task compute stays in code.
- [Python version selection](https://render.com/docs/python-version) supports
  the fully qualified `PYTHON_VERSION` pin.
- [Secrets](https://render.com/docs/configure-environment-variables) belong in
  the service environment, not committed source.

The manifest has been parsed locally and checked for the intended service fields.
No Render CLI/API schema validation, Linux build, linked Git source or hosted
run is claimed. The official local task-server path additionally requires
Render CLI 2.12.0 or later; the CLI was not installed during preparation.
