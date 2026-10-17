# Pre-event work disclosure

Project: ReviveGraph. Participant: solo. Intended event: Hackyard Build 2026, IIT Guwahati, 24–25 October 2026.

## Record — 16 October 2026 (Asia/Kolkata)

The opened ReviveGraph folder was empty when this task began. No local or ancestor `AGENTS.md` file was found; the instructions supplied in the chat were followed. This task created only these planning documents with AI assistance from OpenAI Codex:

| File | Pre-event contribution |
| --- | --- |
| `README.md` | Purpose, intended demonstration, proposed stack and current status |
| `docs/PRODUCT_SPEC.md` | All 18 planned capabilities, priorities, workflows and future acceptance criteria |
| `docs/ARCHITECTURE.md` | Proposed system/data/API contracts, constrained hardware model, deterministic optimization and AI boundaries |
| `docs/UI_PLAN.md` | Design tokens and Figma-ready briefs for six screens |
| `docs/BUILD_PLAN.md` | Proposed preparation/onsite schedule, baseline, validation cases and demo sequence |
| `PRE_EVENT_WORK.md` | This disclosure record |

No application implementation, dependency installation, CSV dataset, Figma design/prototype, AI provider integration, optimization run, application test run, performance measurement or physical repair was produced in this task. Documentation review is not software validation. No repository commit or release is claimed.

The 12-computer fleet is a planned synthetic demonstration, not collected hardware evidence. Costs, technician durations, health inputs and future verification in that demonstration must be identified as synthetic assumptions. No recovery count, measured diagnostic result or environmental saving has been established.

## Rules consulted

The [official Build 2026 rules](https://hackyard.org/build2026/rules) were checked on 16 October 2026; the page states it was updated 22 September 2026. They permit disclosed pre-existing tools, designs, datasets and foundations, while judging focuses on creation or material advancement during the official onsite window. This record does not assert selection, attendance confirmation or organizer approval of the project.

Technical planning references: [OR-Tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver) and [SQLite transactions](https://www.sqlite.org/lang_transaction.html). Listed technologies are proposed dependencies; none is claimed installed or integrated.

## Planned work, not yet completed

Further preparation may include a labeled synthetic fixture and a disclosed scaffold, as sequenced in `docs/BUILD_PLAN.md`. Substantial onsite work is planned to complete and integrate optimization, failure replanning, human approval, work orders and verification. These entries describe intent only.

For every later pre-event change, append its actual date, author/AI assistance, files or design links, reused source/license, implemented behavior, validation evidence and known limitations. At the event start, record the exact starting commit/archive hash and design/dataset versions; keep a separate dated onsite change log. Never backdate work or move pre-event implementation into the onsite record.

## Record — 16 October 2026: native Figma design

OpenAI Codex, working on behalf of the solo participant, created the [ReviveGraph native Figma Design file](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV) from the six existing planning documents. The file contains Foundations, Components and Screens pages; a `Demo Prototype` section on Screens; six desktop screen frames; representative 390 px Inventory and Simulation frames; and fourteen linked prototype states/branches. The [prototype starts at import preview](https://www.figma.com/proto/Z3UwUmtqAq7HsMWLeYgcpV/ReviveGraph?node-id=6-66&starting-point-node-id=6%3A66&scaling=scale-down). The Figma Starter plan limited the file to three pages, so a fourth page could not be created. No substitute application code was made.

The design uses shared variables, typography styles, editable auto-layout frames and native component variants. Illustrative asset/part IDs, 12-computer counts, costs, solver labels, scenario approvals and simulated verification appear solely as **design examples**. They were not imported as a CSV fixture, computed by an optimizer, executed as work orders or observed on physical machines. The AI suggestion in Diagnostics is labeled illustrative and remains separate from accepted human assessment.

Figma screenshots were rendered and visually inspected; layout fixes included a clipped Optimizer allocation row, Dashboard workflow spacing, a clipped Simulation footer and prototype dialog/button sizing. Native prototype reactions, start point, Inter font family and absence of full-UI image fills were read back. Four local preview PNGs were saved under `docs/design-previews/`. A live browser presentation run, formal contrast/keyboard review and application tests have **not** been completed. There is still no application implementation, synthetic CSV fixture, real diagnostic measurement, measured performance, physical repair or environmental impact result. The user-requested Fetch scheduling conflict was flagged in `docs/BUILD_PLAN.md`; exact Fetch hours remain unconfirmed.

## Record — 16 October 2026: synthetic fixture v1

OpenAI Codex, working on behalf of the solo participant, created `datasets/synthetic-v1/computers.csv`, `components.csv`, `board_profiles.json`, `operation_costs.json`, `scenarios.json` and `manifest.json`, plus `docs/FIXTURE_SPEC.md` and `scripts/validate_synthetic_fixture.py`. README, PRODUCT_SPEC and BUILD_PLAN were updated to reflect the actual fixture and remaining onsite work. All health states, toy profiles, part locations, INR paise amounts and technician minutes were authored for the simulation; there were no external hardware measurements, manufacturer certifications, supplier quotes or observed repair times. The CSVs retain the proposed architecture v1 import columns; JSON sidecars carry fixture-only profiles, costs, scenarios and summary metadata. The native Figma file was preserved unchanged.

The fixture has 12 synthetic institution-owned desktops and 31 uniquely identified physical parts. Starting classification under the conservative planning policy is 0 confirmed usable, 8 with a known faulty/missing blocker and 4 uncertain/not confirmed usable. A documented before-failure allocation of 7 targets costs 217,000 paise and 304 technician minutes; after a simulated failure of donor `RG-RAM-07`, a documented feasible alternative of 7 targets costs 215,000 paise and 299 minutes. These are manually justified **feasible examples**, not a production solver run, an exact full-fleet optimum or completed work. Eleven restricted small cases include a greedily suboptimal allocation, unique-part contention, unsupported/unknown eligibility and resource boundaries; the validator exhaustively enumerates only those tiny cases as a preparation oracle.

Validation actually run from the project root on 16 October 2026:

```powershell
& 'C:\Users\pavan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\validate_synthetic_fixture.py
```

Result: exit code 0; all 11 tiny cases matched their expected maxima, including greedy-trap maximum 2 versus baseline 1; inventory, provenance, ownership, locations, board profiles, initial blockers and both example operation totals passed. An independent read-only review checked the arithmetic and identified terminology/layout/evidence limitations; the usability wording and layout/donor checks were tightened before the final validator run. This is **preparation data validation only**. No application import, backend, optimizer, AI integration, live prototype update, approval transaction, work order execution, physical verification or environmental impact calculation was made. The Figma's illustrative R1/R2 counts, costs and allocations will need reconciliation after actual solver integration; no design values were changed or presented as measured results.

## Record — 16 October 2026: disclosed application foundation 0.1.0

OpenAI Codex, working on behalf of the solo participant, created and validated the registration → preview → transactional import → inventory → deterministic compatibility application foundation **before the event**. This code must be included in the pre-event starting snapshot. It does not belong in the future onsite work record.

| Created files / area | Actual pre-event work |
| --- | --- |
| `backend/revivegraph/{__init__,db,domain,imports,main}.py` | FastAPI application factory; SQLite schema/version bootstrap; immutable fixture/profile registration and SHA-256 pins; bounded CSV preview; atomic/idempotent commit; evidence/origin/current-location persistence; inventory and deterministic hardware/configuration/eligibility inspection |
| `backend/requirements.in`, `backend/requirements.lock.txt`, `pytest.ini`, `backend/tests/test_foundation.py` | Dependency input/fully pinned installed versions and 30 focused backend test cases, including parameterized cases |
| `frontend/package.json`, `package-lock.json`, `index.html`, `tsconfig.json`, `vite.config.ts`, `components.json` | React/TypeScript/Vite scaffold, Tailwind v4, local font dependency, Radix dialog/CVA shared primitives, shadcn-compatible configuration and exact npm lock |
| `frontend/src/{main,App}.tsx`, `api.ts`, `types.ts`, `styles.css`, `lib/utils.ts` | Shared six-item navigation and dark shell, backend dashboard counts, API client/types and responsive tokens/layout |
| `frontend/src/components/` | Import dialog, evidence inspection, Computers/Components tables/details, compatibility/configuration inspection, shared button/panel/badge/loading/error/empty primitives |
| `frontend/playwright.config.ts`, `frontend/e2e/import.spec.ts` | Real Chromium import/evidence/compatibility flow, stale-response guard case and 390 px layout check against an isolated test database |
| `scripts/{setup,start-backend,start-frontend}.ps1`, `.gitignore` | Windows setup/start helpers; generated environments, SQLite files and build/test outputs ignored |
| `docs/FOUNDATION_CONTRACT.md` | Actual API/schema clarifications, registration/hash policy, evidence precision, transactions and implementation limits |
| `docs/implementation-previews/{inventory-desktop,compatibility-desktop,inventory-mobile}.png` | Screenshots of the running application, visually inspected |

README, PRODUCT_SPEC, ARCHITECTURE, UI_PLAN, BUILD_PLAN and FIXTURE_SPEC were updated for the actual implemented subset and remaining milestones. The pre-existing six files in `datasets/synthetic-v1/` and `scripts/validate_synthetic_fixture.py` were preserved. The original authored fixture and Figma design were reused as project preparation; Figma context/screenshots were read using the design-to-code workflow and the native file was not edited. React/FastAPI/Tailwind/Radix/font and test dependencies were installed through package managers; exact versions are recorded in the lockfiles and remain subject to their upstream package licenses. No external hardware dataset or diagnostic measurements were added.

Per-subject assessment records now preserve actual supplied provenance/evidence refs and hash-matched fixture source/date/author context. The fixture's `2026-10-16` remains **date precision**; missing base evidence refs remain null. The manifest's synthetic author label does not become a technician identity or approval. Actual import UTC time/importer are separate fields. Changed CSV files do not inherit the original authored date/label. Physical-provenance imports remain pending human review, blocked from eligibility/confirmed usability; no human-review mutation workflow was implemented. The complete implemented schema/API clarifications are in `docs/FOUNDATION_CONTRACT.md`.

Validation actually run from the project root, unless stated otherwise, on 16 October 2026:

```powershell
.\scripts\setup.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\validate_synthetic_fixture.py
```

From `frontend/`:

```powershell
npx playwright install chromium
npm run test:e2e
npm run typecheck
npm run build
```

Results: setup exit 0 (backend lock confirmed, npm clean install succeeded); **30 backend tests passed**; **1 Chromium flow passed**; typecheck and production build exit 0; pip reported no broken requirements; unchanged preparation oracle exit 0 with all 11 tiny expectations and both feasible example totals still valid. Backend tests include an induced mid-component-insert abort with zero partial inventory/assessment/fleet/audit writes, safe retry, concurrent identical commits, invalid/duplicate references, content/rule/key conflict guards, an actual backend process stop/restart using the same SQLite file, unknown health/profile fields, RAM/DDR/SATA/configuration rules and pending/synthetic physical exclusions. Chromium used an isolated SQLite database, checked that preview inventory was empty before commit, imported 12 computers/31 components, inspected authored evidence versus import metadata, checked compatibility/eligibility, rejected a delayed stale configuration response and verified a 390 px page had no document-level horizontal overflow. Browser page-error collection was empty. Desktop/mobile screenshots were inspected. No lint or full accessibility audit is claimed. Backend tests emit one upstream Starlette/httpx TestClient deprecation warning; the checks otherwise pass.

An independent read-only specialist review identified pending-physical evidence classification, rule-version pinning, stale configuration responses and missing visible eligibility reasons; these were corrected and covered by the final checks. This review is separate from the executed test evidence above. Local validation created synthetic SQLite test databases under ignored `data/`/temporary directories; no physical inventory was imported.

**Donor-demo risk recorded:** stock `RG-RAM-15` is cheaper than extracting donor `RG-RAM-07`, so RAM-07 is not guaranteed to be selected by the eventual optimizer. Onsite integration must choose a failure from the actual computed allocation and inspect a real alternative/no-spare outcome. Handwritten/Figma allocations remain preparation evidence; the application serves no computed plan and labels optimization “Not calculated.”

Production CP-SAT optimization, scenario replanning, revision-bound approval/reservations, work orders and verification integration remain planned onsite milestones. AI, interactive graph visualization, manual assessment editing, general fixture/evidence upload, public deployment/authentication and environmental factors are not implemented here. No completed repair, environmental saving, performance benchmark, deployment, Git commit or release is claimed. Exact Fetch hours remain unconfirmed.

The Windows backend/frontend startup helpers were also executed for handoff. FastAPI started on `127.0.0.1:8000` with reload watching only `backend/`; Vite started on `127.0.0.1:5173`. The frontend page and proxied state endpoint returned HTTP 200. The normal persisted database is initially empty at revision 0, ready for the reviewed import flow; the 12/31 browser demonstration used its isolated test database. Processes may need restarting after the local session ends.

## Record — 16 October 2026: local foundation checkpoint

OpenAI Codex, acting for the solo participant, inspected the existing project and initialized a local Git repository because none existed. `.gitignore` was reviewed and expanded to exclude dependency environments/caches, generated build/test outputs, local databases, logs, credentials and the `backups/` directory. `.gitattributes` was added to preserve exact file bytes, including registered fixture hashes, without changing the existing global line-ending setting. No application feature or executable source was changed.

`docs/CHECKPOINT_0_1_0.md` records the actual preparation date, implemented/unimplemented boundaries, Figma/prototype references, fixture/schema/inspection versions, previously executed validation, startup/recovery instructions, limitations, donor-selection risk and unresolved Fetch schedule overlap. README, the full planning package, source, lockfiles, tests, fixture/oracle and intended design/application previews form the source checkpoint. Earlier disclosure entries remain intact.

Git author identity was checked. No configured name/email pair or explicit author identity was available; Git reported `Author identity unknown` and `fatal: no email was given and auto-detection is disabled`. The intended commit `Checkpoint disclosed ReviveGraph foundation 0.1.0` and new annotated tag `pre-event-foundation-v0.1.0` are therefore **pending**, without inventing an identity or changing local/global identity settings. No existing tag is overwritten and no push/publication occurs. The exact staged file list must be inspected before any later commit.

The recovery archive is created from the reviewed Git index tree under ignored `backups/`. Checkpoint verification inspects its complete entry list, compares archived source bytes with the staged/working files, checks ZIP integrity, required source/documentation/fixture/lockfile coverage and forbidden generated/secret paths, and calculates SHA-256. The final path, index-tree identifier and archive digest are reported in an ignored external receipt and the task response, rather than embedding this checkpoint's own future commit hash in its contents. This is a source-only recovery package: **locked dependency installation is required; it is not an offline dependency bundle**. Native Figma content remains hosted separately; references and intended previews are included.

The previously passing application test suite, browser flow and preparation oracle are not rerun for this metadata/archive task. No new application behavior, physical repair, performance result or completed central workflow is claimed. Production optimization, scenario replanning, approval/reservations, work orders and verification integration remain unimplemented onsite work. The donor risk (`RG-RAM-15` may be cheaper than donor `RG-RAM-07`) and unconfirmed Fetch overlap remain unresolved.

The exact staged list was reviewed: 56 intended source/documentation/fixture/preview files. Ignore checks excluded the environment, node_modules, build/test outputs, database, backup, log and credential paths. Git's default whitespace check reported preserved CRLF formatting in `backend/requirements.lock.txt` and extra EOF blank lines; these cosmetic warnings were retained without changing executable source or the existing lockfile. Archive integrity and staged/working byte comparisons are separate from that formatting check.
