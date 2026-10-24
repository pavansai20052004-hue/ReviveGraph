# Proposed architecture

Status updated **20 October 2026**: registration/import, inspection, CP-SAT allocation, persisted simulation failure/replanning, approval/reservations, simulation work/verification and JSON reporting are implemented as disclosed preparation. [RECOVERY_CONTRACT.md](RECOVERY_CONTRACT.md) is authoritative for actual schema 2 and local endpoints; [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) records all 18 statuses. The broader contracts below remain product targets wherever they exceed that subset. AI, physical evidence review/execution and automatic reconciliation of started work are unimplemented.

## Boundaries and architecture choice

React/TypeScript/Vite renders six screens using Tailwind CSS, shadcn/ui, React Flow and Recharts. FastAPI owns validation, compatibility, evidence, optimization, approval and audit. SQLite stores inventory and immutable planning history. A Python OR-Tools CP-SAT module consumes a normalized snapshot. An optional provider adapter interprets logs and explains service results.

Choose a **modular monolith** with one local backend process over separate optimization/agent services: it keeps transactions and a solo build manageable. Separate services would help long-running or multi-tenant workloads but add deployment and consistency work without helping the constrained fleet. The implemented local solver runs synchronously in a FastAPI worker thread outside write transactions, with bounded search and a 120-second frontend request timeout. Durable asynchronous run IDs/polling below remain an enhancement; this explicit contract change avoids an unnecessary job queue for the constrained demo. A snapshot/approval race is checked again before result persistence. Retries reuse persisted logical results; a crash before persistence requires recalculation.

## Hardware and evidence contract

Only whole RAM modules and whole storage devices move. Motherboard, CPU, cooler, chassis, PSU and required integrated display capability form a **fixed base assembly**. A target requires an accepted healthy base; a faulty/unknown base can donate separately assessed healthy removable parts but cannot be counted recovered. Motherboard replacement, GPUs, laptops, soldered RAM, adapters, DDR5, NVMe/M.2 and proprietary systems are unsupported initially.

| Object | Required characteristics and conservative rule |
| --- | --- |
| Motherboard profile | Profile/version, declared supported RAM generation, voltage, non-ECC unbuffered UDIMM support, slot count, per-slot and total RAM limits, approved module configurations/speeds, SATA ports, boot support, usable 2.5-inch bay, SATA power/data connection availability. Missing decisive fields yield unknown. |
| RAM | DDR3 240-pin 1.5 V **or** DDR4 288-pin 1.2 V, non-ECC unbuffered full-size UDIMM, capacity in GiB, speed and profile evidence. No cross-generation pairing. Exclude SO-DIMM, registered/ECC and DDR3L-only cases. Each occupied slot takes one physical module; module-set rules are checked for the complete configuration. Mixed modules are unknown unless explicitly permitted by the profile. |
| Storage | One 2.5-inch SATA SSD/HDD per target; capacity in decimal GB, interface, form factor and condition evidence. Target must explicitly support the device's interface/boot requirements and have a suitable bay, port and power/data connection. No inferred cable or adapter availability. |
| Base / peripherals | Base condition is separately recorded. External keyboard, monitor and boot/install media are assumed available for the demo and disclosed; their allocation is outside the model. |

Compatibility is `compatible`, `incompatible` or `unknown`, with rule IDs, reasons and evidence references. Known disqualifiers yield incompatible; absent/unsupported information otherwise yields unknown. Only compatible edges may feed allocations. Synthetic board profiles describe a toy supported universe and must not be represented as manufacturer certification. Real hardware requires documented profile evidence and technician review.

Health is `healthy`, `faulty` or `unknown`; evidence has `synthetic` or `physical` provenance, source, timestamp and reviewer. AI suggestions are stored separately from accepted assessments. Synthetic healthy evidence is eligible **only in simulation**. Physical planning requires accepted physical assessments; observed symptoms alone are not a healthy certification. No fabricated numeric health scores or diagnostic readings.

Every part has a stable physical component ID, one legal owner and exactly one current location (installed computer, stock or quarantine). Historical origin is immutable; current installation changes only through recorded work steps. Transfers require the same owner or an explicit authorization record; cross-owner transfers are excluded from the first demo. Reservations do not change physical location. CSV repetition, a graph edge or a candidate match cannot create a second part.

## Proposed database entities

| Entity | Essential fields / constraints |
| --- | --- |
| Fleet, Computer | IDs, owner, mode, asset tag unique within fleet, base profile/health reference, version. |
| BoardProfile | Versioned normalized hardware fields, supported configuration rules and evidence source. |
| Component | Stable ID unique within fleet/mode, type/specs, owner, origin, location, assessment reference, version; location references at most one computer. |
| Assessment, DiagnosticSuggestion | Subject, evidence/provenance, accepted health/reviewer or unaccepted AI suggestion; preserve history. |
| ImportBatch | Input hash, schema version, validation report, committed IDs; idempotent batch commit. |
| Scenario, FailureEvent | Parent snapshot, mode, overlay revisions, failed part, actor/reason; no physical writes from scenario events. |
| PlanRun, Plan, Allocation | Run status, input hash/revisions, rule/model/solver versions, constraints, solver status/objectives; immutable plan; unique component allocation within plan. |
| Approval | Exact plan ID/hash, snapshot revision, approver, decision, time, reason and mode. |
| Reservation | Component, approved plan, reservation scope and status; unique active component reservation within physical fleet or simulation scenario. |
| WorkOrder, WorkStep | Approved plan, target, part IDs, dependencies, state, estimated cost/minutes, idempotency key; one order per target per plan. |
| Verification | Order, outcome, mode, checklist, technician, evidence refs, time; corrections append records instead of overwriting. |
| AuditEvent | Actor, action, entity, time, correlation ID, prior/new revision and reason; append-only at application level, not claimed tamper-proof. |

Enable foreign keys and transactional uniqueness constraints. Approval atomically checks revisions and reserves every allocated part, including retained parts. Order creation checks the approval and reservations again. Stale/concurrent requests return conflict, never partial success. SQLite permits one simultaneous writer; keep writes short and handle busy/retry deliberately ([SQLite transaction documentation](https://www.sqlite.org/lang_transaction.html)).

## Deterministic recovery model

Precompute supported **complete configurations** per target: accepted healthy base, at least 8 GiB RAM in valid slots within board limits, and one eligible storage device of at least 240 GB. Include retained installed components in these configurations so they consume the same finite stock as transfers. Only healthy, owner-authorized, unreserved parts in the active mode may participate.

Let binary `y[i,k]` select configuration `k` for target `i`. Enforce at most one configuration per target and, for every component `p`, `sum(y[i,k] containing p) <= 1`. A selected configuration defines a recovered candidate; an unselected donor is not counted. Allow zero selected configurations: “0 recoverable under these limits” is a valid solution, not automatically infeasible. Malformed models and contradictory mandatory constraints are distinct errors.

Derive a unique operation set from selected configurations and current locations: remove departing modules/devices, remove faulty occupants when required for space, install incoming parts, then verify each recovered target. Retained parts incur no removal/install charge; donor extraction and displaced-part handling are not free. Each physical removal occurs once even if the donor also receives replacements. Every operation has a nonnegative integer cash cost and technician duration; unknown cost/time blocks the affected option rather than defaulting to zero. Charge target preparation and verification once. No purchases in P0. Labor is constrained in minutes; monetary labor is included only if explicitly entered, avoiding automatic double-counting.

Hard constraints: total cost in integer INR paise <= budget, total technician minutes <= capacity, valid configurations, ownership, health, unique parts and existing reservations. Time is a single technician effort pool, not a promised completion schedule. Orders encode removal-before-install dependencies, including swaps through temporary stock; concurrent scheduling is deferred.

Optimize lexicographically: (1) maximize selected recovered computers, (2) minimize total cash cost, (3) minimize technician minutes, (4) minimize transfers, then (5) canonical tie-break by sorted asset/configuration IDs. Solve sequential stages with prior proven optima fixed; canonical tie-breaking must resolve remaining equal solutions explicitly. If a stage ends with only a feasible solution, retain it, report the incomplete priority stages and do not claim overall optimality. Never treat timeout as proof of infeasibility.

Pin solver/model/rule versions; use sorted inputs, a fixed seed, one worker and a recorded deterministic search limit. Log objective bounds, status and termination reason. External wall-clock cancellation is reported separately and cannot promise identical incumbents. Reproducibility claims apply only to the same normalized snapshot and solver settings. CP-SAT uses integer constraints and distinguishes OPTIMAL, FEASIBLE, INFEASIBLE, MODEL_INVALID and UNKNOWN ([official CP-SAT reference](https://developers.google.com/optimization/cp/cp_solver)). Independently validate every emitted configuration and resource total before making a plan approvable.

## API contracts (proposed `/api/v1`)

All objects carry IDs, mode and revisions. Mutating requests require an identified local demo actor, expected revision where relevant, and `Idempotency-Key`. Error shape: `{error: {code, message, field_errors, current_revision}, request_id}`. Use 422 for invalid fields, 409 for stale/conflicting state, 404 for missing IDs and 503 for unavailable optional providers. UI labels demo identity as non-secure; physical use or public hosting requires real access control first.

| Method / route | Request → response / behavior |
| --- | --- |
| `POST /imports/preview` | Fleet/mode + computer and component CSV files → batch ID/hash, counts, errors and normalized preview. No inventory mutation. |
| `POST /imports/{id}/commit` | Preview hash + expected fleet revision → atomic inserted records and new revision. Changed files require another preview. |
| `GET /computers`, `GET /components` | Fleet/scenario and filters → paginated inventory with provenance and health. |
| `POST /assessments` | Subject, health, evidence, provenance, expected revision → accepted human assessment; changes invalidate dependent plans. |
| `POST /diagnoses` | Subject + supplied log text/evidence references → suggestions/citations and provider status; never accepted health. |
| `GET /compatibility` | Snapshot ID + optional target → edges, decision/reasons and rule version. |
| `POST /plan-runs` | Snapshot/scenario revision, budget_paise, technician_minutes, policy version → 202 run ID. |
| `GET /plan-runs/{id}` | → queued/running/succeeded/failed/cancelled, solver status and plan ID if an independently valid solution exists. |
| `GET /plans/{id}` | → input hash, configurations, operation totals, excluded reasons, bounds, mode and supersession/staleness. |
| `POST /scenarios` | Parent plan/snapshot ID → isolated synthetic scenario revision. |
| `POST /scenarios/{id}/failures` | Component ID, reason, expected revision → failure event + new scenario revision; then call `/plan-runs` for the replacement. |
| `POST /plans/{id}/approvals` | Plan hash/revision, decision, actor, reason → approved/rejected record; approval reserves eligible parts atomically. |
| `POST /plans/{id}/work-orders` | Approval ID/hash → idempotent order set; rejects stale approval or wrong mode. |
| `GET /work-orders`, `PATCH /work-orders/{id}/steps/{step}` | Query orders or record expected-version step outcome/evidence → updated order, locations and audit in one transaction. |
| `POST /work-orders/{id}/verifications` | Outcome, checklist, evidence refs, actor, mode → append-only verification; pass requires completed work/checklist. |
| `POST /plans/{id}/release` | Reason + expected revision → release reservations/cancel pending orders only if no work started; started work requires reconciliation. |
| `GET /reports`, `GET /audit-events` | Scope/mode → provenance-bearing JSON report or paginated events. |

CSV schema v1 is two files: computers (`asset_id, owner_id, board_profile_id, base_health, provenance`) and components (`component_id, owner_id, location_asset_id, type, ram_generation, form_factor, capacity_gib, capacity_gb, speed_mt_s, voltage_mv, ecc, buffered, interface, health, provenance, evidence_ref`). Empty location means stock; type-inapplicable fields may be blank. Require correct units, valid references, unique IDs, legal enums, evidence for accepted health and consistent owner/mode. Preview reports invalid installed layouts. Physical health imports remain pending human review. Updating existing IDs is rejected in v1; re-uploading the identical committed batch is idempotent. Log/file size limits are configurable and must be fixed before implementation; imported text is untrusted.

## Revision, failure and execution lifecycle

Run state and solver status are separate. Plans progress draft → approved/rejected; revisions can become stale or superseded without rewriting history. Any relevant inventory/evidence/constraint/failure change invalidates prior approval. Simulation failures affect only the scenario overlay. A revised plan needs a new human approval. Replanning itself never moves parts.

Orders progress pending → in_progress → awaiting_verification → verified_pass / verification_failed / verification_inconclusive, or cancelled before work starts. An order for a recovered target includes its required donor extraction steps even when the donor is not itself recovered. Shared extraction is recorded once, and cross-order dependencies prevent installing a part before its removal is recorded. Scenario orders update scenario locations only. A real failure after work starts pauses affected work; completed transfers remain facts, and remaining reservations are reconciled before solving again. This recovery path is outside the first demo's pre-execution failure sequence but must fail closed. On process restart, interrupted runs become failed/retryable; reservations and completed work persist. Retrying requests cannot duplicate approvals, orders or transfers.

## AI, impact and trust

Adapter contract: `interpret_logs(evidence) -> suggestions + evidence_refs` and `explain_plan(validated_plan) -> explanation + referenced_ids`. Later agent tools may read inventory, request simulation/solve and draft explanations under call/time limits. No arbitrary shell, SQL, health certification, compatibility-rule editing, approval, purchasing or work execution tools. Treat logs as data, enforce schemas and identifier existence, and redact secrets before optional provider calls. Deterministic reason text remains available offline.

Impact starts with counts and budget estimates. Planned recovery is not actual avoided waste. Optional mass estimate = sum of explicitly sourced per-asset masses for physical verified passes, labeled “estimated mass retained in use,” with no component double-counting. CO2e requires a sourced replacement counterfactual, factor version and repair/transport adjustment; remain unavailable until chosen. Show scenario projections separately and never claim measured emissions savings or completed physical repairs from synthetic results.


## Local completion slice — 25 October 2026

Synthetic health now resolves through each subject's current assessment pointer;
original imported row JSON and append-only prior assertions remain intact. New
assessment routes use fleet-revision/current-assessment CAS and prohibit editing
behind approved or recorded execution. No physical-health authoring was introduced.

The additive schema-2 continuation table stores one immutable reviewed child per
paused context revision. `reconciliation.py` reconstructs sunk charges from priced
completed operations and every verification attempt, preserves scenario locations,
and runs the existing locally validated solver with residual caps. Ancestor
verification policy is inherited even for temporarily unselected targets. Old
contexts stay paused; new exact approval/reservations and a new operation DAG are
required. No source fixture, deterministic compatibility rule or ordinary snapshot
optimizer behavior changed. See RECOVERY_CONTRACT.md for the additive API.

Agent37 transport/settings/actions are removed. Local canonical evidence summaries
remain. The Adaption dataset pipeline and real accepted artifact remain provider
independent preparation; runtime AI is deferred. Hosted Render remains blocked by
the recorded billing requirement, and Nodus work is postponed.
