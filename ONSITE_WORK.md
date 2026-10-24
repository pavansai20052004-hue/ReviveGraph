# Onsite work — ReviveGraph

## 24 October 2026 — Nodus CPU execution increment

The participant stated that the official onsite build had started and explicitly resumed development. The disclosed starting application is preserved at commit `8232884a0115e1626ec03991caf6c815ae177486`, tag `pre-event-final-rehearsal-2026-10-22`. Existing optimization, pre-work failure replanning, approval, work orders, simulated verification and audit export are pre-event features, not new onsite claims.

This increment adds a versioned CPU request/result protocol, an allowlisted remote worker reusing the existing solver, an opt-in Nodus Jobs adapter with a US$0.10 cap and timeout, remote download validation, sanitized attempt receipts, provider selection/labels, focused tests and an isolated first-run command. The participant approved up to US$0.10 of event credits for the initial calculation. It does not add physical repairs, change synthetic assessments, redesign the interface, implement AI explanations or add Render Workflows.

Actual validation, using isolated temporary databases and no normal inventory changes:

- `python -m pytest backend/tests/test_nodus.py backend/tests/test_recovery.py::test_failure_crash_retry_does_not_duplicate_overlay_or_plan backend/tests/test_recovery.py::test_change_during_solve_refuses_persistence -q`: **18 passed** for the initial adapter plus three existing lifecycle regressions, 42.21 s.
- After adding API persistence/audit/provider-inheritance coverage, `python -m pytest backend/tests/test_nodus.py -q`: **16 passed**, 27.91 s. Fake SDK handles are explicitly named `fake-test-job-never-a-remote-run`; these are transport tests, not cloud evidence.
- After adding strict integer representation rejection, the targeted untrusted-output cases: **11 passed**, 17.30 s. Corrupted protocol/input/source/output hashes, duplicate physical-part use, changed totals/ledger/baseline, unsupported status/version and float-for-integer substitutions are rejected.
- Targeted receipt/timeout tests after the status collection corrections: **2 passed**, 2.83 s. Timeout requests cancellation, preserves safe logs/cost/usage and produces no local fallback. Repeated paid request identity is blocked.
- Sanitization regression after adding JSON-token and known-environment-key redaction: **1 passed**, 0.92 s.
- `npm --prefix frontend run typecheck`: passed. `npm --prefix frontend run build`: passed, Vite build 3.68 s.
- `npx playwright test e2e/nodus.spec.ts --config playwright.reference.config.ts` from frontend: **1 passed**, 47.3 s. Actual browser import, explicit provider selection, disabled-remote error with no plan write, local calculation and persisted provider label worked; 390 px document overflow check passed. No cloud submission was made by this test.
- `python -m pip check`: no broken requirements. Optional `nodus-compute==1.0.27` and its additions are separately locked; the installed bundled CLI reports `nodus 0.1.45`. No original lockfile or solver version was changed.

One reviewer inspected the trust, paid-attempt and local regression boundaries. Its findings were corrected: dynamic local solver lookup preserves existing interruption/race checks, failed jobs collect evidence best-effort, and safe status fields match the installed SDK (`startTime`, `completionTime`, `cost`, `unitMetrics`). The 360-second timeout applies to waiting, not source upload/create, HTTP retries or evidence collection. A first Windows native-library import stalled and those test-owned processes were stopped; a fresh traced import and subsequent test/backend processes succeeded without modifying OR-Tools. The SDK download was interrupted once and pip resumed it successfully. Existing Starlette/httpx deprecation and test-runner color warnings remain; no error was suppressed.

The actual CLI preflight returned **not logged in**. At the participant's request, Codex started the official interactive `nodus login` command so the participant can authorize its browser page. The participant's sign-in and event-credit availability are still pending at this record update. **No remote Job, remote allocation, actual cloud usage or success is claimed yet.** No test approval, work order or simulated verification was created by the first-run script. Historical pre-event records are retained without backdating.

Account blocker update, 24 October: the participant reports the authorization page asks to verify a card and continue. Official Nodus billing documentation checked in response states that card setup itself does not charge or enable auto-recharge, but new work requires a verified payment method even with promotional credits. The separate credits guide says uploaded sources, saved outputs, archived logs and direct storage downloads also require payment or support review for trial accounts; the exact event organization's entitlements are not yet verified. Card details and any bank authorization remain the participant's own account action. No card was entered, payment/top-up authorized, auto-recharge enabled or remote job submitted by Codex. An event representative or Nodus support may need to confirm the account's activation and source/output entitlement before the first real run. References: https://nodus-compute.ai/docs/guides/billing/add-a-card/ and https://nodus-compute.ai/docs/guides/billing/credits/.

## 24 October 2026 — grounded assistant and workflow integration

While Nodus activation was blocked, the participant authorized continuing the
integrated project and confirmed Agent37 and Render account availability. New
implementation in this increment:

- `assistant.py`, `settings.py`, placeholder-only `.env.example` and an ignored
  `.env.onsite`: explicit local evidence summaries and opt-in Agent37 fact
  selection tied to actual saved plan/asset hashes. Authoritative text, health,
  hardware rules and numbers come from deterministic source facts. Invalid
  provider answers are rejected; uncertain attempts cannot automatically retry
  with the same identity. Selected facts, actor labels, provider IDs and actual
  supplied usage append to the audit and survive restart.
- Diagnostics now displays the assistant alongside original assessment evidence,
  with plan selection, questions, loading/errors, disabled/unconfigured provider
  state, source details and restored saved answers. Local summaries are explicitly
  labelled as making no AI request. Native Figma and existing design were kept.
- `workflow.py` performs input validation, CPU execution, independent result
  validation and calculation audit generation. It is now the default local
  calculation path. `workflow_render.py` optionally triggers a deployed Render
  workflow and revalidates the downloaded full stage envelope before persistence.
  The existing recovery lifecycle still owns snapshot/reservation checks and
  saving. No schema migration, fixture change or oracle replacement was needed.
- The API and Optimizer UI distinguish orchestration (`local`/`render`) from CPU
  execution (`local`/`nodus`). Both default to local. Failure replanning inherits
  both from the parent. UI exposes actual stage/hash evidence; old plans do not
  receive invented workflow traces.
- Actual Render SDK 1.4.0 task source registers a root and four child stages with
  zero retries. HTTP submission also has zero retries and a bounded timeout.
  Optional dependencies are separately locked. A concrete, unapplied Blueprint
  and deployment recipe were prepared in `workflows/`; automatic deployment is
  off and Nodus starts disabled. No push, deployment or hosted run occurred.
- Existing Nodus safe logs are now forwarded as a bounded sanitized excerpt/hash
  through the workflow and retained by the caller, preserving evidence beyond an
  ephemeral worker disk. Missing Render usage remains null; Render platform log
  retrieval and billing collection remain unimplemented.

Independent review identified and corrected three assistant consistency issues:
answers from a previous asset could remain visible after switching computers;
scenario-failed parts could show eligible=true in structured evidence; and plan
status could change during a provider call. Answers are now scoped to asset/plan,
late responses cannot populate another view, scenario eligibility is explicitly
excluded and changed-status replies are rejected. Malformed provider URLs/output
and unsupported fact claims are rejected. Initial tests also accidentally patched
the TestClient's inherited HTTP method; the test double was corrected so real app
routes run and only provider traffic is mocked.

Executed checks, all using temporary/isolated synthetic inventory:

| Actual command/check | Actual result |
| --- | --- |
| `python -m pytest backend/tests/test_workflows.py backend/tests/test_nodus.py -q` after log forwarding | **50 passed**, 22.72 s: 33 workflow/API cases and 17 Nodus cases. Actual Render SDK registration, in-process task functions and mocked HTTP serialization/parsing checked; no cloud call. |
| `python -m pytest backend/tests/test_assistant.py -q` after failed-part/status corrections | **18 passed**, 9.92 s. |
| Assistant file plus Nodus API/provider-inheritance and existing crash/race cases | **22 passed**, 26.85 s, after wiring execution/orchestration. |
| `test_unconfigured_agent_does_not_create_attempt` after adding explicit instance-review gate | **2 passed**, 3.28 s; disabled or unreviewed provider makes no attempt. |
| `test_local_facts_replay_evidence_and_restart` after explicit unknown-health exclusion assertion | **1 passed**, 2.49 s. |
| `npx playwright test e2e/assistant.spec.ts --config playwright.reference.config.ts` | **1 passed**, 11.2 s: actual import/calculate/local-summary/audit restoration, delayed response while switching assets and desktop/390 px overflow/screenshots. No AI call or human approval. |
| `npx playwright test e2e/nodus.spec.ts --config playwright.reference.config.ts` after Render selector wiring | **1 passed**, 10.9 s: disabled Render and Nodus produce actionable errors/no plan; local solve persists four-stage trace; 390 px layout check passes. |
| `npm --prefix frontend run typecheck` | Passed. |
| `npm --prefix frontend run build` | Passed; Vite production build 848 ms. |
| `python -m pip check` | No broken requirements found. |
| `git -c core.whitespace=cr-at-eol diff --check` | Passed. |
| Prepared Blueprint parse/intent fields | Passed locally; official CLI/API schema validation and Linux build remain unverified. |

Existing FastAPI/Starlette httpx deprecation and test-runner color warnings remain.
Only relevant changed-path checks were run, not the entire prior passing suite.
Automated actors/evidence in tests are test-authored; they do not represent the
participant personally entering a decision. These new browser checks make no
approval, complete no work and record no verification. Physical repair count is
zero. Fixture and preparation oracle changes were checked absent in Git.

Two local preview processes were started on 18274/15274 using a new, empty ignored
`data/onsite-preview-20261024.sqlite3`. Health, integrations and state returned 200;
state is revision 0 with no computers/plans/orders/passes. Provider configuration
returned false/disabled. The normal database, old manual rehearsal and all
previous tags/archives/receipts were not changed. Browser-test screenshots are
generated evidence under ignored `data/onsite-assistant-desktop.png` and
`data/onsite-assistant-mobile.png`.

Agent37 browser setup initially hit a Vercel checkpoint and later reached its
sign-in screen. The participant reports that instance creation asks for a card
and advertises $5 free. No instance, card entry, top-up, budget change or paid AI
request was made by Codex. A dedicated instance/profile must be reviewed before
enabling it. Agent37's chat API is agentic by default; the prompt cannot enforce
tools-off on the remote instance. ReviveGraph exposes no local mutation tools or
credentials to it. Hard provider-side isolation and live response/usage remain
unverified. Nodus activation is also pending. Render still needs reviewed source,
deployment/spending authorization, successful build and its actual task slug.

The integration is **partial pending live-provider gates**, not a completed
three-provider cloud demo. The read-only specialist review found no additional
blocking workflow trust defect; stage integrity does not establish remote
attestation or locally prove optimality. Post-start reconciliation, renewed
approval and safe resume remain unimplemented and preserved as a separate onsite
slice. Physical diagnosis/repairs, authenticated production use, broader AI log
interpretation and environmental estimation remain incomplete. Fetch overlap and
exact hours remain unresolved. All 18 capabilities stay specified.


Final targeted follow-up: rendered inspection found that the first mobile PNG
captured an in-flight existing sidebar/margin resize transition. The browser
check now waits for the actual sidebar/main geometry to settle before capture;
it passed again (1 test, 10.9 s) and the 390 px PNG was visually inspected with
unobscured content. No mobile application layout change was needed. CPU wording
was clarified so a local solver inside hosted Render is labelled Render worker
CPU, distinct from laptop CPU and Nodus CPU. The related local-facts check passed
again (1 test, 2.51 s); the final production build/typecheck passed, Vite 666 ms.
This follow-up did not make a provider call or change allocation behavior.

## 24 October 2026 — time-boxed Adaption explanation dataset integration

The participant requested a strict 60-minute integration. Work started at
13:32:44 UTC (19:02:44 IST), with a deadline of 14:32:44 UTC (20:02:44 IST).
The disclosed existing uncommitted Nodus/Agent37/Render work was preserved.
No pre-event work was backdated. New source is limited to dataset preparation,
the optional SDK script/reference loader, tests, documentation and the small
Agent37 reference-example hook. No frontend redesign or core recovery feature
was added.

Actual additions:

- `datasets/explanation-synthetic-v1/train.jsonl`, `holdout.jsonl` and manifest:
  16 explicitly synthetic pairs, 12 for adaptation and four example pairs held
  out. Source rows cover the 12 machines plus competition, donor failure, greedy
  allocation and resource boundaries. Four explanatory sections live in the
  canonical context; completions select exact canonical fact IDs, matching the
  existing assistant. The generator rechecks all source fixture/scenario
  assumptions through the unchanged preparation oracle and inspection rules.
- `scripts/build_explanation_dataset.py`: deterministic generation and byte
  reproducibility check; changed versioned dataset bytes are not overwritten.
- `scripts/adapt_explanations.py` plus optional Adaption SDK 0.15.0 lock:
  environment-only key access, official SDK upload/create/complete, estimate-first
  workflow, explicit paid approval/hash/estimated-credit threshold, one launch
  marker and idempotency key, no automatic retries, bounded polling/streaming
  download, run-ID checks before/after export and separately retrieved evaluation.
  Local `quote` and `collect` resume saved state without uploading/launching again.
- `explanation_examples.py` and a narrow Agent37 hook: only a fully accepted
  artifact can provide reference examples. Exact source completions/context/hashes,
  all training IDs once, no held-out IDs, non-degrading provider numeric scores,
  prompt bounds, current-evidence IDs and a 32 KiB request budget are enforced.
  At most two JSON-quoted synthetic examples are used. Generated prose never
  becomes displayed evidence; current-plan canonical fact rendering is unchanged.
  Missing/invalid/unconfigured data yields zero examples without an Adaption call.
- Setup/limitations and sanitized reproducible evidence in
  `docs/ADAPTION_INTEGRATION.md` and `docs/evidence/adaption-20261024.json`.

The participant initially had no API key in this session's environment, then
supplied a key and explicitly authorized its use. It was placed only in temporary
command-process environments for the requested provider calls and removed in
their cleanup. No key was written to project credential files, source, datasets
or receipts. A hidden local key-entry method is documented for future use.

Actual external work: one synthetic training dataset was created/uploaded, ID
`02f181dc-af5e-41f4-8537-439de55fb813`. The four held-out examples stayed local.
An ingestion/status API request timed out after successful upload. The same
dataset was resumed/requoted without a second upload. Its real quote was one
credit, estimated 11 minutes. The participant explicitly approved one run with a
refreshed estimate of at most one credit. The immediate prelaunch quote remained
one credit. Exactly one paid adaptation launch was submitted, run ID
`dataset-02f181dc-af5e-41f4-8537-439de55fb813-1792850855309`; it succeeded.

The SDK/API supplies an estimate and row limit, not a hard billing-cap field.
Actual billed credits were not returned and remain null. No additional paid
adaptation, AutoScientist training, live Agent37 request or provider cancellation
was submitted. Read-only collection was repeated to verify the same run identity
after download; this is not another adaptation run.

The 175,908-byte raw JSONL download contains 12 rows and is retained unchanged
with its hash. Adaption reported quality scores 4.0→8.6, grades D→B, relative
improvement 115% and percentile-after 31.5. These are provider dataset metrics,
not held-out assistant improvement, solver uplift, physical diagnosis or repairs.
The accepted artifact contains all 12 rows. Four completions had a single entire
JSON code fence removed before exact canonical comparison. Actual prompt lengths
were 2,388–5,942 characters; the original conservative 2,000-character draft
limit was replaced by a reviewed 6,000-character bound plus a two-example/32 KiB
total request budget. No text/context is truncated. The extra provider persona
column is discarded. Narrative, prose around fences, nested fences and changed
fact selections remain rejected; no compatibility rule was loosened.

Actual checks:

- Initial mocked Adaption checks: 19 passed. Expanded Adaption + existing
  assistant checks: 45 passed, 86.20 s. After the reviewed format/boundary and
  concurrent-run export checks, the final combined command
  `python -m pytest backend/tests/test_adaption.py backend/tests/test_assistant.py -q`
  passed **52 tests**, 9.13 s, with the existing FastAPI/httpx deprecation warning.
  Tests mock provider clients/HTTP, including real SDK serialization; no test
  spends credits.
- `python scripts/build_explanation_dataset.py --check`: passed, all 16 rows and
  original scenario checks reproduce exactly.
- `python -m pip check`: no broken requirements; the original core lock is
  unchanged and only Adaption/distro/sniffio add-on pins were installed.
- A separate isolated actual import/local solve loaded the real accepted
  artifact and passed it through the Agent37 prompt layer with mocked HTTP.
  It selected two examples totaling 16,146 bytes and returned current DDR3/DDR4
  mismatch/boundary IDs. This is an automated check, not a live AI call or human
  approval. Local solve still reported OPTIMAL, 7 candidates, 215,000 paise,
  299 minutes; physical repairs remained zero. Its first check driver used wrong
  multipart field names and was corrected before passing; the app contract was
  not changed.
- Ten protected files (six original fixture files, deterministic rules,
  optimizer, recovery lifecycle and preparation oracle) matched their pre-task
  SHA-256 values. A live-key-pattern scan of the checked new source/evidence
  found none. Git whitespace check passed. The normal database was not opened
  by these preparation checks; temporary databases were used and cleaned up.

The raw receipt/launch/download/accepted/runtime-check files are under ignored
`data/adaption/onsite-estimate-20261024/`; versioned sanitized metadata is in
`docs/evidence/adaption-20261024.json`. Optional runtime examples were not enabled
in the normal running application. The current application works without
Adaption. Held-out Agent37 before/after predictions and actual billing remain
unmeasured/unavailable, respectively. Physical repairs remain zero. All earlier
Figma work, archives, tags, fixture bytes and historical records are preserved.
