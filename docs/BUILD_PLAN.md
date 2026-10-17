# Build and validation plan

Status: proposed onsite schedule plus disclosed application foundation, updated 16 October 2026. Solo participant; optimize for one reliable end-to-end demonstration. Native Figma design, unchanged synthetic fixture v1 and registration/import/inventory/compatibility code exist. Foundation checks passed as recorded below; the central optimization-to-verification flow remains onsite work.

## Preparation milestones

| Milestone | Deliverable and exit condition | Dependency / status |
| --- | --- | --- |
| P0 — Planning | Six consistent documents with hardware scope, safety invariants, six UI briefs and disclosure | Documents created 16 Oct; updated as preparation advances |
| P1 — Figma design | Native foundations, six desktop screens, clickable import → failure → approval → simulated verification flow, plus 390 px Inventory/Simulation layouts; formal application accessibility checks remain later | P0; design/prototype created 16 Oct, see `UI_PLAN.md` |
| P2 — Synthetic fixture design | Two CSVs with 12 institution-owned computers and 31 finite uniquely identified parts; four JSON sidecars, explicit synthetic provenance/costs/time, feasible example plans and restricted tiny-case oracle; no completed repairs | P0; created and preparation-validated 16 Oct, see `FIXTURE_SPEC.md` |
| P3 — Disclosed foundation | React/FastAPI/SQLite scaffold, immutable fixture registration, real preview/atomic import, shared UI, inventory/evidence inspection and deterministic compatibility; record exact behavior | Implemented and locally validated 16 Oct; manual assessment editing/physical review remains later work |
| P4 — Freeze preparation | Dated source checkpoint, dependency locks, Figma/fixture references and verified source recovery archive; list implemented vs unimplemented behavior | Checkpoint prepared 16 Oct; local commit/annotated tag pending unavailable author identity; see `CHECKPOINT_0_1_0.md` and external archive receipt |

Remaining preparation is a proposal, not permission to claim it has happened. Update [PRE_EVENT_WORK.md](../PRE_EVENT_WORK.md) as each artifact is created. If preparation runs short, keep the same onsite core and reduce visual/AI enhancements. Do not silently complete the central onsite scope beforehand.

## Onsite milestones — relative to announced 24-hour start

| Window | Substantial work / completion gate |
| --- | --- |
| Hours 0–2 | Record starting snapshot and actual official window; revalidate the disclosed synthetic fixture against implemented import/compatibility behavior and reconcile hand-checked expectations. |
| Hours 2–7 | Complete and integrate CP-SAT configurations, operation costs/time and constraints; implement independent output validator and baseline; exercise tiny oracle cases. |
| Hours 7–11 | Implement scenario snapshots, donor failure and deterministic replanning; retain original plan and compare revisions; protect against stale results. |
| Hours 11–15 | Implement human approval, transactional reservations, idempotent work orders and simulated verification; prove approval cannot be bypassed. |
| Hours 15–19 | Integrate six screens with real backend responses and complete the full 12-machine flow; repair edge cases and restart behavior. |
| Hours 19–22 | Execute core validation matrix, responsive/browser review and offline rehearsal; fix failures before adding enhancements. |
| Hours 22–24 | Buffer, demo rehearsal, report export and honest evidence/disclosure; optional AI only if the core is already stable. |

Dependency chain: normalized inventory/evidence → compatibility/configurations → optimizer + validator → scenario replanning → revision-bound approval/reservations → orders → verification → truthful analytics/report. AI and richer impact estimates are independent enhancements and must not block this chain. Onsite completion is not guaranteed by this schedule.

## Baseline and comparison protocol

Build a simple deterministic greedy baseline: visit recoverable-base targets in stable asset-ID order; choose the least-cost currently feasible complete configuration (then minutes, transfers and configuration ID), mark its parts used, and continue within remaining budget/time. Recompute operation totals against the complete chosen set; reject any increment that violates shared-removal or resource rules. Use exactly the same compatibility engine, eligibility, cost/time model, constraints and validator as CP-SAT.

Compare final recovered candidates first, then cash/time and transfers; record solver status and runtime only after execution on stated hardware/settings. No promised uplift or speed target. A time-limited solver may be worse than greedy; show it honestly. For proven optimal solutions the primary recovery count should be at least the valid baseline count. Use exhaustive enumeration on tiny fixtures as an independent optimality oracle, rather than assuming the baseline is optimal.

## Planned meaningful validation

| Case | Evidence required before declaring pass |
| --- | --- |
| CSV transaction and retry | Invalid references/duplicate part IDs/negative or malformed fields yield row errors and zero writes; identical commit retry yields no duplicates. |
| Eligibility and hardware | Known DDR3/DDR4 mismatch rejected; missing board fields unknown; faulty/unknown parts excluded; unsupported storage rejected; invalid multi-module combinations rejected. |
| Provenance / ownership | Synthetic assessments excluded from physical plans; unauthorized owner transfer rejected; scenario writes cannot alter physical locations/results. |
| Shared donor | Two targets compete for one part; validator proves at most one assignment, including retained parts; donor losing required memory is not also counted without replacement. |
| Resources | Exact-budget/time case succeeds; one unit over excluded; zero limits honored; extraction, faulty-part removal and verification charged once. |
| Known optimum | Tiny enumerated fixtures match CP-SAT's proven optimum and canonical tie-break; greedy trap has a demonstrable better fleet allocation where constructed. |
| Solver outcomes | Distinguish zero-recovery feasible result from infeasible, invalid, unknown and feasible-only termination; never approve an unvalidated output. |
| Reproducibility | Repeat same snapshot/version/settings and compare canonical allocations/objectives; altered input hash forces a new plan. |
| Failure replan | Failed donor ID absent from revised allocations; old plan retained; revised totals validated; stale approval rejected. Include no-spare scenario. |
| Approval and conflicts | Order creation without approval fails; concurrent/stale requests cannot double reserve; repeated approval/order requests produce one logical result. |
| Restart / partial work | Interrupted solver is retryable; completed steps survive restart; failure after work starts pauses affected work and does not roll back physical facts. |
| Verification / audit | Missing checks cannot pass; pass/fail/inconclusive persisted with mode/evidence; synthetic passes never increase physical totals; exports include revision chain and assumptions. |
| AI boundaries (P1) | Prompt-injection logs, invented IDs, unsupported health claims and provider outages cannot write accepted facts or bypass approval. |
| Interface / end-to-end | Six-screen browser flow at desktop and 390 px, keyboard/focus checks, loading/error/stale states; imported fixture count is exactly 12. |

Implement domain unit tests first, then database/API tests for transaction boundaries and one browser acceptance flow. Run typecheck, relevant lint, backend tests and production frontend build after integration. Record actual commands/results when they exist; this table is a future checklist, not evidence of passing tests.

## Demo sequence

1. Disclose solo work, preparation and the synthetic dataset; show no physical repairs claimed.
2. Import 12 synthetic desktop records and their parts; show the eight known faulty/missing blockers and four uncertain assessments/profile fields without presenting uncertainty as proven physical damage.
3. Set declared budget/time; run baseline and optimizer; inspect final assignments, totals and solver status.
4. Open simulation, select a donor component and inject failure; show preserved original plan and changed recovery plan.
5. Have the human reviewer approve the exact revised simulation plan; create traceable simulation work orders.
6. Advance the removal/install checklist, record simulated verification with synthetic evidence, then show separated impact counts and export the audit report.

Aim for a 5–7 minute rehearsal, not a claimed measured duration. Keep local offline operation for P0; if AI is unavailable, explain deterministic results without presenting canned text as a live model response. If recalculation fails, show the error and any clearly labeled earlier run; do not silently substitute a successful plan.

## Remaining decisions and risks

Synthetic supported profiles, CSV rows and cost/time assumptions are pinned in `datasets/synthetic-v1/`. Registration now stores sidecar/source hashes and the inspection engine version; imports store individual assessment assertions with authored-date precision separate from import time. General fixture/evidence uploads and physical human-review workflow still need explicit contracts. The main handwritten allocations are feasible examples, not known optima; the tiny-case enumeration proves only its restricted cases. The Figma counts, prices and allocations still differ and remain illustrative until an implemented solver supplies validated results. AI provider/model, real-hardware evidence policy, environmental factors and deployment/auth remain undecided. Scope creep, operation-cost errors, stale approval and inflated impact claims are the principal risks. Preserve meaningful onsite optimization, failure replanning and approval implementation; all pre-event code remains disclosed.

**Donor selection risk:** `RG-RAM-07` is not guaranteed to appear in a future computed allocation, because stock `RG-RAM-15` is cheaper when extraction is charged. During onsite integration, select a failure from the actual validated solver allocation and inspect its alternative or no-spare outcome. Do not force an allocation to match the handwritten/Figma story while claiming unconstrained optimization.

**Fetch scheduling conflict:** Fetch conflicts with the proposed onsite build schedule, but its exact hours are unconfirmed. The hour blocks above are provisional effort allocations, not a confirmed availability schedule. Confirm the Fetch timing and actual Hackyard build window before freezing or promising onsite milestones; do not invent an overlap duration.

## Foundation validation actually performed — 16 October 2026

| Check | Actual result |
| --- | --- |
| `scripts/setup.ps1` | Exit 0; exact backend lock installed/confirmed and `npm ci` succeeded |
| `.venv\Scripts\python.exe -m pytest -q` | 30 passed; one upstream Starlette/httpx TestClient deprecation warning |
| Actual backend process restart | Included in the 30 tests: imported 12/31, stopped process, restarted against the same SQLite file, recovered counts/revision and safely retried commit |
| Atomicity / concurrency | Included: injected component-insert abort leaves zero inventory/assessments/fleet/audit writes; retry succeeds; two concurrent identical commits produce one revision/import event |
| `npm run test:e2e` from frontend | 1 Chromium flow passed: invalid preview, valid preview with zero inventory writes, commit, evidence inspection, hardware/health/physical eligibility, late-response rejection and desktop/390 px layouts |
| `npm run typecheck`, `npm run build` from frontend | Exit 0; production assets built |
| `.venv\Scripts\python.exe -m pip check` | No broken requirements |
| Original `scripts/validate_synthetic_fixture.py` | Exit 0; fixture/oracle unchanged and all 11 restricted expectations pass |

These are foundation checks, not completion of the planned validation matrix above. Actual screenshots under `docs/implementation-previews/` were inspected; formal accessibility review, full React Flow visualization, manual evidence editing, solver/output validation, approval/reservations, orders and verification tests remain later work.
