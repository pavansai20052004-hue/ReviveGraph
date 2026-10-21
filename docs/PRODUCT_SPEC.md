# Product specification

Status updated **20 October 2026**: the participant authorized advancing the core as disclosed preparation. The local synthetic import → compute → fail/replan → approve → work → simulated verification/report flow is implemented. [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) records all 18 current statuses; [RECOVERY_CONTRACT.md](RECOVERY_CONTRACT.md) records actual APIs and safe limits. Acceptance criteria below define product intent; they do not imply complete physical/AI capability or change the dated earlier disclosure.

## Purpose, users and success condition

Help a college IT technician or refurbishment operator decide which machines to recover across a fleet, which parts to move and what resources are required. A supervisor reviews the plan before work orders exist. In the local solo demo, one person may play both roles using a clearly labeled demo identity; this is not production authentication.

The core demonstration succeeds when the planned 12-machine synthetic import produces an auditable feasible plan, a simulated donor failure produces a new plan excluding that part, the old revision cannot authorize work, and human approval creates traceable orders whose verification remains labeled simulated. No target recovery count or speed is asserted before the fixture and solver are built.

## All 18 capabilities and priorities

P0 = core onsite demonstration. P1 = enhancement after the reliable core; neither category implies completion. Capabilities share six main screens rather than requiring eighteen routes.

| # | Capability | Workflow / priority | Testable product acceptance criterion |
| --- | --- | --- | --- |
| 1 | Dashboard | Overview; P0 | Show fleet size, eligible stock, planned recoveries, simulated passes and physical passes separately; empty data shows no invented totals. |
| 2 | Computer Inventory | Intake; P0 | List assets with base health, motherboard profile and installed components; opening an asset exposes provenance and blockers. |
| 3 | Component Inventory | Intake; P0 | Inventory tab tracks each physical part by unique ID, owner, location, health and reservation; duplicate IDs cannot create extra stock. |
| 4 | Bulk CSV Import | Intake; P0 | Preview both computer and component CSVs; show row/field errors and commit a valid batch atomically; retry cannot duplicate assets. |
| 5 | AI Diagnosis | Assessment; P1 | An optional provider returns evidence-linked suggestions from supplied logs; unavailable service and unsupported claims remain visible, without changing accepted health. |
| 6 | Component Health Assessment | Assessment; P0 | A human can record healthy/faulty/unknown with source and evidence; synthetic observations are marked synthetic and unknown is ineligible. |
| 7 | Compatibility Graph | Assessment; P0 | Edges expose deterministic compatible/incompatible/unknown decisions and reasons; filtering and a tabular alternative preserve this information. |
| 8 | Smart Parts Matching | Planning; P0 | Candidates contain only eligible compatible parts and include explainable rejection reasons for others; candidates are not reservations. |
| 9 | Recovery Optimizer | Planning; P0 | Return feasible complete configurations with solver status and objective values; a part is assigned at most once across the entire fleet. |
| 10 | Budget and Resource Constraints | Planning; P0 | Integer cost and time totals never exceed supplied nonnegative limits; zero is a valid hard limit, not “unlimited.” |
| 11 | Recovery Simulator | Rehearsal; P0 | Fork a scenario and preview transfers/results without mutating physical inventory or creating physical passes. |
| 12 | Autonomous AI Agent | Guided assistance; P1 | A bounded propose → tool → explain loop logs actions and stops at approval; attempted health writes, approval or arbitrary execution are denied. |
| 13 | Failure Replanning | Rehearsal; P0 | Inject one donor failure, retain the original plan, produce a linked replacement and show changed allocations, cost and count. |
| 14 | Human Approval System | Authorization; P0 | Only a current validated plan can be approved by an identified human; stale approval is rejected after evidence or constraints change. |
| 15 | Repair Work Orders | Execution; P0 | Approved allocations produce idempotent orders with part IDs, removal/install dependencies, instructions and verification checklist; unapproved requests fail. |
| 16 | Recovery Verification | Execution; P0 | Record pass/fail/inconclusive against an order with mode, actor, checklist and evidence; incomplete checks cannot become passes. |
| 17 | Impact Analytics | Review; P0 basic, P1 estimates | Count planned, simulated and physical results independently; emissions estimates stay unavailable unless factors, source and assumptions are supplied. |
| 18 | Reports and Audit Trail | Review; P0 basic, P1 formatted reports | Export a JSON report of inputs, rule/solver versions, plan revisions, approval, orders and verification; every mutation has a traceable audit event. |

P1 additions include live AI integration, agent orchestration, sourced environmental models, PDF reports, richer charts and broader hardware support. If AI is unavailable, the entire P0 flow remains usable through manual evidence review and deterministic services. The AI Diagnostics screen still hosts that manual workflow.

## Core flows

1. **Import and assess:** select simulation mode; preview computer/component CSVs; fix errors; commit; inspect base assemblies and individual parts. Import records are synthetic assertions, not diagnostic measurements. Review unknowns and health evidence; deterministic matching lists eligible parts and explains exclusions.
2. **Plan fleet recovery:** set budget and technician minutes; inspect assumptions; solve the whole fleet; inspect final configurations including retained parts, donor losses, costs and work. Baseline comparison uses the same snapshot and constraints.
3. **Stress and approve:** fork the plan into a simulation, fail one chosen donor part and replan. Review before/after differences, accept or reject the exact new revision, then create orders. Rejection creates no reservations. Scenario approval authorizes simulation orders only.
4. **Execute and verify:** follow removal-before-install dependencies; record each step; complete verification. A synthetic fixture produces simulated verification only. Physical mode later requires actual inventory and technician evidence. Failed/inconclusive verification stays unresolved.
5. **Review and export:** inspect plan/approval history, outcomes by mode and audit events; export the report with assumptions and provenance.

## Cross-cutting acceptance and exclusions

- Unknown compatibility or health blocks allocation with a reason. AI text cannot override this rule.
- A donor cannot remain “recovered” after losing a required part unless a compatible replacement is included in its final configuration.
- Plans are immutable snapshots. Approval and order creation revalidate inventory, constraints and reservations; conflicts produce an actionable stale-plan error.
- Core work runs locally for one operator. Public deployment, production access control, simultaneous technicians, purchasing, device agents, automatic hardware diagnostics and motherboard/CPU transfers are outside the first demo.
- Storage ownership and authorization to transfer/wipe data are explicit. A physical order cannot be verified until its data-handling checklist is satisfied; the app will not erase a disk.
- Keyboard access, readable contrast, visible focus, non-color status labels and narrow-screen alternatives are part of UI acceptance.

## Assumptions and decisions still open

Assume institution-owned desktop stock with permitted transfers within one owner, fixed serviceable base assemblies for recovery targets, synthetic cost/time inputs and a single technician-minute pool. Default useful configuration: at least 8 GiB RAM and one storage device of at least 240 GB (decimal), subject to board limits. These are demo policy choices, not universal minimums.

Synthetic CSV rows, toy board profiles and cost/time assumptions are pinned in [fixture v1](FIXTURE_SPEC.md); its original preparation oracle remains separate from the implemented application's solver/lifecycle tests. The AI provider/model, optional impact factors and availability of any real machines remain undecided. The [Figma design](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV) contains **illustrative** counts, component IDs and resource values for layout/prototype purposes; it is not a solver result and has not been reconciled to actual computation. These acceptance criteria define the full product; only the supported subset recorded in IMPLEMENTATION_STATUS has implementation/test evidence.
