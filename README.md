# ReviveGraph

ReviveGraph helps colleges and refurbishment centres recover usable desktop configurations by reallocating compatible, healthy components within repair-resource limits.

**Status — 21 October 2026, disclosed version 0.2.0:** the local synthetic flow works from **fixture registration → CSV preview → atomic import → inventory/evidence → deterministic compatibility/interactive graph → CP-SAT allocation and greedy comparison → selected donor failure/replanning → explicit approval/reservations → work orders → simulated verification → audit JSON export**.

Built for Hackyard Build 2026 at IIT Guwahati, 24–25 October 2026, by a solo participant. The participant explicitly authorized advancing the central implementation before the event. Every addition is preparation, recorded in PRE_EVENT_WORK; it must not be relabeled as onsite work. The revised BUILD_PLAN proposes further meaningful onsite advancement. Exact Fetch overlap hours remain unconfirmed.

The native Figma design, original synthetic-v1 files, preparation oracle, `pre-event-foundation-v0.1.0` tag and original source ZIP/receipt are preserved. AI, accepted-health editing, reviewed physical evidence and physical execution are not implemented. **No physical repairs, diagnostic measurements or environmental savings are claimed.**

**Visual update — 20 October:** the participant's supplied dashboard screenshot is now the primary interface reference. Its compact dark sidebar, header, cards, table borders and hierarchy are implemented across the live workspaces. Dashboard uses actual fleet/alert data, discrete Recharts solver/greedy/parent comparisons, persisted workflow progress and a real audit feed. Reports now has a dedicated read-only interface and JSON export. [Desktop dashboard](docs/implementation-previews/reference-dashboard-desktop.png), [390 px dashboard](docs/implementation-previews/reference-dashboard-mobile.png) and [Reports](docs/implementation-previews/reference-reports-desktop.png) show actual isolated-test renders; no industrial metrics, generated history or live AI claims were copied.

## Dataset and actual computed result

Import **12 institution-owned synthetic computers and 31 uniquely identified components**. Initial classification is **0 usable, 8 known unusable, 4 uncertain**; uncertainty is not proof of broken physical hardware. Synthetic health assertions, toy board profiles and cost/time assumptions are explicitly authored inputs.

With budget **250,000 paise (₹2,500)** and **330 technician minutes**, the implemented solver returns **7 usable final / 7 newly recovered candidates, 215,000 paise (₹2,150), 299 minutes and 7 transfers**, with all four objectives and stable tie-breaking proven OPTIMAL in the validated run. The same-input greedy baseline reaches the same main-fleet totals. The restricted tiny trap proves 2 versus greedy's 1; no main-fleet uplift is claimed.

The actual computed donor is `RG-SSD-10` (PC-09 → PC-03). Its failure produces a revised plan substituting `RG-SSD-11` (PC-11 → PC-03), with the same count/cash/time and proven optimum. Stock `RG-RAM-15` is selected instead of the old handwritten donor `RG-RAM-07`. Always choose a demonstration failure from actual output. The fixture's handwritten allocations remain separate feasible preparation evidence, not runtime results. See [all 18 capability statuses and allocation](docs/IMPLEMENTATION_STATUS.md).

## Stack and supported boundary

| Area | Technology / current use |
| --- | --- |
| Interface | React, TypeScript, Vite, Tailwind, shadcn-compatible Radix/CVA primitives and Lucide icons; screenshot-led compact navy operations console |
| Graph | React Flow interactive inspection driven by actual backend decisions; full table/reason alternative retained |
| Backend | Python, FastAPI, SQLite via sqlite3 |
| Allocation | OR-Tools CP-SAT 9.15.6755, independent output validator, same-snapshot greedy baseline |
| AI / charts | Provider/model undecided and no AI requests; Recharts displays actual discrete plan comparisons |

The constrained model supports desktop DDR3/DDR4 non-ECC unbuffered UDIMM and one 2.5-inch SATA drive. Fixed motherboard/CPU/base assemblies do not move. Unknown health or decisive compatibility fields block allocation; one physical part cannot be used twice, including retained parts. Compatibility, allocation, ownership and hard budget/time constraints are deterministic. AI cannot invent hardware facts or approve repairs.

## Start locally on Windows

Install Python 3.12+ and a recent Node.js LTS release. The development environment used Python 3.14.7, Node 24.19.0 and npm 11.17.0. Setup uses exact lockfiles:

```powershell
.\scripts\setup.ps1
```

Start separate terminals from this folder:

```powershell
.\scripts\start-backend.ps1
```

```powershell
.\scripts\start-frontend.ps1
```

Open [ReviveGraph](http://127.0.0.1:5173); backend [API documentation](http://127.0.0.1:8000/docs). Both bind to localhost. Stop with Ctrl+C. If PowerShell policy blocks helper scripts, use equivalent commands without activating the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
npm --prefix frontend ci
```

Then, in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

```powershell
npm --prefix frontend run dev
```

SQLite persists at `data/revivegraph.sqlite3`; nothing is automatically seeded. Optional `REVIVEGRAPH_DB` selects a separate database. Schema 2 transactionally adds recovery tables to v1 while preserving inventory/evidence. **Before first upgrading valuable saved data, stop the backend and copy the SQLite file to a backup location.** Validation used isolated databases and did not migrate or reset the normal database. The original source ZIP is not a live database backup and still requires locked dependency installation.

## Demonstration sequence

1. Choose **Start synthetic import (or Import CSV) → Prepare demo preview → Commit batch → View imported inventory**. The shortcut registers the pinned fixture and validates both bundled CSVs; committing remains a separate explicit action. Manual registration/file selection remains available. Inspect the initial blockers and per-subject evidence. Preview errors name the file/row/field; invalid batches cannot commit.
2. Open **Compatibility Graph**. Select target/part nodes to inspect deterministic reasons and separate health/ownership/physical eligibility. The graph is a focused view; the complete table remains available.
3. Open **Recovery Optimizer**. Enter **₹2,500 / 330 minutes** and calculate. Inspect final configurations, complete operation charges, proof status and greedy totals.
4. Open **Live Recovery Simulation**. Select a transferred donor from the actual result and inject failure. Inspect before/after IDs and totals. Select the original plan to see stale status and disabled approval.
5. Review the exact revised plan ID/hash, acknowledge **simulated work only**, and approve. Rejection is also available before approval. The local actor is a supplied demo label, not authenticated technician identity. Reservations lock parts and targets in this execution context.
6. Create work orders. Use **Show next available task** to open a prerequisite-ready operation; filter/search the queue or follow named dependency links. Saved checklists and evidence remain visible after reload. Complete target preparation and all donor/displacement removals before installations. Prerequisites may belong to another order. Check each required item explicitly and enter authored simulation evidence references; the app does not run diagnostics or wipe drives.
7. Record pass, fail or inconclusive **simulated** verification. Pass requires completed work, all checks and matching final simulated installed IDs. Export audit JSON from Optimizer/Simulation.
8. For another run, use **Use a new rehearsal context** in Optimizer. After any step starts, failure pauses unfinished work and preserves completed evidence/locations. Automatic reconciliation is unimplemented; review that history and begin an independent context rather than repeating old steps.

Simulation never changes physical component locations or health evidence. Restart preserves plans, reservations, work progress and verification. Physical repair counts remain zero. Environmental estimates remain unavailable because no sourced factors exist.

## Validation

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\validate_synthetic_fixture.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Stop local development servers using 8000/5173, then run:

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

Playwright starts separate servers with an isolated SQLite file under ignored `data/`. It never resets normal inventory. It exercises import/evidence/compatibility regressions, graph interaction, computed planning/failure/stale approval, revision acknowledgement reset, approval, dependent steps, simulated verification, report download and desktop/390 px layouts.

Actual 20 October core checks: **65 backend tests passed**; frontend typecheck/build, pip dependency consistency and the unchanged preparation oracle passed. After the screenshot redesign, **19 focused backend tests passed** (six new audit-read cases plus thirteen lifecycle regressions), **all 3 Chromium flows passed**, and frontend typecheck/build/dependency-tree checks passed. To leave the normal app open, run browser checks from `frontend/` with `npx playwright test --config playwright.reference.config.ts`; this starts separate servers on 18100/15173 and a fresh isolated database. One upstream Starlette/httpx TestClient deprecation warning remains. Formal accessibility/security audits, hardware diagnostics and physical repairs are not claimed. Exact evidence is in PRE_EVENT_WORK.

An optional acceptance harness uses a temporary database, computes/replans, records **automated test approval/check evidence**, reopens persistence and records seven authored simulation passes. Choose a new output filename:

```powershell
.\.venv\Scripts\python.exe scripts\rehearse_recovery.py --output data\my-recovery-rehearsal.json
```

This is executed test evidence, not human technician approval. Its JSON receipt contains actual results and report history; it never becomes solver input.

## Documentation, design and remaining work

- [Product specification](docs/PRODUCT_SPEC.md): all 18 planned capabilities and acceptance criteria.
- [Architecture](docs/ARCHITECTURE.md), [foundation contract](docs/FOUNDATION_CONTRACT.md), [recovery contract](docs/RECOVERY_CONTRACT.md): supported rules, actual APIs/schema/version pins and deliberate deviations from earlier proposals.
- [Capability status](docs/IMPLEMENTATION_STATUS.md), [fixture specification](docs/FIXTURE_SPEC.md), [build plan](docs/BUILD_PLAN.md), [UI plan](docs/UI_PLAN.md), [pre-event disclosure](PRE_EVENT_WORK.md).

The [native Figma design](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV) remains unchanged; its illustrative plan counts, prices and allocations differ from computed results. Application previews: [Optimizer](docs/implementation-previews/optimizer-computed-desktop.png), [Simulation](docs/implementation-previews/simulation-verified-desktop.png), [390 px Simulation](docs/implementation-previews/simulation-verified-mobile.png), [verification checklist](docs/implementation-previews/simulation-verification-checklist.png). Inventory and Compatibility previews are in the same directory.

Remaining work includes manual accepted-health editing/physical review, real profile evidence, physical execution, post-start reconciliation, AI adapter/agent orchestration, general fixture/evidence uploads, richer impact/report formats and production authentication. Only one plan may be approved per simulation context, conservatively protecting shared donor/removal operations. No deployment, push, publication, paid service or new release tag was made.

The [official event rules](https://hackyard.org/build2026/rules) were checked on 16 October 2026. Keep the exact pre-event starting snapshot and a separate dated onsite record; attendance/selection and later rule changes are outside this implementation evidence.


**Workflow update - 21 October 2026:** the dashboard now recommends the next action from persisted state and opens the current revision even if an older plan was selected earlier. A compact Import / Inspect / Plan / Approve / Verify journey distinguishes available evidence from verified evidence. Work takes priority after approval, with ready-task navigation, progress, order filters and saved evidence. Failure comparisons show changed assignments first, actual resource deltas and an optional full allocation view. On small screens the active work queue precedes secondary scenario controls. No automatic checklist completion or physical verification was added. See [current desktop](docs/implementation-previews/effective-dashboard-desktop.png), [work queue](docs/implementation-previews/effective-simulation-desktop.png), [390 px work queue](docs/implementation-previews/effective-simulation-mobile.png) and [allocation changes](docs/implementation-previews/effective-allocation-changes.png).


**Travel feature freeze - 21 October 2026:** development is frozen. See [travel readiness and manual synthetic rehearsal](docs/TRAVEL_READINESS.md) for the separate rehearsal database/address, installed-dependency offline startup evidence and restore limits. Post-start recovery/reconciliation, renewed approval and their new tests are reserved for onsite work. The new source archive requires dependency installation; it is not an offline bundle.


**Final travel rehearsal - 22 October 2026:** the complete automated browser simulation passed all 12 requested stages under scoped external-network restrictions, including both-service restart, saved-evidence restoration and audit download. It recorded 28/28 automated steps and seven authored simulated passes, with zero physical repairs. Your separate manual run remains incomplete at three saved steps and was not modified. See [actual results, offline limits and repeatable click script](docs/FINAL_REHEARSAL_2026_10_22.md). Feature development stays paused until the event; post-start reconciliation and renewed approval remain onsite work.


**Onsite continuation — 24 October 2026:** the participant explicitly resumed development after the official build started. New code adds an opt-in Nodus CPU adapter, a four-stage validated calculation pipeline, optional hosted Render Workflows orchestration, and a grounded Agent37 plan assistant in Diagnostics. Local CPU and local orchestration remain the defaults. The assistant's explicit local evidence summary works without an AI call. See [Nodus setup](docs/NODUS_INTEGRATION.md), [assistant setup and boundaries](docs/ASSISTANT_INTEGRATION.md), [workflow setup](docs/WORKFLOWS_INTEGRATION.md) and the separate [onsite work record](ONSITE_WORK.md) for actual checks. Live Nodus/Agent37 runs are blocked by account activation; Render has not been deployed. Provider mocks and SDK tests are not cloud success. Earlier freeze/status statements above describe the preserved pre-event snapshot.

The isolated onsite preview is available at `http://127.0.0.1:15274` while its
local processes run, with backend `http://127.0.0.1:18274` and a separate ignored
`data/onsite-preview-20261024.sqlite3`. It starts empty so you can explicitly
import the fixture yourself; your normal database and past rehearsals are kept.
To restart this workspace, use two PowerShell terminals from the repository:

```powershell
$env:REVIVEGRAPH_DB = Join-Path $PWD 'data\onsite-preview-20261024.sqlite3'
.\.venv\Scripts\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 18274
```

```powershell
$env:REVIVEGRAPH_API_TARGET = 'http://127.0.0.1:18274'
npm --prefix frontend run dev -- --port 15274 --strictPort
```

**Adaption increment — 24 October 2026:** a separate synthetic explanation
dataset now has 12 training examples and four held-out examples, reproducible
fixture/rule hashes and a separately pinned official SDK. One real, explicitly
authorized Adaption run succeeded after a one-credit estimate. Its reported
dataset score changed from 4.0 to 8.6 (D to B); this is not a measured Agent37
answer improvement. All 12 adapted selections passed exact source-answer checks.
Optional bounded reference examples can be enabled for Agent37; canonical
current-plan facts and deterministic solver decisions remain authoritative.
Missing/invalid artifacts fall back to the existing behavior. No live Agent37
call or normal-database change was made. See [commands, safety boundaries and
limitations](docs/ADAPTION_INTEGRATION.md), [sanitized actual-run evidence](docs/evidence/adaption-20261024.json)
and [onsite disclosure](ONSITE_WORK.md).

**Render deployment checkpoint — 24 October 2026:** the participant authorized
the reviewed source upload to the private
[ReviveGraph repository](https://github.com/pavansai20052004-hue/ReviveGraph).
Render CLI authentication and both Blueprint validations passed, but workflow
creation returned HTTP 402 requiring payment information. The participant cannot
add billing now and asked to preserve the preparation. No hosted workflow or
task run was created. See [exact status and resume commands](docs/RENDER_DEPLOYMENT_STATUS.md).
