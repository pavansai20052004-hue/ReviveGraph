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

## Record — 17 October 2026: pending checkpoint completed

The participant explicitly supplied author identity GJV Pavan Sai / pavansai20052004@gmail.com. OpenAI Codex configured it for this repository only, rechecked the exact 56-file staged tree against the original receipt and created local commit `3ee5117eb3174c313e4be04adfb19350bd0136c9` (`Checkpoint disclosed ReviveGraph foundation 0.1.0`). New annotated tag `pre-event-foundation-v0.1.0` has object `ab885af2bd547e109c0f3291e9d4859875940dc4` and points to that commit. The tree was clean afterwards. The original ZIP, receipt and checksum were left byte-identical with their historical pending-identity status; no global settings, application code, push or publication changed in that completion task. Earlier records remain intact.

## Record — 20 October 2026: recovery application 0.2.0 preparation

The participant explicitly changed the earlier sequencing instruction and authorized advancing the central implementation before the event. OpenAI Codex implemented the following in the opened ReviveGraph project, with independent allocation/interface work and a read-only lifecycle review. **All of this is pre-event preparation**, not onsite work. The original 0.1.0 tag/commit, archive/receipt, native Figma design, six synthetic-v1 files and preparation oracle were preserved. CommitGuard was not accessed or modified. No paid service, deployment, publication, push or new tag/commit was requested or made.

| Files / area | Actual addition |
| --- | --- |
| `backend/revivegraph/optimizer.py` | Production OR-Tools complete-configuration allocation, global part uniqueness/donor/displacement accounting, lexicographic objectives and exact tie-breaking, pinned search/proof metadata, independent output validator and fixture-defined greedy baseline |
| `backend/requirements.in`, `requirements.lock.txt` | OR-Tools 9.15.6755 and exact installed transitive dependencies; upstream package licenses still apply |
| `backend/revivegraph/recovery_schema.py`, `db.py` | Transactional additive schema 1→2 migration; contexts, immutable plans, idempotency, failure events, decisions/reservations, work steps and append-only verification records |
| `backend/revivegraph/recovery.py`, `main.py` | Computed plan persistence/version hashes, selected-component failure overlays/replanning, stale/current checks, explicit approval/rejection, transactional target/part reservations, ordered simulation steps/evidence/locations, verification and provenance-bearing JSON reports; state summary and API version 0.2.0 |
| `backend/tests/test_optimizer.py`, `test_recovery.py`, `test_foundation.py` | 22 solver/validator and 13 lifecycle cases; original foundation no-plan test updated to expect empty computed-plan list rather than absent endpoint |
| `frontend/src/components/RecoveryWorkspace.tsx`, `InspectionGraph.tsx`, `CompatibilityView.tsx`, `App.tsx`, `types.ts`, `styles.css` | Connected six-screen shell, current counts/statuses, constrained planner, before/after selected donor failure, exact acknowledgement/approval/rejection, persisted dependent work/checklists, explicit authored simulated verification, JSON download, independent-context control and real-inspection React Flow graph with table alternative |
| `frontend/package.json`, `package-lock.json` | Local milestone version 0.2.0 and locked @xyflow/react; lazy-loaded graph avoids initial bundle warning |
| `frontend/e2e/recovery.spec.ts` | Full real browser workflow, stale approval guard, acknowledgement reset, graph interaction, verification/export, desktop and 390 px evidence |
| `scripts/rehearse_recovery.py` | Optional isolated acceptance rehearsal with automated test approval/check evidence, persistence reopening and full JSON receipt; never uses normal inventory or handwritten scenario allocations |
| `docs/RECOVERY_CONTRACT.md`, `IMPLEMENTATION_STATUS.md`, existing README/planning documents | Actual API/schema changes, all 18 capability statuses, actual allocations/totals, updated startup/demo instructions, revised meaningful onsite scope and unchanged unconfirmed Fetch overlap |
| `docs/implementation-previews/` | Updated running Inventory/Compatibility previews plus computed Optimizer, Simulation desktop/mobile and actual verification checklist; design previews remain unchanged |

The engine reads imported inventory and registered cost/profile/evidence contracts, never handwritten scenario allocations. The constrained main computation at 250,000 paise/330 minutes returned **7 final usable / 7 newly recovered candidates, 215,000 paise, 299 minutes, 7 transfers**, OPTIMAL with all four objectives and canonical tie-breaking proven over 657 generated configurations. Greedy reached the same totals (different storage assignment); no main-fleet improvement is claimed. The restricted tiny greedy trap proves 2 versus 1. Starting fixture classification remains 0 confirmed usable, 8 known unusable and 4 uncertain.

The real computed donor is **RG-SSD-10**, moved PC-09→PC-03. Its simulated failure replaces it with RG-SSD-11 from PC-11, retaining 7/215000/299/7 and a proven optimum. RAM-15 is selected instead of handwritten donor RAM-07, confirming the old donor-selection concern. Failure selection now follows actual output. Main operations are 7 preparations, 3 RAM removals, 4 storage removals, 3 RAM installs, 4 storage installs and 7 verifications; these sum independently to 215000 paise/299 minutes. They are estimated operations in a synthetic model, not observed repair times or completed hardware.

Approval identifies an explicit local human/demo actor and exact current validated plan ID/hash; actor labels are not authenticated technician identities. Parts and target reservations are atomic and unique within one independent simulation context. Only one approved plan per context conservatively prevents conflicting donor/displacement work. Work progress changes simulation locations only. A pre-work failure preserves original plan results and produces linked recalculation. A failure after work starts records the overlay, pauses unfinished work and preserves completed simulated locations/evidence; automatic reconciliation/resume is unimplemented and explicitly blocked. Physical planning/execution remains unavailable pending real profiles, reviewed evidence and appropriate identity controls.

Per-step evidence/checklists and pass/fail/inconclusive outcomes are authored simulation records. The optional acceptance harness uses actor `automated-rehearsal` and explicitly synthetic evidence to exercise API behavior; its approval is test input, not a real technician's decision. The browser similarly automates a local demo approval. Neither creates physical evidence, changes physical locations nor increases physically verified repair counts. Environmental estimates remain absent.

The Figma design-to-code skill read actual context/screenshots for Optimizer `4:246`, Simulation `5:391` and Compatibility `5:281`. The native file was not edited. No static screenshot was used as an application UI asset. Existing editable design layers/tokens/variants/prototype and original design PNGs remain preserved; their example counts/prices/allocations still differ from actual computation and are not measured results. Actual desktop/mobile renders were inspected; captures were tightened to show compact orders and a dedicated checklist rather than a long expanded list. Mobile capture waits for the existing drawer transition to finish; this avoids recording a transient overlay as clipped text.

Validation actually executed on 20 October 2026 from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_optimizer.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\test_recovery.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\validate_synthetic_fixture.py
.\.venv\Scripts\python.exe scripts\rehearse_recovery.py --output data\recovery-rehearsal-20261020.json
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
npm --prefix frontend run test:e2e -- recovery.spec.ts
```

Results: **65 backend tests passed** (30 foundation, 22 optimizer, 13 lifecycle), pip reported no broken requirements, original oracle passed all 11 restricted cases and both frozen handwritten arithmetic examples. The preparation oracle's old “no production optimizer” message describes that unchanged preparation script's proof scope; it is not the current application status. Full Chromium suite after graph integration passed **2 tests**; targeted recovery reruns after interface/capture refinements passed. Typecheck and production build passed. npm dependency installation reported zero vulnerabilities in its 96-package audit. There is one pre-existing upstream Starlette/httpx TestClient deprecation warning; no new application test failure remains. A first foundation regression still expected `/plans` to be absent and was changed to assert an empty computed-plan list. An initial solver proof timeout was resolved by pruning strictly dominated incoming RAM supersets without dropping retained modules. Initial graph bundle warning was resolved by lazy loading. A rehearsal-script escape warning was fixed with a raw docstring.

Lifecycle checks include atomic/idempotent imports, invalid references, shared-part contention, donor accounting, exact/zero resources, unknown/faulty/physical exclusions, invalid output, FEASIBLE/UNKNOWN/cancellation metadata, concurrent same/different approvals, transaction rollback, stale revisions, tampering, interrupted failure/retry, inventory/approval changes during solve, no-spare failure, order-before-approval rejection, dependency/checklist enforcement, reopening persistence, unresolved verification outcomes and failure after a recorded removal. Browser covers actual import→compute→failure→stale original→revised approval→prerequisite steps→authored simulated pass→parsed report export, real graph selection/controls, acknowledgement reset, zero page errors and desktop/390 px layout checks.

The isolated acceptance rehearsal produced two computed plans, seven work orders and **seven authored simulation passes / zero physical passes** after reopening its temporary database, with unchanged physical inventory counts. Its actual receipt/report is under ignored `data/recovery-rehearsal-20261020.json`, not an input dataset. Browser evidence separately recorded an authored simulated pass. Normal `data/revivegraph.sqlite3` was not reset, imported into or migrated by tests. Checkpoint/archive/source integrity checks are separate from behavioral tests.

Remaining material gaps: AI provider/model and bounded agent orchestration, manual accepted-health/physical review, manufacturer-backed profiles/real hardware, physical execution, automatic post-start reconciliation, general fixture/evidence uploads, authenticated access, formal accessibility/security review, environmental factors and richer report/chart formats. Current 18-capability status is recorded in IMPLEMENTATION_STATUS; none of these gaps is labeled complete. Proposed onsite work now focuses on real evidence/manual review, reconciliation and optional safe AI integration, followed by validation and disclosure. Exact Fetch hours and overlap duration remain unconfirmed.

## Record — 20 October 2026: screenshot-led operations dashboard redesign

The participant supplied `ChatGPT Image Oct 20, 2026, 09_50_41 PM.png` as the primary visual reference and explicitly requested direct implementation in the existing frontend. OpenAI Codex inspected that image before editing, reused the existing React/Tailwind/Radix components and preserved the working recovery flow. The native Figma design was left unchanged; the new screenshot direction supersedes it as the primary reference for this visual pass. No application restart/rebuild from scratch, fixture edit, preparation-oracle edit, tag overwrite, archive change, push or publication was made.

The shared design now uses a near-black/navy canvas and sidebar, left-aligned icon navigation with blue selection, a compact title/search/operator header, subtle 1px card/table borders, 6px panel corners, smaller consistent spacing and restrained emerald/cyan/amber/red/purple state accents. ReviveGraph branding and the explicit synthetic/simulation boundary are retained. The header search actually filters imported inventory; sidebar collapse/mobile navigation, information controls, source navigation and existing import/approval/work controls function. The operator is labeled as a local demo identity rather than copying the reference's person/avatar.

Dashboard adapts the reference's five metrics, central health/alert cards, right insights/activity rail, comparison chart and workflow diagram to actual backend inputs. The fleet visualization contains actual imported computer IDs and usability states, not industrial imagery or invented health scores. Alerts show representative real missing/faulty/unknown records and explain nonexclusive categories. The Recharts comparison uses stored solver/greedy/parent-plan totals; there is no generated time history, prediction interval, industrial metric or environmental saving. The workflow uses persisted approval/removal/install/verification progress. AI is explicitly unconfigured rather than presented as a working insights service.

A read-only, fleet-scoped `GET /api/v1/audit-events` supplies actual action/actor/time/entity/data, exact action filtering and bounded pagination. Parameterized queries scope events through related batches/assets/components/plans/orders/failures/verifications; shared registrations are excluded. It performs no inventory or lifecycle mutations. The new Reports workspace displays real input/version pins, assumptions, operation ledger, decisions, simulated outcomes, event history and the existing provenance-bearing JSON download.

| Files / area | Actual work |
| --- | --- |
| `frontend/src/App.tsx`, `styles.css`, `components/ui/Icon.tsx` | Reference-led shared shell/tokens, functional inventory search, compact navigation/header, responsive 390 px layout, Reports route, consistent restyling of Inventory/Compatibility/Optimizer/Simulation and diagnostic evidence view |
| `frontend/src/components/{Dashboard,DashboardCharts}.tsx`, `dashboard.css` | Actual fleet schematic, five backend metrics, categorized alerts, lazy-loaded discrete Recharts comparisons with exact data table, workflow status, actual insights and audit feed |
| `frontend/src/components/ReportsView.tsx`, `reports.css` | Live report selection, pins/assumptions, approval/verification records, resource ledger, JSON export and real audit filtering/pagination; loading/empty/error/current/stale information |
| `backend/revivegraph/recovery.py`, `backend/tests/test_audit_read.py` | Additive read-only audit endpoint and six isolated tests for scope isolation, decoded data, ordering, filters, bounds, injection-like input and unchanged database contents after reads |
| `frontend/package.json`, `package-lock.json` | Locked Recharts 3.10.1 and lucide-react 1.60.0 dependencies, subject to upstream licenses; installation audited 128 packages and reported zero vulnerabilities |
| `frontend/vite.config.ts`, `playwright.reference.config.ts` | Optional development API-target override and separate test servers on 18100/15173, keeping the user's normal app on 8000/5173 available; fresh ignored test databases |
| `frontend/e2e/reference.spec.ts`, `recovery.spec.ts` | Dashboard data/audit/graph/search/report-export checks, actual desktop/390 px screen captures, containment and navigation; existing recovery geometry check updated for the heading's new header location |
| `docs/implementation-previews/reference-*.png`, README, UI_PLAN, RECOVERY_CONTRACT, PRE_EVENT_WORK | Actual rendered evidence and current design/API documentation |

The initial rendered comparison found excess card stretching, tiny workflow labels, a chart captured during entrance animation and an old test selector for the former heading location. These were corrected: independent compact card sizing, readable workflow labels, static chart bars matching actual values immediately, representative alert categories, compact real activity rows, inline sidebar collapse, content-sized Reports panels and the correct header selector. No failing behavior was hidden by disabling its assertion. Empty inventory still shows Not calculated; failed fetches show retry states; stale/paused plans and synthetic verification remain explicit.

Validation executed from the project root on 20 October 2026:

```powershell
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend ls --depth=0
.\.venv\Scripts\python.exe -m pytest backend\tests\test_audit_read.py backend\tests\test_recovery.py -q
```

From `frontend/`:

```powershell
npx playwright test --config playwright.reference.config.ts
```

Results: typecheck and production build passed; installed dependency tree is consistent; **19 backend tests passed** (six new read-only audit tests and thirteen existing lifecycle cases), with the pre-existing Starlette/httpx deprecation warning. The complete isolated Chromium suite passed **3 tests in 35.8 seconds**: original import/evidence/compatibility regression, computed plan→donor failure→stale approval→revised approval→dependent work→authored simulated verification→report export, and new reference-dashboard/search/Reports/actual-audit checks across desktop and six 390 px workspaces. Browser page-error collection was empty and document overflow checks passed. The first run's obsolete `.page-heading h1` selector failed after the heading moved to the shared header; it was updated to `.header-title h1` and the full suite passed. Test-runner NO_COLOR/FORCE_COLOR warnings are environmental, not application failures.

Actual rendered screenshots were compared with the supplied reference and corrected. Desktop evidence at 1672×941 and mobile at 390 px is stored as `reference-dashboard-desktop.png`, `reference-dashboard-mobile.png`, `reference-inventory-desktop.png`, `reference-compatibility-desktop.png`, `reference-optimizer-desktop.png`, `reference-simulation-desktop.png`, `reference-reports-desktop.png` and corresponding mobile views. The displayed 12/31, seven planned candidates, ₹2,150/299-minute estimate and one authored simulation pass came from the isolated browser database and actual solver/workflow actions; they are not hard-coded default content or physical repairs. The normal application inventory was not seeded/reset for these screenshots.

The original foundation annotated tag and ZIP/receipt hashes were rechecked and preserved. No real hardware evidence, completed physical repair, live AI, environmental estimate or performance benchmark was created. Formal accessibility/security audits remain outside these checks. This redesign and read-only Reports/audit work are pre-event preparation; future onsite work must still be recorded separately, and Fetch hours remain unconfirmed.


## Record - 21 October 2026: workflow-first effectiveness refinement

The participant requested a more effective application and selected "Both, with workflow first" when asked to prioritize workflow and visual refinement. OpenAI Codex continued the existing screenshot-led frontend rather than rebuilding it. The supplied screenshot was inspected again; desktop and 390 px rendered previews were compared and the mobile work-priority issue was corrected. All work described here is pre-event preparation.

Actual changes:

- Dashboard adds one state-aware next action and a compact Import / Inspect / Plan / Approve / Verify journey. Its recommendations distinguish empty/imported inventory, uncalculated/current/revised/stale/rejected/paused plans, approval, active work and completed simulated verification. Opening a plan from the dashboard explicitly selects that current revision rather than silently restoring an older session selection. Available synthetic evidence is not marked reviewed/verified. Unfinished work remains the primary action even when an earlier work order has a simulated pass.
- ImportDialog adds Prepare demo preview, which registers the existing immutable synthetic fixture if needed, loads both real bundled CSV files and requests a real preview. The explicit Commit batch action remains separate. Manual registration, file selection, field errors and preview controls remain available. The browser check confirms zero computers and components after this shortcut's preview.
- RecoveryWorkspace adds resource headroom, actual changed-only allocation comparison, highlighted removed/added IDs, unchanged counts, real cash/time/count deltas and a toggle for all allocations. Zero changes are shown as zero rather than an invented improvement.
- The Simulation result column now leads with work orders. A prerequisite-ready queue names the target/operation/component and opens/focuses the next available task. Filters, asset search, progress and named dependency links support manual execution. It never checks items or authors evidence on the operator's behalf. Saved checklists, evidence references and supplied actor/time fields are restored read-only after reload, including recorded verification timestamps where supplied.
- Additional donor failure controls become a secondary disclosure after work orders exist, retaining the warning that post-start failure pauses execution. On narrow layouts the active result/work queue precedes secondary scenario controls. Stale-plan/paused execution and exact-revision approval protections remain in place.
- New browser regression `frontend/e2e/workflow.spec.ts` covers current-plan navigation despite a saved stale selection, changed-only/full comparison, explicit approval/order creation, work search/ready-task focus, explicit evidence submission and its persistence after reload. It also records actual desktop/390 px previews. Existing import/recovery tests were updated to exercise the real shortcut and target the completion button specifically now that dependency names are clickable.

Relevant source: `frontend/src/components/Dashboard.tsx`, `dashboard.css`, `ImportDialog.tsx`, `RecoveryWorkspace.tsx`, `recovery-flow.css`, shared styles/types, and the import/recovery/workflow browser tests. README, UI_PLAN and BUILD_PLAN describe the current workflow. No backend executable code, fixture, preparation oracle or native Figma design was changed in this refinement.

Validation actually executed on 21 October 2026:

```powershell
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Both passed, including a fresh run after the final mobile refinement. From `frontend/`:

```powershell
npx playwright test --config playwright.reference.config.ts
npx playwright test e2e/recovery.spec.ts e2e/reference.spec.ts e2e/workflow.spec.ts --config playwright.reference.config.ts
npx playwright test e2e/import.spec.ts --config playwright.reference.config.ts
```

The full four-test suite passed in 48.5 seconds. After moving active work ahead of secondary mobile controls, the three affected recovery/reference/workflow flows passed again in 46.7 seconds. After strengthening the fresh-registration shortcut assertions, the focused import flow passed in 10.4 seconds (test body 4.7 seconds). The first full run exposed an overly broad old test selector: a step now contains both a named dependency button and its Record button. The assertion was narrowed to the actual Record action and the complete flow passed; the completion assertion was not removed. Browser page-error arrays were empty, real compatibility/evidence and stale-approval protections were exercised, and the desktop/390 px overflow/containment checks passed. The test environment's NO_COLOR/FORCE_COLOR warning remains nonfunctional. Backend tests were not rerun for this frontend-only refinement; the earlier executed results above remain historical.

Actual inspected previews are `docs/implementation-previews/effective-dashboard-desktop.png`, `effective-dashboard-mobile.png`, `effective-simulation-desktop.png`, `effective-simulation-mobile.png` and `effective-allocation-changes.png`. These show isolated test contexts against the real backend and synthetic fixture, with explicit authored test simulation records. They do not describe the user's normal inventory: a read of the normal app returned revision 0, 0 computers/components/plans/orders and Not calculated. Normal servers were started on localhost 8000/5173; no automatic fleet import, approval or verification was performed there.

Preservation checks confirmed no fixture/oracle diff, foundation commit `3ee5117eb3174c313e4be04adfb19350bd0136c9`, annotated tag object `ab885af2bd547e109c0f3291e9d4859875940dc4`, original ZIP SHA-256 `C9542CED0EA54AB52E15B189BA9922E525CFA5360B79D0720776C1068683AE25` and original receipt SHA-256 `72F5DBAD51D8E678AA6EF09F5B41843DB2A44059872854E836D487931E7616B1`. No commit, tag update, push, publication, deployment or global Git setting change was made.

Physical hardware review/execution, live AI, automatic reconciliation after work starts, production authentication and formal accessibility/security audits remain unimplemented or unverified as already documented. Synthetic evidence remains simulation-only; no real repair or environmental saving is claimed. The donor failure is still chosen from actual computed allocations, because the handwritten RAM-07 example is not guaranteed to be selected. Exact Fetch overlap hours remain unconfirmed.


## Record - 21 October 2026: travel feature freeze and recovery preparation

The participant explicitly froze feature development and requested travel preparation only. No application feature, production code, dependency version, schema, fixture, preparation oracle, native Figma design, optimizer behavior or new executable test was changed in this travel pass. All earlier records are retained. The checkpoint covers the existing recovery 0.2.0 implementation, screenshot-led UI/workflow, locks, tests, specifications, original fixture and intended previews. All are disclosed pre-event preparation, not onsite work.

Post-start recovery/reconciliation from current simulated locations, reservation/dependency reconciliation, renewed approval, safe resume and their new tests are reserved for onsite implementation. Existing safe pause and its earlier tests are already pre-event work. Physical assessment/execution, live AI, production authentication and environmental estimates retain their documented gaps. Exact Fetch timing/overlap remains unconfirmed.

Data preservation and manual rehearsal: the normal app remains on 8000/5173. A read-only SQLite backup of its starting state was saved as `backups/travel-readiness-20261021T051413834938Z/normal-database-snapshot.sqlite3` (SHA-256 `6d5c9555509b878e79d43a24c45a35c85bbef9a22bef5dd043b7c9569d7d341b`). Its starting source-file SHA-256 was `4f339baadc11070432dde77be1a441dd6953a08ea45d374e30da42af0ec14427`. The isolated rehearsal uses `manual-synthetic-rehearsal.sqlite3` in that travel directory and ports 18080/15174.

The participant confirmed a valid 12-computer/31-component preview and explicitly said it was not committed. A later preservation check found that the first registration/preview had reached the normal instance, while its inventory/plans/orders remained empty. It is therefore inaccurate to claim the normal file remained byte-identical. Both the original snapshot and a second `normal-after-preview-preserved.sqlite3` snapshot are retained; both passed SQLite integrity_check. No source database was reset and no existing work was deleted. The participant was asked to pause before committing, open the exact :15174 address and prepare the preview there. Read-only registration timestamps confirmed :15174 proxies to the separate 18080 instance, which subsequently contained its own registration/preview. Manual rehearsal remains **in progress, not passed**; remaining import/evidence/plan/approval/execution/verification steps require participant action and observation. No manual approval, diagnostic measurement or verification outcome is invented. Full instructions and the address warning are in TRAVEL_READINESS.md; progress receipts stay outside source control.

Offline startup actually checked with installed dependencies:

- Backend startup on 18080 and `npm --offline --prefix frontend run dev -- --port 15174 --strictPort` succeeded with preparation-only external socket/DNS connection guards, allowing localhost. Both deliberate external-connection rejection self-checks passed. An initial Node preload failed because of backslash path parsing; using forward slashes fixed the preparation command. This was a harness quoting issue, not a missing application dependency or app-code change.
- A targeted installed-Chromium startup smoke opened Dashboard, the import dialog, Inventory, Compatibility, Optimizer, Simulation and Reports, aborting non-local browser requests. Result: 0 external page requests, 0 failed requests, 0 page errors. It performed no import/solve/approval/work/verification. This was startup validation, not a full-suite rerun or manual rehearsal.
- `.venv\Scripts\python.exe -m pip check`: no broken requirements. All 33 exact backend lockfile versions matched installed metadata; OR-Tools CP-SAT import passed. `npm --offline --prefix frontend ls --depth=0`: all direct frontend dependencies present, no missing/invalid packages reported. No dependency installation/download was performed. Actual runtimes: Python 3.14.7, Node 24.19.0, npm 11.17.0. Fonts/assets were local; AI is unconfigured.

The connection guards are instrumentation, not an OS firewall or proof of every possible native networking path. Laptop Wi-Fi/firewall settings were not changed. Whole-device airplane-mode operation, a fresh-machine install, complete offline dependency-cache availability and separate production-preview startup were not tested. Fresh installation, Figma and external event links may need internet. Preserve the installed runtimes, .venv and frontend/node_modules on the travel laptop. Earlier backend/browser/build successes remain historical; no already-passing suite or build was rerun merely for this checkpoint.

The exact staged list was reviewed: existing implementation, dependency locks, tests, specs, synthetic CSV/JSON and intended PNG previews. The source-path/private-key/token signature check found no generated environments, node_modules, database, credential file or matching secret signature among candidate source files. The travel pass changes only README, BUILD_PLAN, PRE_EVENT_WORK and the new TRAVEL_READINESS runbook; ignored guard/smoke utilities and local receipts are preparation aids, not new application features.

A new local checkpoint uses repository-local author GJV Pavan Sai / pavansai20052004@gmail.com, commit message `Freeze disclosed ReviveGraph implementation for travel` and a new annotated `pre-event-travel-freeze-2026-10-21` tag if absent. Final hashes are recorded outside this committed document. The separately named source archive is `backups/travel-readiness-20261021T051413834938Z/ReviveGraph-travel-freeze-20261021-source.zip`; its sibling receipt/checksum identifies the exact committed source tree, inventory and content verification. It includes source, all six fixture files, locks, docs/tests/previews and startup instructions, excluding Git metadata, databases, credentials, environments, dependencies and generated outputs. **The ZIP requires dependency installation and is not an offline dependency bundle.** Normal-data snapshots are separate, not inside the source ZIP.

Original foundation commit/tag, ZIP, .sha256 and receipt were checked for preservation; none is overwritten. Archive/checkpoint final creation and verification are recorded in the external receipt and reported after creation, avoiding self-reference. No push, publication, deployment, global Git configuration change or automatic manual-rehearsal actions were performed.

Manual progress update before checkpoint: the participant confirmed :15174, explicitly imported 12 computers/31 components and inspected RG-PC-04 as unknown with no technician review. Read-only isolated state corroborated revision 1, 0 usable / 8 unusable / 4 uncertain; normal inventory remains revision 0 and empty. Compatibility/calculation is the next pending manual stage. No manual solver/approval/verification result is yet claimed.


## Record - 22 October 2026: final automated browser rehearsal and source backup

The participant authorized completing a fresh automated pre-travel rehearsal while keeping feature development paused until the 24 October event. Existing README, supplied project instructions, implementation, Git status and earlier disclosure were inspected first. The working tree started clean at `7f4721034f8f5f3d40456bb1dc029a12e17ff155`. No application feature, production code, dependency version, fixture, preparation oracle, schema or Figma artifact changed. No blocking application defect was found; changes in source control are documentation only. Post-start recovery/reconciliation, renewed approval and their new tests remain reserved for onsite development.

Normal and participant-manual databases were snapshotted read-only before work and retained separately. The previous manual rehearsal was inspected directly: 12 computers, 31 components, 2 plans, 7 work orders, **3 completed steps and 0 verification records**. Earlier conversation reports of two confirmed steps were historical; the current three-step state is preserved. No agent finished the participant's manual work, approved that manual plan again or changed its evidence. Normal inventory remained empty with its existing preview metadata preserved. Exact SHA-256 comparison at the end confirmed both databases, every original tracked application/fixture/design file, and all **26 prior backup files** unchanged.

A new isolated database under `backups/final-pretravel-20261022T072337024021Z/automated-synthetic.sqlite3` and ports 18220/15220 were used. The preparation-only Playwright driver exercised the existing UI, using read-only API responses to corroborate each stage. All mutating lifecycle requests originated from browser controls. The driver's own intercepted request headers explicitly recorded actor **automated-pretravel-browser-20261022** and evidence prefix **synthetic:automated-pretravel-browser-20261022:**. These are automated test approval and authored simulation records, not entries personally made by the participant or authenticated technician hardware evidence.

Actual automated stage results: **all 12 PASS**: (1) valid 12/31 preview with zero inventory before commit; (2) explicit browser commit; (3) imported unknown evidence, DDR3/DDR4 mismatch and synthetic evidence physical exclusion; (4) resource-constrained calculation; (5) actual allocations/operation totals/greedy comparison; (6) actually allocated donor failure before any work; (7) before/after comparison with original stale approval disabled; (8) explicit automated simulation acknowledgement/approval; (9) work orders and ready-task navigation; (10) all prerequisite-ordered authored checklists; (11) simulated verification and parsed downloaded audit; (12) actual backend/frontend restart and identical persisted data/UI evidence restored in a new browser context.

Computed original plan `plan_4414008ecc514b67ab1a64ff9d9e71c9` and revised `plan_baee240b22884f6cbfadb7f65db37ce4` both reported **OPTIMAL**. At 250000 paise / 330 minutes, each returned **7 usable-final / 7 newly recovered candidates, 215000 paise, 299 minutes, 7 transfers**. The actual original same-input greedy baseline returned the same aggregate totals with some different allocations; no main-fleet uplift is claimed. The driver did not assert seven as the required optimizer output or inject handwritten allocations. It summed the returned ledger and checked it matched returned cash/minutes and allocation count. The actual donor was **RG-SSD-10 (RG-PC-09 -> RG-PC-03)**. Revised RG-PC-03 used **RG-SSD-11 from RG-PC-11**; all other final assignments were unchanged. Complete allocations and operation arithmetic are in FINAL_REHEARSAL_2026_10_22.md and the receipt.

The UI recorded 21 non-verification operations in prerequisite order, followed by seven authored simulated verification passes, completing **28/28 steps**. Physical repair totals stayed **0**, and imported inventory/physical component location/evidence JSON was identical before and after execution. The before/after audit JSON downloads retained actual plan, version/assumption pins, decisions and simulation evidence. No real diagnostic measurements, physical repairs, environmental savings or performance benchmark was created.

Both guarded service processes were stopped, then restarted against the same database: backend/frontend PIDs **26036/34700 -> 21032/22912**. The fresh browser context restored the revised plan; deep comparisons of the entire plan, decisions, orders, checklist/evidence/actor/time fields and state passed. Saved checkboxes/evidence were visible and read-only. Reports downloaded a second audit with the same persisted plan. SQLite integrity_check passed. Test-owned processes were stopped after the completed checks; unrelated processes were not stopped.

Offline scope: Python/Node socket/DNS guards allowed loopback and rejected deliberate external-connection self-checks. Chromium used a process-only external proxy to a closed loopback port, resolver exclusions for localhost/127.0.0.1, non-local page/WebSocket rejection and blocked service workers. Both complete browser phases deliberately attempted offline-check.invalid and confirmed rejection; each recorded **0 unexpected external requests, 0 failed application requests and 0 page errors**. Deterministic calculation, failure replanning and verification ran with existing installed dependencies and no downloads. No whole-device Wi-Fi/firewall change was made. This is not an OS network namespace or a guarantee against all native/subprocess networking paths; whole-device airplane mode and fresh-machine offline dependency installation remain unverified. Figma/external pages and fresh dependency downloads can require internet. No missing runtime dependency was observed in this flow.

Two preparation launcher/isolation errors were fixed before the passing run: Vite initially launched with the repository root instead of frontend, producing a 404; a wildcard Chromium resolver rule initially blocked 127.0.0.1 itself, corrected by an explicit loopback exclusion. Both were ignored preparation-driver corrections; no application defect was suppressed and no app source was edited. Failed-attempt logs are preserved separately. Only the requested targeted rehearsal and necessary startup/restart/integrity/hash checks ran; prior backend suites, general frontend suites, production build and the preparation oracle were not rerun.

Evidence is retained under `backups/final-pretravel-20261022T072337024021Z/`: stage receipt automated-rehearsal.json, verified-summary.json, process-restart.json, both downloaded automated-audit JSON files, actual screenshots, scoped guard/driver scripts, logs and separate database snapshots. These are generated local runtime evidence and are excluded from the source archive. README/TRAVEL_READINESS link to the new dated report with a short manual click script and isolated startup/restart commands. All previous disclosure text is retained.

The new local documentation checkpoint uses the existing repository-local author identity, a new annotated `pre-event-final-rehearsal-2026-10-22` tag only if absent, and a separately named `ReviveGraph-final-pretravel-20261022-source.zip` in the new evidence directory. Final commit/tag/ZIP hashes and per-file committed-content verification are recorded externally to avoid self-reference. The source ZIP contains the reviewed source, lockfiles, fixture, tests, docs and intended previews; credentials, databases, environments, node_modules, generated runtime files and .git are excluded. **It requires dependency installation and is not an offline installation bundle.** Earlier tags, archives and receipts are preserved without overwrite. No push, publication, deployment or global Git configuration change was performed.

Travel readiness: the complete automated simulation/restart passed, while the participant's personal manual rehearsal remains incomplete and unchanged. Whole-device airplane-mode behavior, fresh-machine setup, physical evidence/repairs and current event/Fetch schedule confirmation remain outside this evidence; exact Fetch hours remain unconfirmed. No post-start recovery, reconciliation, resumed execution or renewed approval was added or tested before the event.
