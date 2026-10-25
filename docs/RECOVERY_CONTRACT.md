# Implemented recovery contract — 0.2.0

Disclosed preparation dated **20 October 2026**, authorized by the participant to advance the central application before the event. This extends the preserved [0.1.0 foundation](FOUNDATION_CONTRACT.md); no original fixture, preparation oracle, native Figma file, checkpoint tag or recovery archive was replaced. These are simulated planning/execution capabilities, not physical repair certification.

## Model, versions and costs

`configuration-cpsat-v1` consumes an imported inventory snapshot with its individual assessments, registered profiles, exact source hashes, `desktop-inspection-v1` rules and `operation-costs-v1` catalogue. OR-Tools is pinned to `9.15.6755`; the independent output validator is `allocation-validator-v1`, greedy baseline `asset-id-greedy-v1`, lifecycle `recovery-lifecycle-v1`. Registered `scenarios.json` remains a hashed provenance reference only. The production engine does not import handwritten allocations or the preparation oracle.

Candidates are complete configurations: healthy eligible fixed base, a supported whole-module RAM set totaling at least 8 GiB, and one eligible 2.5-inch SATA drive of at least 240 GB. Unknown/faulty health, unreviewed physical assertions, unknown decisive hardware fields, ownership mismatch and reservations block use. Only simulation is available through lifecycle APIs; physical planning/execution requires a later evidence/profile/review implementation. Motherboard/CPU and peripheral transfers remain outside scope.

CP-SAT selects at most one configuration per target and at most one use per physical part across all targets, including retained parts. A donor is counted only if its own complete final configuration is selected. A global Boolean OR charges a departing installed part's removal once, even when both donor extraction and displacement apply. Selected targets discard all installed parts absent from their approved final configuration. Incoming parts require installation. Changed targets require one preparation and verification; an already usable unchanged retained configuration requires neither and is not newly recovered. Stock carries no acquisition price in this fixture. All money is integer INR paise; technician effort is integer minutes. No purchases, wage multiplier, extra storage price or undocumented preparation fee is invented. Target preparation covers the fixture's handling/consumables assumption; data-handling checks do not execute a wipe.

Objectives are solved sequentially: maximize usable final count, minimize cash, minimize effort, minimize transfers, then exact lexicographic target/configuration rank (an unselected target ranks after selected configurations). Each objective is fixed only after its optimum is proven. Sorted candidates, one search worker, seed 0 and 2.0 deterministic CP-SAT time units per phase are recorded. Wall cancellation additionally caps each phase at 10 seconds and solver phases at 60 seconds aggregate; cancellation can leave only a feasible incumbent. Deterministic-time and wall-time limits are different units. Reproducibility of incomplete wall-limited incumbents is not guaranteed. Candidate generation is capped at 25,000 complete configurations and 100,000 RAM sets; the baseline/validation and HTTP overhead are outside the solver-phase wall cap.

Responses retain actual last-attempted solver status, phase values/bounds, proven objectives, stable-tie proof, termination reason and limits. A later UNKNOWN can preserve the earlier independently validated incumbent as FEASIBLE, with actual last-attempted status still UNKNOWN. An initial UNKNOWN is not an optimum or an approvable computed result. API calculation requires an OPTIMAL/FEASIBLE validated incumbent; it does not persist a success for an unknown/invalid outcome. All-zero allocation is a valid proven feasible solution when limits or candidates prevent recovery.

The independent validator checks selected IDs, complete hardware/health/ownership eligibility and one-use constraints directly, then reconstructs the operation ledger and sums it against both hard limits. It does not trust CP variables, candidate membership, reported totals or solver status. Approval and work creation run it again. The greedy baseline visits targets in ID order, selects the cheapest feasible incremental complete configuration, then breaks equal cash by time and component IDs. This follows FIXTURE_SPEC's documented greedy trap; the older BUILD_PLAN's proposed extra transfer tie-break is superseded. The main fixture yields equal optimizer/baseline totals; uplift is claimed only for the proven restricted tiny trap.

## Persistence and input identity

SQLite schema **2** adds `recovery_contexts`, `recovery_plans`, `recovery_requests`, `recovery_decisions`, `recovery_reservations`, `recovery_failures`, `recovery_orders`, `recovery_steps` and `recovery_verifications`. A `BEGIN IMMEDIATE` migration creates tables and sets `user_version=2` atomically, preserving existing v1 inventory/evidence/import rows. Unknown schema versions are refused. No normal user database was migrated during validation; tests/rehearsals use isolated files. Before first starting the upgraded app against valuable v1 data, stop the backend and copy the SQLite file to a backup location. The source-only original ZIP is not a live database backup.

Plans retain immutable input snapshot, source/registration hashes, inventory/context revisions, mode, engine versions, scenario identity, constraints, parent link, result, input hash, snapshot hash and output hash. Status, decisions and execution progress are separate persisted lifecycle state. A scenario identity is `fleet:context:revision`. Contexts hold failed-component and simulated-location overlays; they do not alter physical `components`, base health or imported assessments.

Solving runs as a bounded synchronous FastAPI worker-thread operation outside write transactions. This deliberately differs from ARCHITECTURE's proposed durable asynchronous `/plan-runs` polling contract: for the constrained local fleet, a synchronous result with a 120-second UI timeout is the smaller implemented boundary. A production job queue/cancel API remains later work. A fresh read transaction captures a consistent snapshot; the post-solve write transaction rereads inputs and reservations before saving. A crashed calculation has no partly written plan/reservation; retry computes again or returns an already saved plan under the same key.

Simulation contexts are independent rehearsals. Within one `(fleet, simulation, context)` at most one plan may be approved. Reservations uniquely lock every selected part **and target**, including retained parts. This conservative one-approved-plan policy also prevents competing donor extraction/displacement operations even when two final configurations use different parts. Existing reservations block a new calculation in that context. Use the UI's new-rehearsal/context control to compare an independent execution. Physical and simulation scopes cannot share reservations because physical execution is unavailable rather than implicitly authorized.

## Actual API additions

All routes below have `/api/v1` prefix and use existing error envelopes. POST requests require nonblank `X-Actor-ID` and `Idempotency-Key`. Identity remains an unauthenticated local label. An idempotency key binds route, complete body and actor; differing reuse returns 409. Approval, reservation, order creation, step completion and verification write response replay records in the same transaction as their mutations. Successful retries return the original logical result/current plan rather than duplicate rows.

| Method / path | Implemented contract |
| --- | --- |
| `POST /plans` | `{fleet_id:"RG-DEMO-12",context_id:"demo",budget_paise:250000,time_minutes:330}`; nonnegative strict integers, zero is a hard limit. Returns a validated immutable computed plan, solver metadata and same-input greedy baseline. |
| `GET /plans?fleet_id=...` | Latest plans, newest first, default limit 50/max 200. Includes effective stale state, decisions and orders. |
| `GET /plans/{id}` | One persisted plan, exact snapshots/result and current execution state. |
| `POST /plans/{id}/failures` | `{component_id}` must refer to that plan's actual selected part. Commits a simulation overlay revision and failure event, stales old context plans/releases their reservations, then computes linked replacement with original constraints. Idempotent crash recovery resumes a pending replan without applying failure twice. |
| `POST /plans/{id}/decision` | `{decision:"approve"|"reject",input_hash}`; exact current validated plan, current revisions and unchanged output required. Approval atomically records decision/reservations. Rejection creates no reservations. A decided plan cannot flip decision; calculate a new plan. |
| `POST /plans/{id}/work-orders` | `{}`; current valid approval and complete reservation set required. One order per changed target. Repeats return the same orders; no order before approval. |
| `POST /work-orders/{id}/steps/{step}` | `{evidence_ref,checks:[required_check_ids]}`. Every prerequisite and checklist item must be complete; evidence must be nonblank. Writes actor/time, authored simulation evidence and scenario location in one transaction. Verify steps use the verification route. |
| `POST /work-orders/{id}/verification` | `{outcome:"pass"|"fail"|"inconclusive",evidence_ref,checks:[...]}`. All non-verification dependencies required; pass also requires every verification check and final installed component IDs matching the approved configuration. Records append-only outcome/evidence. |
| `GET /plans/{id}/report` | JSON `recovery-audit-v1`: pinned inputs/evidence/cost assumptions, immutable results and context history, failure chain, decisions, work/check evidence, verification and scoped audit events. No environmental estimate; physical repair count remains zero. |
| `GET /state` extension | Actual latest solver status/totals/plan status plus stored order/plan counts and separate simulated/physical pass counts. An empty database still says Not calculated. Physical counts describe the unavailable physical workflow, not a simulated repair. |

This implemented vocabulary supersedes the proposed `/approvals`, `/verifications`, `/scenarios` and `/plan-runs` routes for the local core. CSV v1, registration sidecars and inventory inspection contracts are unchanged. Report events are application audit history, not a tamper-proof ledger or access-controlled evidence archive.

## Work, failure and verification boundaries

Global operations become traceable per-target work orders. Donor-only extraction is attached to a receiving target. Dependencies are preparation → removals → installations → verification; every installation waits for all plan removals, including removals in other orders. This conservative barrier makes swaps acyclic through temporary simulated stock. Checks explicitly include component identity, data handling for storage, authored installation/extraction and simulated boot/memory/storage checks. Evidence fields are entered by the operator; no diagnostic values are fabricated or inferred.

Steps and scenario locations persist across restart. Repeating a completed step under a different request does not overwrite its evidence. Verification outcome corrections append rather than edit earlier records; current order status reflects the latest recorded outcome. Dashboard simulated-pass counts aggregate work orders with current pass status across independent rehearsal contexts; they are not counts of unique physical computers repaired. A pass does not create or improve physical evidence, change physical component locations, or increase physical verified repair counts. Failed/inconclusive outcomes remain visible and do not count as passes.

Before execution, a selected-component failure produces a revised plan and disables the prior approval/orders. **After any work step has started, failure is recorded, unfinished orders pause and completed overlay locations/evidence remain facts.** Automatic reconciliation/replanning from partly executed work is deliberately blocked with `RECONCILIATION_REQUIRED`; review that history and create an independent rehearsal context. This is a safe pause implementation, not a completed reconciliation workflow. Completed terminal verification facts remain in history.

Manual health editing/physical review, arbitrary fixture libraries, authenticated multi-technician operation, AI diagnosis/agent tools, physical execution, formatted PDF reporting, environmental factors and a general scheduling engine remain unimplemented. No central capability should be labeled physically validated from this synthetic run.

Implementation references: [CP-SAT integer/status semantics](https://developers.google.com/optimization/cp/cp_solver) and [SQLite transaction behavior](https://www.sqlite.org/lang_transaction.html). Actual validation evidence and capability status are recorded separately in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md), README and PRE_EVENT_WORK.

## Read-only audit feed and Reports interface — 20 October 2026

`GET /api/v1/audit-events` now exposes real fleet-scoped audit history for Dashboard/Reports. Parameters are `fleet_id` (default RG-DEMO-12), nonnegative `offset`, `limit` 1–200 (default 50), and optional exact `action` (max 100 characters). Response includes decoded `items`, `total`, `offset` and `limit`, ordered by descending event ID. Related batches, assets, components, plans, orders, failures and verifications establish scope through parameterized relational queries. Shared registrations are excluded to avoid cross-fleet event exposure. Reads do not create audit or inventory writes. The Reports UI selects existing plans, reads the existing report contract, filters/paginates actual events and downloads the real JSON report. The underlying allocation, approval, reservation and execution contracts remain unchanged.


## Onsite execution and explanation additions — 24 October 2026

`POST /api/v1/plans` now accepts optional `execution: local|nodus` and
`orchestration: local|render`, both defaulting to local. The request remains the
same integer-budget/minute, simulation-only contract. Every execution completes
input validation, execution, result validation and audit generation. Cloud
providers are explicit opt-ins; no silent local fallback is allowed. The
existing authoritative lifecycle still rebuilds/rechecks its snapshot,
reservations and revision before persistence. No database schema migration or
fixture modification was required.

Plan `execution` metadata records the actual CPU provider separately from its
`workflow.orchestrator`, task/job IDs where supplied, trace hashes and audit
artifact. Missing pre-event metadata remains missing; it is not retroactively
invented. Failure replanning inherits both choices from its parent. Caps are
per Nodus job; Render orchestration is billed separately. Account availability
does not establish activation, credits or a successful run.

Read-only assistant context and explicit local/Agent37 explanation routes are
specified in ASSISTANT_INTEGRATION.md. Explanations append audit records but
cannot approve, mutate hardware assertions or complete work. All old physical
and post-start reconciliation boundaries above still apply. Live provider
success remains unverified; see ONSITE_WORK.md for actual checks.


## Additive local contract — 25 October 2026

The existing schema-2 initialization now also creates `recovery_reconciliations`
without rewriting existing inventory, plans or historical evidence. It uniquely
links a paused context revision to a new continuation context and stores immutable
review/source-state/accounting hashes. Existing snapshots without continuation
policy fields retain the original optimizer behavior. Policy
`reviewed-simulation-continuation-v1` adds hashed snapshot fields
`continuation_policy_version`, `reconciliation_hash`, and
`verification_required_asset_ids`; selected interrupted targets incur fresh priced
preparation/verification even when installations are already complete.

- `GET /plans/{id}/reconciliation-preview`: only the approved paused plan that
  recorded work; returns source-state hash, actual incurred operation attempts,
  original ceilings, remaining limits, scenario locations and failure exclusions.
- `POST /plans/{id}/reconcile`: `{source_state_hash, reviewed: true,
  evidence_ref: "synthetic:..."}`, standard actor/idempotency headers. Creates or
  resumes the same reviewed linked local calculation; no automatic approval.
  Returns the new validated plan with `reconciliation` and `resource_accounting`.
- Child budget/time are pinned to original ceilings minus all ancestor/current
  consumed charges. The old source stays paused; normal exact approval,
  reservation and work-order guards authorize only the new revision.
- Stale state, unused source plan, altered lineage/accounting and a competing
  continuation fail closed. Crash retry uses the original request/body/key.
- A repeated verification attempt now reserves the other planned work and charges
  one additional verification operation before accepting evidence. If it cannot
  fit the current plan's limits, returns `VERIFICATION_RESOURCES_EXHAUSTED`.
- Reports include all linked context ancestors and their order audit events.

`GET /assessments/{computer|component}/{id}` returns append-only history/current ID.
`POST` requires `{health, expected_revision, expected_assessment_id, source,
evidence_ref: "synthetic:...", notes, simulation_only: true}` plus normal headers.
It appends an authored assertion and updates the effective assessment pointer and
fleet revision atomically. Original row JSON and old assessments are preserved.
Authoring is blocked for physical subjects/fleets and fleets with approved or
recorded execution. It never supplies human-reviewed physical evidence.

`POST /plans/{id}/assistant` supports provider `facts` only; obsolete external
provider values return HTTP 410 `EXPLANATION_PROVIDER_REMOVED` before writes/network.
Local context/version/audit history remain compatible. Historical non-local answers
are labeled as historical records from a removed provider.
