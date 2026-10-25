# Free Render web demo — 25 October 2026

This is ordinary **web hosting**, separate from the optional native **Render
Workflows** integration. A web-service deployment does not establish that native
Workflows ran. The earlier Workflows creation returned HTTP 402 requiring payment
information; that historical receipt remains intact.

## Hosting configuration

Use the existing React build and FastAPI API in one same-origin service. The new
optional `revivegraph.web:create_web_app` factory mounts only `frontend/dist`, after
the API routes. The original local API factory/startup is unchanged. Missing
frontend output fails before opening a database.

`deploy/render-web.yaml` specifies Free compute, Singapore, Python 3.14.7,
Node 24.19.0, one Uvicorn worker, automatic deployment off and API health check.
The separately named `codex/render-free-demo` source branch preserves main and
earlier checkpoints. Both dependency lockfiles remain unchanged.

Build from repository root:

```sh
python -m pip install --disable-pip-version-check -r backend/requirements.lock.txt
npm --prefix frontend ci
npm --prefix frontend run build
```

Set `VITE_PUBLIC_DEMO=1` during the frontend build. Start:

```sh
python -m uvicorn revivegraph.web:create_web_app --factory --app-dir backend --host 0.0.0.0 --port $PORT --workers 1
```

At runtime, set `REVIVEGRAPH_DB=/tmp/revivegraph-demo.sqlite3`,
`REVIVEGRAPH_NODUS_ENABLED=0` and `REVIVEGRAPH_RENDER_ENABLED=0`.
Do not upload `.env.onsite`, credentials, the normal database, the rehearsal database,
or provider login caches. No paid-provider credentials are needed for this demo.

## Important demo boundaries

- Shared, unauthenticated synthetic workspace, not production hosting. Use only
  synthetic data. Other visitors can see and change the same fleet/history.
- The Free instance sleeps after 15 idle minutes and can take about a minute to
  wake up. The UI explains cold-start failures and provides retry.
- **SQLite changes are lost on sleep, restart or redeploy.** Import again after a
  reset. Export audit JSON before leaving. Reload within the same running process
  is persistence, not durable cloud storage.
- Free instances cannot attach persistent disks. This task does not migrate the
  existing database to Postgres or promise durable backups of hosted state.
- Calculations run on the free web instance CPU, labelled **Render demo CPU**.
  The app's execution identifier `local` means local to that server process.
  It is not Nodus execution or a native Render Workflow task run.
- Provider selectors remain visible for product consistency, but the backend
  rejects disabled Nodus/native-Workflow dispatch before making provider calls.
- All assessments, assumptions, checklists and verification remain synthetic or
  simulated. Physical repair totals remain zero.

## Preparation checks actually executed

- Two focused backend host tests passed: missing-build/no-DB side effect;
  static/API containment and a 12/31 preview followed by explicit commit.
- Production frontend typecheck/build passed with the hosted-demo flag enabled.
- Local production-host browser flow passed: real preview/commit when fresh,
  12/31 inventory, real CPU solve, reload, hosted notice at 1440/390 px, no 390 px
  horizontal overflow, and a mocked HTML 503 cold-start response followed by retry.
- The local host calculation returned OPTIMAL, seven candidates, INR 2,150 and
  299 minutes within INR 2,500/330. These are actual software results with synthetic
  cost/time inputs, not measurements or physical repairs.
- Independent focused review found no blocking issue. The cold-start HTML response
  concern was addressed and checked in the browser flow.
- Exact critical published Python/npm versions and Python 3.14 Linux wheels were
  checked read-only. Actual Linux installation and cloud execution remain gates
  until the deployment log and live endpoint checks pass.

Private local smoke receipts/screenshots are in ignored `data/free-web-smoke`.
An initial test assertion was narrowed to the two intended count fields because
the state response also includes health counts. A browser-driver viewport call was
corrected from the context to the page. These were test-driver fixes, not hidden
application failures. No already-passing full application suite was repeated.

## Deployment verification

Service creation starts the first build even with future auto-deployment off.
Require an actual `live` deploy, `/api/v1/health`, frontend/assets and the browser
import/calculation flow before claiming successful hosting. A Free-plan API request
can still encounter account-specific verification or quota limits; no card,
paid-plan upgrade or credit purchase is authorized by this configuration.

## Official sources

- [Free hosting](https://render.com/docs/free): eligible service types, idle/sleep,
  temporary filesystem and quotas.
- [FastAPI hosting](https://render.com/docs/deploy-fastapi): public port binding.
- [Native runtimes](https://render.com/docs/native-runtimes): Python plus Node/npm.
- [Compute plans](https://render.com/docs/compute-plans): Free resource limits.
- [Workflows pricing](https://render.com/docs/workflows-limits): distinct metered
  service. A free web deploy is not proof of this sponsor integration.
