# Implemented foundation contract — 0.1.0

Status: disclosed pre-event code, 16 October 2026. This is the implemented subset of [ARCHITECTURE.md](ARCHITECTURE.md), covering fixture registration → two-file preview → transactional import → inventory → deterministic inspection. Planning, allocation, scenario overlays, approvals, work orders and repair verification have no implemented endpoints. The independent preparation oracle remains in `scripts/validate_synthetic_fixture.py` and is not imported by the application.

## Runtime and persistence

The frontend uses React/TypeScript/Vite, Tailwind v4, local Inter font files, CVA button variants and a Radix dialog. `components.json`, CSS variables and `@/` aliases provide a shadcn-compatible component foundation. The native Figma inventory, import, dashboard and compatibility frames informed its tokens, typography, spacing and layout; their illustrative values are replaced with backend counts or “Not calculated.” Compatibility currently has a list/table inspector; interactive React Flow graph visualization is deferred.

FastAPI uses Python's `sqlite3`, with foreign keys enabled on every connection and schema `PRAGMA user_version=1`. The normal database is `data/revivegraph.sqlite3`, relative to the project root independently of launch directory. `REVIVEGRAPH_DB` optionally selects another database. Unknown schema versions are refused. No destructive migration or automatic database reset exists. To back up, stop the backend and copy the database to a separate file. Rule/schema upgrades require an explicit migration design; do not delete or rewrite saved inventory to conceal conflicts.

All startup commands bind to `127.0.0.1`. Vite proxies `/api` to FastAPI; no public CORS configuration is needed. `X-Actor-ID` is a supplied local demo label, **not authentication** or verified technician identity. This foundation is intended for a local laptop.

## Immutable fixture registration and pins

`POST /api/v1/fixture-registrations` accepts `{"fixture_id":"revivegraph-synthetic-v1"}` with `X-Actor-ID` and `Idempotency-Key`. It registers the bundled directory only; arbitrary filesystem paths and arbitrary uploaded profile libraries are not accepted. Registration validates the manifest identity, board IDs/versions/types/limits/provenance and nonnegative integer INR-paise/minute operation catalogue. Nullable decisive profile fields are preserved as unknown.

SHA-256 is calculated over the **exact bytes** of all six disclosed fixture files. The aggregate registration hash covers these file hashes plus `inspection_rule_version=desktop-inspection-v1`. Raw-byte hashing makes whitespace/line-ending changes a different registered input. Store immutable manifest, board and cost JSON, file hashes, registration actor/time and engine version. `(fixture_id, fixture_version)` cannot be registered with conflicting content; a global `(profile_id, profile_version)` also cannot acquire a conflicting profile hash. Registration is idempotent for identical content. A changed rule engine cannot silently reinterpret old inventory: the backend refuses inspection/commit against a different pinned version. A new rule version needs an explicit fixture/version migration strategy.

The original CSV hashes support source matching. `scenarios.json` is hashed only as preparation provenance: its handwritten allocations are never loaded into inventory decisions or returned as computed plans. Only `computers.csv` and `components.csv` are downloadable through `/api/v1/bundled-fixture/{filename}`. `GET /fixture-registrations` returns public identity/hash metadata, not scenario allocations.

Each import batch identity is SHA-256 of the registration hash, fleet ID, mode and two exact CSV hashes. Its payload retains the inspection version. Imported computers/components refer to that batch and registration; origin is the immutable initial installed computer or stock, while current location is a separately stored nullable computer foreign key. IDs are globally unique in this foundation so a second fleet import cannot multiply one physical ID. Future simulation scenarios must overlay the same inventory rather than reimport its IDs.

## Evidence schema and CSV v1 clarification

The CSV columns are unchanged. Every computer base assertion and component assertion becomes a separate persisted assessment with these fields:

| Field | Meaning in this foundation |
| --- | --- |
| `subject_type`, `subject_id`, `health` | Exact imported subject and asserted health |
| `assessment_kind` | `authored_synthetic_assertion` or `unreviewed_physical_assertion`; future `human_reviewed_physical_assessment` is reserved for an actual review workflow |
| `provenance`, `evidence_ref` | Original supplied values; base evidence reference remains null because CSV v1 does not supply one |
| `source`, `recorded_value`, `recorded_precision`, `supplied_author_label` | Actual supplied fixture context, inherited only when that CSV's exact hash matches its registered source file |
| `human_reviewed`, `human_reviewer` | False/null for every import; the manifest's synthetic author label does not become a technician approval |
| `imported_at`, `imported_by` | Actual server UTC timestamp to seconds and the supplied importer label, separate from historical assertion metadata |
| `acceptance_scope`, `context_source` | Simulation-only or pending physical review, plus context derivation |

For the unchanged fixture CSVs, each subject receives source `synthetic:fixture-author-assertion`, `recorded_value="2026-10-16"`, `recorded_precision="date"` and the supplied synthetic author label. No midnight timestamp is invented. Modified CSVs retain their supplied provenance/evidence references but receive **unknown recorded date, null source and null author** when the CSV does not hash-match the registered original. Import time does not fill these gaps. There is no general evidence sidecar upload or manual assessment/review mutation endpoint yet; those are explicit later additions, rather than silently extending CSV v1.

Synthetic assertions cannot enter a physical-mode import. Physical-provenance CSV assertions can be stored as pending review, but they remain ineligible in every inspection mode and cannot be counted usable solely from claimed healthy values. Toy synthetic board profiles also fail physical eligibility. No endpoint in this foundation can create a human-reviewed physical assessment.

## Implemented API and import behavior

Paths below have prefix `/api/v1`. Registration, preview and commit require the two mutation headers above.

| Method/path | Actual request/response |
| --- | --- |
| `GET /health` | Process/schema/rule version |
| `POST /fixture-registrations`, `GET /fixture-registrations` | Register/list immutable fixture metadata |
| `GET /bundled-fixture/{computers.csv or components.csv}` | Original CSV bytes for the browser's real multipart upload |
| `POST /imports/preview` | Multipart `registration_id`, `fleet_id` (default `RG-DEMO-12`), `mode`, `computers_file`, `components_file`; returns batch ID/hash, expected revision, normalized records, file hashes, counts and file/row/field errors |
| `GET /imports/{batch_id}` | Retrieve persisted preview/commit status after restart |
| `POST /imports/{batch_id}/commit` | JSON `preview_hash`, `expected_revision`; returns committed batch/revision |
| `GET /state` | Backend counts, fleet revision and optimization status “Not calculated” |
| `GET /computers`, `GET /components` | Inventory/evidence/version pins; optional `fleet_id`, `offset`, `limit` (maximum 1,000) |
| `GET /computers/{id}`, `GET /components/{id}` | Details, source evidence and locations; computer also returns installed parts, profile and derived usability/blockers |
| `GET /compatibility` | Required `target_asset_id`; optional fleet and eligibility `mode` (defaults to persisted fleet mode). Returns hardware decision/reasons separately from health/owner/availability eligibility |
| `POST /compatibility/configuration` | Read-only JSON `target_asset_id`, `ram_component_ids`, `storage_component_id`, `mode`; inspects complete configuration and eligibility without allocating/reserving parts |

The implemented import clarification is that **each installed location must reference a computer in that same uploaded pair**, while a blank location means stock. CSV v1 inserts only; it cannot update existing IDs or add parts into an already imported computer through a later batch. This conservative full-batch rule keeps first-import reference checks explicit. Supporting incremental installed-component intake will require a documented contract extension.

Both files must be UTF-8, exactly the v1 columns in order, nonempty and at most 1 MiB / 1,000 records each. Rows report malformed headers, duplicate IDs, invalid health/booleans/units, missing registered board references, wrong owner, invalid locations and known contradictions in installed layouts. Blank decisive spec fields remain unknown and block compatibility, rather than being defaulted. An under-equipped/faulty computer remains valid inventory input; it is classified with blockers. The 8 GiB/240 GB usefulness threshold is distinct from board hardware compatibility.

Preview persists only batch metadata/report; it creates no fleet, inventory, assessment or audit-import record. A stored preview was chosen over a stateless signed preview because it keeps exact input content and safe restart/replay behavior simple on one laptop. Re-previewing an uncommitted identical batch refreshes its validation/revision. Commit uses `BEGIN IMMEDIATE`, recomputes hashes and validation against the immutable registration/current inventory, checks revisions, then inserts the entire fleet/assessment/computer/component set, audit event and committed-batch revision in **one transaction**. Any failure rolls all of those writes back. An identical already committed batch returns its original revision before stale-revision checks. Reusing a commit idempotency key for different parameters returns 409.

Error bodies contain `error.code`, `error.message`, `error.field_errors` and a request ID; stale/conflict errors return 409 and invalid requests/commits return 422. The browser keeps failed commit inputs and retry key. It offers a new preview when the fleet has changed.

## Deterministic inspection boundary

RAM checks generation, full-size UDIMM form (DDR3 implies 240-pin/1.5 V; DDR4 implies 288-pin/1.2 V within this supported universe), voltage, ECC/buffering, speed and per-slot capacity. Complete sets check module count, slot count, total/minimum capacity and declared mixed-module support. Storage checks 2.5-inch/SATA form, known capacity, port/bay and explicit boot/data/power support. Known incompatibility takes precedence over missing information; otherwise missing decisive information yields unknown. Storage below 240 GB may fit hardware but fails usefulness eligibility.

Hardware compatibility does not certify health, ownership or availability. Those appear as separate eligibility blockers; current installed/stock location does not reserve or allocate the part. Target fixed-base health is checked separately for complete configurations. Initial usability is derived from installed configurations and evidence, yielding the fixture's 0 usable / 8 known unusable / 4 unknown classification. Configuration results cannot overwrite newer frontend selections after a late response.

## Later donor demonstration

`RG-RAM-07` is **not guaranteed to be selected** by the eventual optimizer: stock `RG-RAM-15` avoids donor extraction and is cheaper under the authored operation model. The handwritten before-failure example deliberately uses RAM-07 as a feasible teaching case; it is not evidence that a cost-minimizing solver will choose it. During onsite optimizer integration, choose a failure from an actual computed allocation and inspect available alternatives. Do not force the solver to reproduce Figma or handwritten allocations while claiming an unconstrained optimum.

## Validation evidence and limits

On 16 October 2026, backend tests exercised valid/invalid imports, preview isolation, induced mid-insert rollback, identical/concurrent retries, hash/key conflicts, actual process restart, rule pins, pending physical evidence, DDR/SATA/unknown decisions and complete configurations. The Chromium flow exercised invalid preview → valid preview with zero inventory → commit → asset/component evidence → compatibility → stale response protection → 390 px layout. Screenshots are under `docs/implementation-previews/`.

Frontend typecheck/build, backend dependency consistency and the original fixture preparation validator are separate checks. Exact commands/results are recorded in [PRE_EVENT_WORK.md](../PRE_EVENT_WORK.md). No solver, approval, work-order, verification, AI, physical hardware or performance benchmark result is established by these foundation tests. The interactive graph, manual assessment editing and general fixture/evidence upload remain later work.

Implementation references: the CSV upload uses FastAPI's documented multipart file/form handling ([FastAPI request files](https://fastapi.tiangolo.com/tutorial/request-files/)); Tailwind is integrated through its Vite plugin ([Tailwind Vite installation](https://tailwindcss.com/docs/installation/using-vite)). These references explain library integration; the local test evidence establishes the behavior claimed here.
