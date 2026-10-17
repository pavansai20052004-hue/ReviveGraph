# ReviveGraph foundation 0.1.0 checkpoint

Actual checkpoint preparation date: **16 October 2026 (Asia/Kolkata)**. This records disclosed work created before Hackyard Build 2026, 24–25 October, by a solo participant with OpenAI Codex assistance. Earlier dated preparation records remain in [PRE_EVENT_WORK.md](../PRE_EVENT_WORK.md).

This folder was not a Git repository when checkpointing began. It has now been initialized locally. At preparation time neither a Git author name/email pair nor an explicit author identity in the environment was available. The local commit and annotated tag therefore remain **pending author identity**; no identity has been invented or written to Git settings. Intended commit message: `Checkpoint disclosed ReviveGraph foundation 0.1.0`. Intended new annotated tag: `pre-event-foundation-v0.1.0`; an existing tag must never be overwritten. No push or publication is authorized by this checkpoint.

The commit/tag identifiers and recovery ZIP SHA-256 belong in the external checkpoint receipt/final report. This document deliberately does not embed its own future commit hash. Source is staged for review/commit. A source-only archive can be built directly from the reviewed Git index tree even while author identity is unavailable.

## Implemented application boundary

The working foundation is **fixture registration → two-file CSV preview → transactional import → inventory → deterministic compatibility inspection**. It includes the React/TypeScript/Vite shell, Tailwind/shadcn-compatible primitives, FastAPI, SQLite schema bootstrap, immutable content/version pins, individual assessment assertions, safe commit retry and initial/current component locations. The API and schema details are in [FOUNDATION_CONTRACT.md](FOUNDATION_CONTRACT.md).

| Planned capabilities | Checkpoint implementation status |
| --- | --- |
| 1 Dashboard | Inventory counts/statuses from the backend; optimization says “Not calculated” |
| 2 Computer Inventory; 3 Component Inventory; 4 Bulk CSV Import | Computers/Components tabs, details, search/filter, bounded UTF-8 preview, row/field errors, atomic import and idempotent retry |
| 5 AI Diagnosis; 12 Autonomous AI Agent | Unimplemented; provider/model undecided |
| 6 Component Health Assessment | Imported assertion/evidence inspection only; manual editing and human physical review unimplemented |
| 7 Compatibility Graph; 8 Smart Parts Matching | Deterministic table/list and complete-configuration inspection; graph visualization, allocation and reservation unimplemented |
| 9 Recovery Optimizer; 10 Budget and Resource Constraints | Operation assumptions registered; production CP-SAT, configuration selection and budget/time optimization unimplemented |
| 11 Recovery Simulator; 13 Failure Replanning | Unimplemented |
| 14 Human Approval; 15 Repair Work Orders; 16 Recovery Verification | Unimplemented, including revision-bound approval and transactional reservations |
| 17 Impact Analytics | Basic inventory counts only; no measured recovery, physical repairs or environmental estimates |
| 18 Reports and Audit Trail | An internal import audit event is stored; report/export and full lifecycle audit interfaces unimplemented |

The synthetic fixture contains **12 institution-owned desktop records and 31 physical-component IDs**. Its starting classification is 0 confirmed usable, 8 known unusable and 4 uncertain. Health, compatibility and ownership/availability eligibility remain distinct. Unknown decisive fields block use; synthetic assertions are simulation-only. Authored dates preserve supplied precision and remain separate from actual import timestamps. No imported author label is treated as a technician approval.

## Design references preserved

- [Native Figma Design file](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV)
- [Clickable synthetic demo prototype](https://www.figma.com/proto/Z3UwUmtqAq7HsMWLeYgcpV/ReviveGraph?node-id=6-66&starting-point-node-id=6%3A66&scaling=scale-down)
- [UI plan and frame references](UI_PLAN.md)
- Native-design previews in `docs/design-previews/` and actual application previews in `docs/implementation-previews/`

The native file is hosted in Figma; its editable contents are not an offline `.fig` export inside this source archive. Figma plan counts, costs, allocations and simulated outcomes remain illustrative design content. The three-page Starter-plan organization and remaining design states are documented in UI_PLAN. No Figma content changes are part of this checkpoint.

## Version pins

| Item | Version / identity |
| --- | --- |
| Frontend / backend foundation | `0.1.0` |
| Fixture directory | `datasets/synthetic-v1/` |
| Fixture ID / manifest version | `revivegraph-synthetic-v1` / integer `1` |
| CSV import contract | `v1`, unchanged columns |
| Board-profile schema | `toy-board-profiles-v1`; profile records version `1` |
| Operation-cost schema | `operation-costs-v1`, integer INR paise and technician minutes |
| Preparation scenario schema | `synthetic-scenarios-v1`; handwritten allocations are evidence only |
| SQLite schema | `PRAGMA user_version = 1` |
| Inspection engine | `desktop-inspection-v1` |
| Exact dependencies | `backend/requirements.lock.txt`, `frontend/package-lock.json` |

Fixture registration hashes the exact bytes of all six fixture files plus the inspection rule version. A batch also binds fleet/mode and both CSV hashes. Conflicting fixture/profile versions are rejected; a different running inspection engine fails closed. The tracked `.gitattributes` disables line-ending conversion to preserve exact source/fixture bytes despite the existing global `core.autocrlf=true` setting; no global setting is changed.

## Previously executed validation

The following results were **previously executed during foundation development on 16 October 2026**, as recorded in PRE_EVENT_WORK. They were reviewed for this checkpoint and **were not rerun merely to create the checkpoint**.

| Prior check | Recorded result |
| --- | --- |
| Backend pytest | 30 passed, including preview isolation, invalid/duplicate references, induced mid-insert rollback, safe/concurrent retries, hash/key/rule conflicts and an actual backend process restart |
| Chromium end-to-end flow | 1 passed: invalid preview → valid preview without inventory writes → import 12/31 → evidence/compatibility inspection → delayed stale-response protection → 390 px layout |
| TypeScript typecheck / production build | Both exit 0 |
| Locked setup / dependency consistency | Setup exit 0; npm clean install succeeded; pip reported no broken requirements |
| Original preparation oracle | Exit 0; all 11 restricted tiny expectations and both feasible example operation totals valid |
| Visual inspection | Actual desktop/390 px screenshots inspected; browser page-error collection empty |

The prior backend run emitted one upstream Starlette/httpx TestClient deprecation warning. No full accessibility audit, lint pass, solver test, physical hardware test, repair verification or performance benchmark is claimed. Checkpoint-only checks inspect ignore behavior, the exact staged files, source/secret exclusions and ZIP contents/integrity; they do not establish new application behavior.

The reviewed source inventory has 56 files, including seven intended PNG previews. Git's default staged whitespace check flags preserved CRLF line endings in the backend dependency lockfile and extra EOF blank lines in several files. Those formatting warnings are recorded without rewriting existing source/lockfile bytes during this checkpoint. Archive verification compares exact bytes rather than normalizing them.

## Startup and recovery

On Windows, install Python 3.12+ and a suitable recent Node.js LTS release. The prior validation used Python 3.14.7, Node 24.19.0 and npm 11.17.0. From the restored project folder:

```powershell
.\scripts\setup.ps1
```

Then start separate terminals:

```powershell
.\scripts\start-backend.ps1
```

```powershell
.\scripts\start-frontend.ps1
```

Open `http://127.0.0.1:5173`. A new database starts empty. Use **Import CSV → Register synthetic-v1 → Use bundled CSV pair → Preview both files → Commit batch**. SQLite normally persists at `data/revivegraph.sqlite3`. README contains direct commands if local PowerShell policy blocks helper scripts.

The recovery ZIP lives under ignored `backups/`, contains the reviewed source, both lockfiles, tests, documentation, all six fixture files, the preparation oracle and seven intended preview PNGs. It excludes `.git`, databases, credentials, virtual environments, node_modules, build/test outputs and logs. Extract its `ReviveGraph/` folder into a new location, reinstall locked dependencies, then import the fixture to recreate demo inventory. **The archive requires dependency installation; it is not an offline dependency bundle.** It does not preserve live database state or native Figma content.

## Known limits and onsite work

Only the constrained DDR3/DDR4 desktop UDIMM and 2.5-inch SATA toy universe is supported. CSV v1 inserts only and requires installed locations to refer to a computer in the same uploaded pair. General fixture/evidence upload, manual human assessment editing, physical review, public authentication/deployment and interactive graph rendering are unimplemented. The local actor label is not verified identity. No production optimizer or computed recovery plan is served; handwritten feasible examples and the preparation oracle remain separate evidence.

**Donor-demo risk:** `RG-RAM-07` is not guaranteed to be selected by the eventual optimizer because stock `RG-RAM-15` avoids extraction and is cheaper. During onsite integration, choose a failure from an actual validated computed allocation and inspect the alternative/no-spare outcome. Do not force a handwritten or Figma allocation while claiming unconstrained optimality.

Substantial production optimization, scenario replanning, approval/reservations, work orders and verification integration remain planned onsite work. **Fetch overlaps the proposed onsite schedule, but its exact hours are unconfirmed.** No overlap duration or confirmed availability schedule is invented; confirm Fetch timing and the actual Hackyard build window before finalizing onsite milestones.
