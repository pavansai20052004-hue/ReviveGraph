# Local synthetic product — 25 October 2026

The accepted scope is the complete **local synthetic recovery workflow**. The
participant explicitly deferred AI diagnosis/autonomous AI and physical repairs,
requested removal of Agent37, and postponed further Nodus work. Earlier dates,
results and provider work remain historical records, not newly claimed work.

## All 18 planned capabilities

| # | Capability | Current supported boundary |
| --- | --- | --- |
| 1 | Dashboard | Implemented; actual inventory, plan, progress and audit data. Aggregate simulation passes are historical records across rehearsals. |
| 2 | Computer Inventory | Implemented; persisted assets, profiles, evidence, usability and blockers. |
| 3 | Component Inventory | Implemented; unique component identity, ownership, physical location and original import origin. |
| 4 | Bulk CSV Import | Implemented; both-file preview, explicit transactional/idempotent commit and restart persistence. |
| 5 | AI Diagnosis | Explicitly deferred. Manual evidence inspection remains available. |
| 6 | Component Health Assessment | Implemented for authored synthetic assertions with append-only history and revision guards. Physical review remains deferred. |
| 7 | Compatibility Graph | Implemented; deterministic graph/table, compatibility and eligibility are separate. |
| 8 | Smart Parts Matching | Implemented; complete compatible configurations and one-use component allocation. |
| 9 | Recovery Optimizer | Implemented locally; CP-SAT, proof metadata, independent validation and greedy comparison. |
| 10 | Budget and Resource Constraints | Implemented; integer paise/minutes, retained/donor/displacement work, continuation sunk charges and bounded verification retries. |
| 11 | Recovery Simulator | Implemented; named independent contexts and explicitly linked continuations. Physical inventory is unchanged. |
| 12 | Autonomous AI Agent | Explicitly deferred. Agent37 transport/configuration/actions have been removed; local deterministic evidence summaries remain. |
| 13 | Failure Replanning | Implemented before work, plus explicit reviewed post-start reconciliation into a linked continuation with remaining limits. |
| 14 | Human Approval System | Implemented; exact-plan review/rejection and transactional reservations. Continuations require renewed approval. Demo actor labels are not authentication. |
| 15 | Repair Work Orders | Implemented for simulation; dependency-ordered extraction/install/checklists and residual work after reconciliation. |
| 16 | Recovery Verification | Implemented for authored simulated pass/fail/inconclusive results. No physical diagnostic or repair claim. |
| 17 | Impact Analytics | Actual operational counts/resource projections implemented. Environmental estimates deferred without sourced assumptions. |
| 18 | Reports and Audit Trail | JSON export implemented, including continuation ancestors, decisions, operations and authored evidence. PDF is a later enhancement. |

This is completion of the accepted local scope, not a claim that all original
production/AI/physical enhancements exist.

## Synthetic assessment authoring

Inventory details and manual evidence inspection expose assessment history and
an explicitly acknowledged synthetic assertion form. Authoring requires a source,
`synthetic:` evidence reference, supplied actor, expected fleet revision and current
assessment ID. Old assertions and original imported row JSON remain unchanged.
Only the effective assessment pointer changes; the fleet revision increments and
unapproved plans become stale. The recorded timestamp is the actual server
authoring time, separate from the preserved original import time.

This action cannot make a subject physically reviewed. It is blocked for physical
subjects/fleets and for a fleet with approved or recorded work. Author a separate
imported synthetic fleet rather than mutating the evidence behind execution.

## Interrupted work and continuation policy v1

1. Failure after any completed operation pauses the source context, preserves
   completed steps/locations/evidence, and releases its reservations.
2. Select the actual approved paused plan that recorded work. An unused plan
   cannot supply larger resource ceilings.
3. Review the preview of saved scenario locations, failures and incurred charges.
   Every completed non-verification operation is charged once; every verification
   attempt, including fail/inconclusive, is charged separately.
4. Explicitly acknowledge the preview and supply an authored simulation evidence
   reference. One continuation is permitted per paused context revision.
5. A new linked context starts from those saved locations and exclusions. Its
   local solve uses original ceilings minus incurred charges, with immutable
   lineage/accounting bound into its snapshot hash. Source orders remain paused.
6. Previously completed component moves are not replayed. Fresh preparation and
   verification are conservatively charged for interrupted targets. Required
   verification IDs carry through every ancestor, including temporarily unselected
   targets. This is an explicit conservative accounting policy, not measured labor.
7. Review and approve the exact new plan, then create its residual work orders.
   A saved review or earlier approval never starts the continuation automatically.

Retries after interrupted calculation resume the same prepared continuation.
Stale review hashes and competing branches fail closed. Remaining headroom in a
plan is a **projection**; a reconciliation preview reconstructs recorded charges.
Repeated verification also reserves the other planned work before allowing another
priced attempt. A continuation may recover fewer targets when prior work consumes
resources; no expected recovery count is forced.

`newly_recovered` keeps the existing optimizer meaning: relative to authored
health/usability in that snapshot before scenario failure exclusions. Do not add
recovery counts across revisions or treat historic simulation passes as currently
repaired physical machines.

## Provider status

- **Agent37:** removed from active app code/settings/UI. Obsolete provider requests
  receive HTTP 410 before a request record or network call. Historical provider
  audits, source history and disclosure are preserved. Local summaries are fixed
  validated facts, not natural-language AI answers.
- **Adaption:** the real completed 24 October dataset run and immutable accepted
  artifact remain preserved. SDK/mock tests, exact dataset reproduction and offline
  artifact acceptance pass. It is now dataset preparation for a future provider;
  no runtime inference is performed and no application-accuracy gain is claimed.
- **Render:** local four-stage pipeline and hosted task/client source pass tests;
  the Blueprint now explicitly names its repository/branch and authenticated
  validation returns valid. No deployment or paid run was retried. The recorded
  billing requirement and native-Windows task-server `/tmp` blocker remain.
- **Nodus:** existing source is preserved and backend regressions pass. New cloud
  integration work and live execution remain postponed by participant instruction.

## Validation actually executed

- Backend full suite: **176 passed**, 111.42 seconds; one existing upstream
  Starlette/httpx deprecation warning. Includes 9 continuation tests, 4 assessment
  tests, and process-scoped external-network denial for local solve/evidence.
- Chromium original recovery flow: **1 passed**, 30.2 seconds.
- Chromium local evidence/removed-provider flow: **1 passed**, 12.9 seconds.
- Chromium new local-product flow: passed import/authoring/calculation, post-start
  failure, reconciliation, new approval, work, simulated verification, export and
  reload; desktop and 390 px geometry checked. Browser non-local requests blocked.
- Frontend typecheck/production build and `pip check`: passed.
- Original synthetic fixture/oracle: passed all 11 tiny cases; original bytes and
  PRE_EVENT_WORK unchanged. Explanation dataset: 12 train/4 held out, exact bytes.
- Real Adaption artifact hash accepted offline:
  `8e85fb150d0eb244351187248b5daf6756a35a8a0a6139c2caf8c1842c3de916`.
- Authenticated Render Blueprint validation: `valid: true`, one planned workflow.
  Validation is not deployment.

Initial broad regression found one old restricted-case test writing legacy row
health without its now-authoritative assessment; its setup was corrected while
retaining its one-target/zero-spare assertions. The first offline guard blocked
Windows asyncio's own loopback socket pair; it was corrected to allow loopback
while rejecting external connections/DNS. Browser test-driver corrections scoped
an assertion to the visible history and waited for work-order persistence.
Independent review reproduced two real continuation defects (unused-plan ceiling
escalation and lost ancestor verification); both have fixes and regressions.

Validation used isolated databases. Checklists, approvals and evidence in these
runs are **automated test-authored simulation records**, not participant-entered
technician evidence. Physical repair totals remain zero. This is not a fresh
OS-level airplane-mode, hosted deployment or offline dependency-installation test.

## Repeat the local demo

Start backend/frontend using README commands. For an isolated run, set a new
`REVIVEGRAPH_DB` only in that backend process; keep the normal database untouched.
Import preview → inspect 12/31 → commit → inspect evidence/compatibility → calculate
at ₹2,500/330 minutes → approve → create orders → record one preparation with
clearly authored simulation evidence → fail an allocated donor → review the paused
reconciliation → supply `synthetic:` review evidence → calculate continuation →
renew exact approval → follow residual prerequisites/checklists → simulated
verification → export JSON → reload to inspect saved history.

For the simpler judging flow, inject failure before approval/work and use the
existing direct before/after replan. Both paths preserve original allocations.
