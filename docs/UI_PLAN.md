# UI and Figma plan

Status: briefs plus native Figma design and a disclosed application foundation, 16 October 2026. The design/prototype remain unchanged. The application now implements the shared shell, backend-count dashboard, CSV flow, inventory/evidence details and compatibility list/configuration inspection; other main screens show “Not implemented yet.” Every designed example is labeled “Synthetic demo — illustrative data.” Counts, costs, solver labels and verification outcomes in Figma remain illustrative content, not computed or measured results.

## Visual system and shared shell

Professional dark operations workspace: deep navy, restrained emerald for approved/healthy states and cyan for selection/explanation. Typography and tables carry hierarchy; avoid decorative gradients and excessive cards.

| Token | Proposed value / use |
| --- | --- |
| Canvas / surface / raised | `#07111F` / `#0D1B2A` / `#14273A` |
| Border / strong control border | `#2A4055` / `#64748B` |
| Text / secondary | `#F1F5F9` / `#A8B8CC` |
| Accent / focus | emerald `#34D399` / cyan `#22D3EE`; dark text on filled accent buttons |
| Warning / error | amber `#FBBF24` / rose `#FB7185`; always pair with icon and text |
| Type | Inter with system sans fallback; mono for IDs; 28/36 page title, 20/28 section, 14/20 body, 12/16 metadata |
| Space | 4, 8, 12, 16, 24, 32, 48 px; 8 px control radius, 12 px panel radius |
| Controls / motion | Minimum 40 px desktop control, 44 px touch target; 120–180 ms state transitions; respect reduced motion |

Verify actual contrast in Figma and rendered UI (normal text at least 4.5:1; meaningful control boundaries/focus at least 3:1); tokens alone do not establish compliance. Use solid focus rings, labeled inputs, accessible dialogs, keyboard tables, live status announcements and text alternatives to graphs/charts.

Desktop frame 1440×1024: 232 px left navigation, 64 px top bar, 24 px content padding, 12-column grid with 24 px gutters. Top bar shows fleet, mode, snapshot revision and actor. Navigation contains exactly the six main screens. Global “Synthetic demo” or “Physical inventory” banner persists in every detail/export flow; switching modes cannot carry approval across modes.

At 1024 px use compact navigation; at 390 px use a drawer, stacked panels and horizontally scrollable data tables with pinned key columns. Graph has a list alternative. Drawers become full-screen sheets. No hover-only controls. Empty counters use 0 or “Not calculated” according to meaning; loading uses skeletons, not fabricated data. Global stale-data banner links to refresh and explains why approval is unavailable.

Shared components: AppShell, ModeBadge, HealthBadge, EvidenceLink, DataTable, FilterBar, MetricStrip, EmptyState, InlineError, RuleReason, PlanRevisionBadge, CostTimeSummary, ApprovalDialog, WorkOrderDrawer and AuditTimeline. Chart colors never substitute for labels.

## 1. Dashboard

- **Purpose/layout:** fleet overview and next required action; heading and import CTA, compact metrics strip, broad recovery funnel/trend area, recent audit activity and blocker list. No trend chart until multiple real observations exist.
- **Content:** imported computers, eligible parts, planned recoveries, simulated verification passes, physical passes, estimated budget/time. Impact section shows assumptions link and unavailable estimates explicitly. Reports export lives here.
- **Interactions:** click a metric to open a filtered inventory/plan; resume current scenario; inspect latest approval and order drawer; export JSON with current mode and provenance.
- **States:** skeleton metrics while loading; empty fleet offers Import CSV; no plan shows “Not calculated”; report failure retains data and offers retry; stale plan metrics show their revision and cannot masquerade as current.
- **Figma frames:** empty fleet, populated synthetic overview, stale plan and report error; desktop and narrow variants.

## 2. Computer Inventory

- **Purpose/layout:** header with Import CSV, search/filter row, Computers / Components tabs, dense sortable table and selected-item drawer. This screen owns both inventories.
- **Content:** asset/part ID, location, owner, board/specs, health, evidence provenance and blockers. Computer drawer includes fixed base and installed-part slots; component drawer includes origin, current location and reservations.
- **Interactions:** select rows, inspect evidence and compatibility, enter reviewed assessment; CSV dialog follows files → preview/errors → commit confirmation → result. Error rows include file, row, field and correction guidance.
- **States:** table skeleton; empty stock vs no filter matches use different messages; invalid imports never partially commit; duplicate/stale commit errors explain safe retry; unsupported profiles display unknown rather than a green health/compatibility badge.
- **Figma frames:** both tabs, asset drawer, component drawer, import preview with errors and valid commit result. Annotation must distinguish example copy from actual imported evidence.

## 3. AI Diagnostics

- **Purpose/layout:** asset selector and health summary, evidence/log pane on left, suggested interpretation and deterministic eligibility reasons on right; human assessment controls below.
- **Content:** supplied logs with source/time/provenance, unknown fields checklist, accepted human assessment separated from AI suggestions. No invented confidence scores. Provider status stays visible.
- **Interactions:** paste authorized logs, request interpretation if configured, inspect cited source, accept/edit a human assessment with evidence and reviewer; open Compatibility Graph. P1 agent trace is a bounded step list, never an auto-approve button.
- **States:** no selected asset; missing evidence; interpretation pending/cancelled; provider not configured/offline; malformed/uncited output rejected. Manual assessment remains available without AI. Assessment update warns that affected plans become stale.
- **Figma frames:** manual review, optional AI interpretation, provider unavailable and contradictory evidence. Tag AI-assisted frames “P1 — proposed”.

## 4. Compatibility Graph

- **Purpose/layout:** filters and legend above React Flow canvas, selected-edge explanation drawer and collapsible equivalent candidates table.
- **Content:** target computer nodes and component nodes; edges for compatible/incompatible/unknown with textual labels, line styles and reason IDs. Healthy compatibility is distinct from availability/reservation.
- **Interactions:** filter by target, component type and decision; zoom/fit/reset; inspect edge evidence; open candidate list. Highlight proposed allocations separately. Dragging nodes changes layout only; drawing an edge cannot assert compatibility.
- **States:** graph loading; no parts; no compatible candidates with rejection reasons; unknown profile suggests evidence review; network error offers retry and last-snapshot label.
- **Figma frames:** one-target focus, unknown decision drawer, proposed allocation overlay and keyboard-accessible table view. Avoid displaying every rejected edge by default.

## 5. Recovery Optimizer

- **Purpose/layout:** constraints panel on left; result summary and final-configuration table on right; baseline comparison, per-operation details and approval area beneath.
- **Content:** INR budget, technician minutes, recovery policy, snapshot/version; solver status, termination reason/bounds, candidate recovery count, cash/time totals, retained/transferred parts and excluded targets. Baseline and optimizer share identical constraints.
- **Interactions:** validate limits, calculate, inspect operation costing, compare baseline, open simulation, approve/reject revision, create orders, inspect orders and audit. Approval dialog names exact plan/revision/mode, assumptions, resource totals and actor; approval and order creation are distinct actions.
- **States:** before calculation; queued/running; zero-recovery feasible result; feasible-but-not-proven-optimal; optimal; invalid model; no solution found before limit; transport failure; stale plan/reservation conflict. Controls explain why approval is disabled and never call every unsuccessful run “infeasible.”
- **Figma frames:** constraints, result with detailed allocations, non-optimal status, stale approval and approval dialog. Include a human rejection path.

## 6. Live Recovery Simulation

- **Purpose/layout:** persistent simulation banner, event/timeline rail, central fleet/allocation view, before/after comparison panel and bottom action bar. “Live” means live scenario recalculation, not telemetry from hardware.
- **Content:** parent and scenario revisions, selected donor part, failure event, changed destinations, candidate count/cost/time deltas, approval state, orders and simulated verification records.
- **Interactions:** fork scenario; choose actual donor part from the plan; inject failure with reason; recalculate; inspect diff; approve new revision; create simulation orders; advance steps and record simulated pass/fail/inconclusive with synthetic checklist. Reset creates a new scenario instead of erasing the audit history.
- **States:** scenario not started; failure applied awaiting replan; recalculating; no recovery possible; replacement awaiting approval; stale previous approval; failed verification. Double clicks cannot repeat events or orders. After execution starts, failures pause work with a reconciliation message.
- **Figma frames:** initial plan, failure/replan diff, approval, order checklist, simulated verification and interrupted-work state. No “physically repaired” celebration for simulated outcomes.

## Figma production handoff

The target organization was Foundations, Components, Screens and Demo Prototype. Use auto layout, shared variables, named component variants and desktop/narrow frames. Link the click-through from import to simulated verification with realistic *labeled sample* content. Cover loading, empty, error, stale, disabled, focus and success states; success must state its mode. The actual three-page organization and remaining states are recorded below.

Design review gate for later implementation: review actual text/control contrast, keyboard behavior, responsive tables and live error handling in code. The visual renders were inspected, but no application accessibility test has run.

## Native Figma design created on 16 October 2026

- [ReviveGraph Figma file](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV)
- [Clickable synthetic demo prototype](https://www.figma.com/proto/Z3UwUmtqAq7HsMWLeYgcpV/ReviveGraph?node-id=6-66&starting-point-node-id=6%3A66&scaling=scale-down) — starts at import preview. Native click reactions and starting point were read back in Figma; a browser presentation run has not been separately tested.

The Starter plan allowed **three pages**, not the requested four. The file has `Foundations`, `Components` and `Screens`; `Demo Prototype` is a named **section on Screens**. The account did permit editable Design frames, variables, components and prototype connections. The page limitation is a file-organization constraint, not a raster/code substitute.

| Screen / state | Figma frame |
| --- | --- |
| Dashboard desktop | [Dashboard](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=4-2) |
| Computer Inventory desktop, with Components tab and CSV entry | [Computer Inventory](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=5-29) |
| AI Diagnostics desktop, with manual evidence review | [AI Diagnostics](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=5-191) |
| Compatibility Graph desktop, with rule-reason list | [Compatibility Graph](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=5-281) |
| Recovery Optimizer desktop | [Recovery Optimizer](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=4-246) |
| Live Recovery Simulation desktop | [Live Recovery Simulation](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=5-391) |
| Representative narrow layouts | [Inventory 390 px](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=7-520) · [Simulation 390 px](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=7-558) |
| Prototype start and key states | [Import preview](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-66) · [Import error](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=7-204) · [Calculation](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-590) · [Before/after](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-978) · [Stale approval](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-1080) · [Human decision](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-1223) · [Work orders](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-1509) · [Simulated result](https://www.figma.com/design/Z3UwUmtqAq7HsMWLeYgcpV?node-id=6-1611) |

The prototype has fourteen editable frames and a connected main route: import preview → Components inventory → evidence review → compatibility → calculation → R1 plan → donor failure → R2 before/after comparison → stale R1 guardrail → human approval of R2 → simulated orders → simulated verification. Import error and human rejection branch to separate frames. The stale approval action is disabled and has no click reaction. Rejection creates no order in the illustrative story.

Foundations contains 19 shared color/spacing/radius variables, five typography styles, a swatch/type specimen and a mapping of all 18 planned capabilities into the six navigation screens. Components contains native button, nav and status variants plus a metric component. Screen and prototype frames use auto layout and component instances. A structural read-back found no image-filled complete-UI captures; rendered screenshots were inspected for the six desktop views and the two narrow layouts. [Dashboard preview](design-previews/dashboard.png), [Optimizer preview](design-previews/recovery-optimizer.png), [Inventory mobile preview](design-previews/inventory-mobile.png), [Simulation mobile preview](design-previews/simulation-mobile.png).

The six primary layouts and essential demo states are present. Planned secondary variants from the briefs that remain undesigned include the Dashboard empty/report-error states, AI provider outage, every solver failure status, complete narrow layouts for the other four screens and interrupted physical work. No real diagnostic evidence, solver result, environmental estimate or physical verification is represented.

## Application foundation handoff — 16 October 2026

The Figma design-to-code workflow read high-fidelity context and screenshots for Dashboard (`4:2`), Inventory (`5:29`), Import preview (`6:66`) and Compatibility (`5:281`). The implemented shell preserves the 232 px navigation, deep navy tokens, local Inter typography, emerald primary actions and cyan inspection states. Real backend counts replace Figma's sample values. The native design was not edited.

The current app has a working import dialog, Computers/Components tabs, source/evidence details and deterministic compatibility table plus complete-configuration inspector. It provides loading, empty, error, invalid-preview and pending-evidence states. Dashboard uses backend inventory counts; all optimization metrics are “Not calculated.” Diagnostics, optimizer and simulation are clearly unimplemented. Interactive React Flow graph rendering, manual assessment editing and the other product workflows remain later work.

Actual renders: [Inventory desktop](implementation-previews/inventory-desktop.png), [compatibility desktop](implementation-previews/compatibility-desktop.png), [Inventory 390 px](implementation-previews/inventory-mobile.png). A Chromium flow exercised the app and desktop/mobile renders were inspected; this does not constitute a full keyboard/contrast/accessibility audit.

## Record — 20 October 2026: implemented recovery interface

The existing native Figma file and prototype remain unchanged. The Figma design-to-code workflow read high-fidelity context and screenshots for Optimizer `4:246`, Simulation `5:391` and Compatibility `5:281`; their navy surfaces, emerald/cyan accents, typography and spacing informed the existing component/token system. The application now connects these workflows to computed backend responses instead of illustrative Figma numbers.

Implemented UI states include calculation/loading/error, persisted plan selection, named independent rehearsal contexts, actual allocation and operation ledger, solver proof/baseline, before/after failure comparison, stale/paused plans, exact-revision approval/rejection, cross-order step dependencies, authored simulation evidence/checklists, verification and JSON export. Compatibility adds a focused interactive React Flow graph sourced from real inspection decisions and retaining its complete table/reason alternative. Diagnostic evidence review remains separate from the unconfigured AI service; accepted-health editing is not implemented.

Actual application evidence is saved in `docs/implementation-previews/optimizer-computed-desktop.png`, `simulation-verified-desktop.png`, `simulation-verified-mobile.png` and `simulation-verification-checklist.png`. The original Figma design previews remain design examples. Figma's “4 recoverable”, ₹11,200/310 min and ₹12,400/345 min and RAM-07/RAM-11 revision examples still require an explicitly labeled future design reconciliation; they were not changed or served as solver results. The computed main flow uses 7 candidates at ₹2,150/299 min and donor SSD-10→SSD-11 instead.

Browser validation covers desktop and 390 px, graph selection/controls, stale revision and acknowledgement reset, approval, steps and simulated verification/report export. Formal contrast/accessibility review, real hardware and production authentication remain outside these checks.

## Record — 20 October 2026: primary screenshot reference

The participant supplied `ChatGPT Image Oct 20, 2026, 09_50_41 PM.png` and requested direct frontend implementation. It is the primary visual reference for the current operations-console redesign; the native Figma file is preserved and was not edited. The reference's near-black/navy layout, icon sidebar, blue active navigation, compact header, five metrics, subtle 1px borders, 6px cards and split-column hierarchy now carry through Dashboard, Inventory, Compatibility, Optimizer, Simulation and Reports.

Reference content was adapted: assets become actual computers/components, health becomes backend usability, alerts use actual missing/faulty/unknown records, predictive analytics becomes a discrete actual solver/greedy/parent comparison, workflow nodes show persisted approval/removal/install/verification, and activity reads the real fleet-scoped audit feed. No industrial metrics, fictional history, diagnostic health scores, fake AI capability or environmental savings were copied. Synthetic/loading/empty/error/stale states remain explicit.

Rendered desktop and 390 px screens were inspected against the supplied image. Corrections removed excess card stretching and animation ambiguity, increased small workflow labels, placed the sidebar collapse beside the brand and compacted actual activity rows. Evidence is saved in `implementation-previews/reference-dashboard-desktop.png`, `reference-dashboard-mobile.png` and `reference-{inventory,compatibility,optimizer,simulation,reports}-{desktop,mobile}.png`. The full three-flow browser suite, typecheck/build and nineteen focused backend tests passed. This is implemented application evidence, not a native Figma revision or a formal accessibility audit.


## Workflow-first application refinement - 21 October 2026

The running application adds one state-aware next action and compact five-stage journey above the dashboard metrics, retaining the screenshot-led navy/blue/emerald language. The import shortcut prepares a real preview only. Optimizer/Simulation show resource headroom and changed-only before/after allocations, including genuine zero deltas. After work orders exist, the execution queue leads the result column and the 390 px layout; additional failure controls are secondary. Named dependency navigation, ready-task focus, filters/search and persisted read-only checklist evidence reduce manual scanning. Synthetic evidence is not marked verified merely because it is available.

Actual inspected previews: `implementation-previews/effective-dashboard-{desktop,mobile}.png`, `effective-simulation-{desktop,mobile}.png` and `effective-allocation-changes.png`. Native Figma remains unchanged. The values shown come from isolated actual backend/browser actions against synthetic-v1, not physical measurements or a Figma sample.
