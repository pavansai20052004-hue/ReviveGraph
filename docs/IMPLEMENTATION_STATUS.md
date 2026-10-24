> **Current status: 25 October 2026.** See [LOCAL_PRODUCT_STATUS.md](LOCAL_PRODUCT_STATUS.md)
> for the accepted local scope, all 18 current capability boundaries, Agent37 removal,
> synthetic assessment authoring and reviewed continuation. The dated tables below
> are preserved as historical foundation/integration snapshots.

# Capability status — 20 October 2026

Status refers to the supported local **synthetic simulation**. Implemented means the specified constrained path exists and was exercised, not real-hardware certification or a production service. Original acceptance criteria remain in PRODUCT_SPEC; current endpoints and limitations are in RECOVERY_CONTRACT.

The 20 October screenshot-led interface pass added real dashboard comparisons/activity, a dedicated Reports workspace and read-only fleet-scoped audit querying. It preserved the core simulation capability boundaries below. The complete three-flow Chromium suite and nineteen focused audit/lifecycle backend tests passed; this is additional UI/read-API validation, not a claim that all physical or AI features exist.

| # | Planned capability | Status | Current boundary |
| --- | --- | --- | --- |
| 1 | Dashboard | Implemented | Backend inventory, latest solver totals, distinct recorded simulation/physical counts; no invented environmental savings. |
| 2 | Computer Inventory | Implemented | Persisted 12-asset import, evidence/profile details, initial usability and concrete blockers. Physical inventory remains unchanged by simulations. |
| 3 | Component Inventory | Implemented | 31 unique physical IDs, ownership/current/import-origin locations, health/evidence inspection; simulation reservations remain scoped to approved plans. |
| 4 | Bulk CSV Import | Implemented | Both-file preview with errors, no inventory preview writes, atomic/idempotent commit, restart persistence. |
| 5 | AI Diagnosis | Unimplemented | No provider/model or log interpretation; Diagnostics exposes imported evidence separately and states AI is not configured. |
| 6 | Component Health Assessment | Partial | Per-subject imported assertion/evidence inspection; manual accepted-health editing and reviewed physical assessment workflow absent. |
| 7 | Compatibility Graph | Implemented | Deterministic inspection plus interactive React Flow target/part graph and full tabular alternative; focused view rather than arbitrary fleet layout. |
| 8 | Smart Parts Matching | Implemented | Deterministic eligible complete configurations and explainable exclusions; actual allocation uses unique physical IDs. |
| 9 | Recovery Optimizer | Implemented | OR-Tools CP-SAT lexicographic allocation, proof/termination metadata and independent output validation. |
| 10 | Budget and Resource Constraints | Implemented | Strict integer paise/minutes, exact/zero boundaries, retained/donor/displacement/install/prep/verify accounting. |
| 11 | Recovery Simulator | Implemented | Named isolated rehearsal contexts, scenario failures/locations, actual plans and simulated execution; no physical writes. |
| 12 | Autonomous AI Agent | Unimplemented | No provider adapter, bounded AI tool loop or AI-origin actions. |
| 13 | Failure Replanning | Partial | Pre-work selected-component failure with linked replanning, no-spare result and comparison works. Post-start safe pause works; automatic reconciliation/resume remains absent. |
| 14 | Human Approval System | Implemented | Explicit current-plan/hash review/rejection, transactional component/target reservations, stale/conflict guards and idempotent retry; local demo identity is not authentication. |
| 15 | Repair Work Orders | Partial | Traceable persisted simulation orders, extraction/install dependencies, checklists/evidence and restart. Physical execution and post-failure reconciliation absent. |
| 16 | Recovery Verification | Partial | Authored simulated pass/fail/inconclusive, prerequisite/checklist/final-location checks and evidence. No real hardware inspection or physically verified repairs. |
| 17 | Impact Analytics | Partial | Planned/simulated/physical counts and resource estimates separate; no sourced environmental model, avoided-waste or CO₂e claims. |
| 18 | Reports and Audit Trail | Implemented | Downloadable provenance-bearing JSON of inputs, assumptions, revision history, approval, operations/progress, verification and scoped audit events. PDF/export formats and tamper-proof retention absent. |

## Actual main-fixture computation

Budget 250,000 paise / 330 technician minutes, original synthetic-v1 imported inventory: **7 usable final / 7 newly recovered candidates, 215,000 paise, 299 minutes, 7 transfers**. CP-SAT reports OPTIMAL for all four objectives and exact stable tie-breaking; 657 generated complete configurations. These are computed simulated plans, not completed computers. The same-snapshot greedy result also has 7 / 215,000 / 299 / 7. No main-fleet uplift is claimed. The restricted two-target greedy trap is proven at 2 versus 1 by tiny enumeration and CP-SAT.

| Target | Selected RAM | Original selected storage | After actual donor `RG-SSD-10` failure |
| --- | --- | --- | --- |
| RG-PC-01 | RG-RAM-01 | RG-SSD-06 | Same |
| RG-PC-02 | RG-RAM-11 | RG-SSD-02 | Same |
| RG-PC-03 | RG-RAM-03 | RG-SSD-10 | RG-SSD-11 |
| RG-PC-04 | RG-RAM-15 | RG-SSD-05 | Same |
| RG-PC-05 | RG-RAM-05 | RG-SSD-12 | Same |
| RG-PC-06 | RG-RAM-12 | RG-SSD-07 | Same |
| RG-PC-07 | RG-RAM-08 | RG-SSD-15 | Same |

The actual donor SSD-10 starts in PC-09; revised SSD-11 starts in PC-11. Both are assessed individually in the synthetic fixture; a donor's uncertain/faulty base does not certify or disqualify its separately eligible removable parts. PC-09/PC-11 are not counted recovered. Revised totals remain identical and OPTIMAL. Stock RAM-15 is selected rather than the old handwritten donor RAM-07; the original donor-demo risk was real and was handled by choosing a failure from computed output.

Operation totals before and after: 7 prepare, 3 RAM removal, 4 storage removal, 3 RAM installation, 4 storage installation, 7 verification. Cash: `7×10000 + 3×2000 + 4×3000 + 3×5000 + 4×7000 + 7×12000 = 215000`. Effort: `7×10 + 3×5 + 4×6 + 3×8 + 4×10 + 7×18 = 299`.

The automated isolated acceptance rehearsal recorded seven **authored simulation passes** after saving and reopening its temporary database; physical passes and physical inventory usability remained zero. The browser rehearsal recorded one authored simulation pass and exported JSON. Neither is technician approval or observed diagnostic evidence. The receipt under ignored `data/recovery-rehearsal-20261020.json` contains the actual run/report, not a production input.


## Onsite integration status — 24 October 2026

The table and main-fleet computation above describe the disclosed pre-event
foundation. New onsite code now adds optional Nodus CPU execution, four-stage
local orchestration, Render Workflows task source/hosted trigger and a grounded
Agent37 plan assistant. This updates the integration boundary, not the history
of who implemented the original local optimizer.

- Capabilities 9/10/18: local calculations now retain stage trace and calculation
  audit artifacts. Nodus and Render adapters are implemented and tested with
  transport doubles; actual cloud runs remain blocked/unverified.
- Capability 5: hardware log interpretation/AI diagnosis is still unimplemented.
  Diagnostics additionally supports actual saved-plan explanations and explicit
  local facts. The Agent37 transport requires a reviewed dedicated instance,
  credentials, activation and a real validation call before live completion.
- Capability 12: bounded read-only fact selection is implemented as the first
  assistant slice. An autonomous mutating agent is still unimplemented. AI has
  no approval, health-editing or work-completion authority.
- Capability 13 and execution: pre-work replanning and existing post-start safe
  pause remain. Reconciliation, renewed approval and safe resume remain absent.

All 18 capabilities remain in PRODUCT_SPEC. Physical repair counts remain zero.
No cloud usage, completed hardware repairs or environmental savings are inferred.
See ONSITE_WORK.md and the integration documents for executed checks and account
blockers.
