# ReviveGraph

ReviveGraph helps colleges and refurbishment centres inspect damaged desktop fleets and prepare to reallocate compatible, healthy components within repair-resource limits. The disclosed application foundation supports inventory intake and deterministic compatibility inspection; fleet optimization and repair execution are planned onsite work.

**Status — 16 October 2026:** a React/TypeScript/Vite frontend, FastAPI backend and SQLite foundation are implemented and locally validated. The real flow is **fixture registration → CSV preview → atomic import → inventory → compatibility inspection**. The native Figma design, synthetic-v1 fixture and independent preparation oracle are preserved. Production optimization, scenario replanning, approvals, work orders, verification and AI integration remain unimplemented. No physical repairs or measured recovery performance are claimed.

Built for Hackyard Build 2026 at IIT Guwahati, 24–25 October 2026, by a solo participant. Attendance/selection status is outside this package. Preparation must be disclosed; substantial optimization, replanning and approval integration is reserved for the official onsite window.

## Intended demonstration

Import a **synthetic fleet of 12 institution-owned desktop computers** → assess available components → calculate a fleet recovery plan → inject a donor-component failure into a simulation → recalculate → obtain technician approval of the revised plan → create repair work orders → record simulated verification results. In fixture v1, none is initially confirmed usable: eight have a known faulty or missing blocker and four have unresolved health/profile evidence. The latter are planning-ineligible, not proven physically broken.

The fixture contains two hand-checked **feasible** 7-target allocations, not a proven full-fleet optimum or an application result. A simulated pass is never a technician-verified physical repair. Physical verification requires separately recorded real evidence.

## Stack and boundaries

| Area | Proposed technology |
| --- | --- |
| Interface — implemented | React, TypeScript, Vite, Tailwind CSS; shadcn-compatible tokens/primitives with Radix dialog |
| Graph / charts — later | React Flow / Recharts; current compatibility inspection uses a table/list |
| Backend / persistence — implemented | Python, FastAPI / SQLite via stdlib sqlite3 |
| Allocation — onsite | Google OR-Tools CP-SAT |
| AI — later | Provider-neutral adapter; provider and model undecided |

Compatibility, health eligibility, allocation and budget enforcement are deterministic backend responsibilities. AI may interpret logs, request bounded tools and explain evidence; it cannot declare compatibility, certify health, approve work or execute repairs. The initial hardware scope is desktop DDR3/DDR4 RAM and 2.5-inch SATA storage, with fixed motherboard/CPU assemblies and explicit supported profiles.

## Run locally on Windows

Use Python 3.12+ and a recent Node.js LTS release; this task was validated with **Python 3.14.7, Node 24.19.0 and npm 11.17.0**. Run from this project folder. Setup installs the exact dependency versions in the backend and frontend lockfiles:

```powershell
.\scripts\setup.ps1
```

In terminal 1:

```powershell
.\scripts\start-backend.ps1
```

In terminal 2:

```powershell
.\scripts\start-frontend.ps1
```

Open [ReviveGraph](http://127.0.0.1:5173). Backend API documentation is at [FastAPI docs](http://127.0.0.1:8000/docs). Both processes stay on localhost. Stop them with Ctrl+C.

If local PowerShell policy blocks helper scripts, use the equivalent commands directly, without activating the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
npm --prefix frontend ci
```

Then run the following in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

```powershell
npm --prefix frontend run dev
```

On a new database, choose **Import CSV → Register synthetic-v1 → Use bundled CSV pair → Preview both files → Commit batch → View imported inventory**. You can also choose the two real CSV files from `datasets/synthetic-v1/`. Preview errors identify file, row and field; invalid batches cannot commit. A successful fixture import shows **12 computers / 31 components**, with 0 usable, 8 known unusable and 4 unknown computers. Inspect a row, expand its evidence, or open Compatibility Graph for the deterministic list/configuration inspector.

The database persists at `data/revivegraph.sqlite3`; no inventory is automatically seeded on startup. An optional `REVIVEGRAPH_DB` environment variable selects a separate development database. Restarting the backend preserves registrations, batches, evidence, inventory and revisions. Back up the database while the backend is stopped; no destructive reset command is provided.

## Implemented behavior and limits

- Immutable fixture registration pins manifest, profiles, operation costs, source CSV hashes, scenario-evidence hash and the inspection rule version.
- Two-file previews persist only batch metadata. Commit revalidates the hashes/references/revision and writes inventory, assessments and the import event atomically. Identical retries return the original revision.
- Computers/Components tabs show backend records, current/initial locations, health assertions, usability blockers and evidence. Dates retain their supplied precision; authored synthetic assertions, actual import time and physical review are distinct.
- Hardware compatibility is independent from health/owner/availability eligibility. Unknown decisive fields block use. Complete RAM sets check slots, capacities and module combinations; synthetic evidence stays simulation-only.
- Dashboard counts come from the backend. Optimization says **Not calculated**. Diagnostics, optimizer and simulation screens show **Not implemented yet**. Manual evidence editing and human physical review are not implemented.

The local actor label is not production authentication. General fixture uploads, inventory updates, cross-owner transfers, graph visualization and public deployment remain later work. The two CSVs retain v1 columns; same-batch installed-location references and other implemented API clarifications are documented in [FOUNDATION_CONTRACT.md](docs/FOUNDATION_CONTRACT.md).

**Donor demo risk:** the eventual optimizer may prefer cheaper stock `RG-RAM-15` over donor-extracted `RG-RAM-07`. Choose a failure from an actual computed allocation during onsite integration; do not present a handwritten/Figma allocation as solver output.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\validate_synthetic_fixture.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

For the browser check, first stop any local backend/frontend using ports 8000/5173, then:

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

Playwright starts its own backend/frontend with a separate fresh SQLite database under ignored `data/`. It exercises CSV error handling, preview without inventory writes, commit, evidence details, compatibility, a delayed stale configuration response and a 390 px layout. It never resets the normal database.

Actual results on 16 October 2026: **30 backend tests passed; 1 Chromium flow passed; typecheck/build, dependency consistency and the unchanged fixture oracle passed**. The backend test run emits one upstream Starlette/httpx TestClient deprecation warning. No application failure remains in these checks. Rendered screenshots were inspected at desktop and 390 px; a full accessibility audit is still pending.

## Planning package

- [Product specification](docs/PRODUCT_SPEC.md): all 18 capabilities, priorities and acceptance criteria.
- [Architecture](docs/ARCHITECTURE.md): hardware rules, data entities, API contracts and optimization.
- [UI plan](docs/UI_PLAN.md): six screen briefs, design tokens, actual Figma frame links and remaining design states.
- [Build plan](docs/BUILD_PLAN.md): preparation, onsite milestones and future validation.
- [Synthetic fixture specification](docs/FIXTURE_SPEC.md): CSV/JSON assumptions, initial blockers, feasible plans and tiny-case proofs.
- [Implemented foundation contract](docs/FOUNDATION_CONTRACT.md): registration, hashes, evidence, SQLite transactions and actual API subset.
- [Pre-event disclosure](PRE_EVENT_WORK.md): factual preparation record.

The [native Figma design](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV) covers six desktop screens, representative 390 px Inventory/Simulation layouts and a clickable synthetic demo flow. It remains unchanged; its illustrative plan counts/costs need reconciliation after the real solver runs. [Application desktop preview](docs/implementation-previews/inventory-desktop.png), [compatibility preview](docs/implementation-previews/compatibility-desktop.png) and [390 px Inventory preview](docs/implementation-previews/inventory-mobile.png) show the implemented subset. The preparation oracle remains separate from application tests and production optimization.

## Event reference

The [official rules](https://hackyard.org/build2026/rules), checked 16 October 2026, allow disclosed pre-existing work and focus judging on onsite creation or material advancement. Maintain dated preparation records and a separate onsite change log when implementation begins.
