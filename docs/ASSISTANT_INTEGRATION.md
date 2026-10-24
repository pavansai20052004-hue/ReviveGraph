# Grounded assistant — onsite increment, 24 October 2026

The Diagnostics screen preserves imported assessment inspection and now adds a
read-only plan assistant. This is separate from accepted assessments and human
decisions. It does not diagnose hardware or change the synthetic fixture.

## Implemented boundary

`GET /api/v1/plans/{id}/assistant-context?asset_id=RG-PC-06` reads the pinned
snapshot, checks its hashes and independently validates the saved allocations
and operation ledger. It builds source-addressable facts for allocations,
initial blockers, hardware versus eligibility inspection, resource limits,
greedy comparison, scenario failure changes and feasible single-RAM substitutions.
An alternative holds all other assignments fixed and passes the same fleet
validator; it is not a newly optimized result. Failed scenario parts are excluded
even when their physical imported health remains healthy.

`POST /api/v1/plans/{id}/assistant` accepts `question`, `provider` (`facts` or
`agent37`) and optional `asset_id`, using the existing actor/idempotency headers.
The explicit local summary makes no AI request. Agent37 receives actual synthetic
facts and selects up to six known fact IDs. It cannot introduce new displayed
numbers, health assertions or hardware rules: the application renders the
selected source text. Unsupported IDs, extra response fields, failed turns and
invalid JSON are rejected. This bounded selection is the first AI integration;
free-form log diagnosis and an autonomous mutating agent remain unimplemented.

Answers record provider, exact plan hashes, selected asset, source facts,
operator label, actual response time, and provider-supplied response/session IDs,
model and allowlisted usage where present. Missing usage stays null. An audit
event persists the answer and is included in the existing report. Restart and
browser reload restore recorded evidence, filtered to its original plan/asset.
If plan status changes during a call, the response is rejected. No assessment,
reservation, approval, work order, verification or physical inventory is modified.
Recording an explanation is itself an audit write; “read-only” describes its
authority over the recovery decisions, not absence of all database writes.

## Account setup and actual validation boundary

Copy `.env.example` to the ignored `.env.onsite`, preserving an existing file.
Supply `AGENT37_API_KEY`, `AGENT37_INSTANCE_URL` and optionally
`AGENT37_PROFILE` locally. Never paste credentials into chat or commit them.
The instance URL must be an HTTPS root on a single `*.agent37.app` subdomain;
arbitrary hosts, credentials, ports, paths and redirects are rejected. Only
explicit `REVIVEGRAPH_AGENT37_ENABLED=1` enables calls. Configuration status
does not establish a successful live connection.

`REVIVEGRAPH_AGENT37_INSTANCE_REVIEWED=1` is also required after the operator
reviews the dedicated instance/profile boundary described below. It is an
explicit operator acknowledgement, not an automated provider-security audit.

Find an existing Hermes instance on the [Agent37 cloud dashboard](https://www.agent37.com/dashboard/cloud).
The [Agent API quickstart](https://www.agent37.com/docs/agents-api/agent-quickstart.md)
and [chat contract](https://www.agent37.com/docs/agents-api/chat.md) describe
`POST https://{instance}.agent37.app/v1/responses` with `X-Agent37-Key`.
Non-streaming requests can still return HTTP 200 with a failed status, which
this adapter rejects. The call timeout is 210 seconds; it does not prove the
remote turn was cancelled. An in-progress/failed attempt is durably retained
before contacting Agent37, so reusing its key cannot incur an automatic second
request. Inspect an uncertain turn on the provider before deliberately starting
another. The browser preserves the key within its session as well.

**Provider-side limitation:** `mode=chat` is a single agent turn, not a tools-off
setting. The prompt requests no external tools, but cannot enforce the instance's
capabilities. Before live use, select a dedicated instance/profile without
connected services, sensitive files or application credentials; review and disable
unneeded tools through supported provider controls. ReviveGraph supplies no local
mutation tools or credentials to the agent. Hard provider-side tool restriction
has not been verified. A generic connected personal assistant instance is not
appropriate for this adapter.

Account availability was confirmed by the participant. Instance identification,
credentials, profile review, spending authorization and a real request remain
pending. Chrome navigation initially encountered a Vercel Security Checkpoint
and browser inspection timed out, then reached the sign-in screen. The participant
subsequently reported that creating an instance requires adding a card and shows
a $5 offer. Those UI terms were participant-reported; no no-charge guarantee or
event-credit activation is inferred from them.
No instance was created, budget changed or paid AI call made by Codex.
Provider and transport tests use explicit fake IDs and do not establish live
Agent37 compatibility or actual usage. See `ONSITE_WORK.md` for executed checks.

The [provider budgets guide](https://www.agent37.com/docs/agents-api/budgets.md)
distinguishes managed-service budgets from instance compute/storage charges.
A real request needs an agreed spending bound and reviewed account settings;
this adapter does not claim its HTTP timeout is a monetary cap.

## Optional Adaption examples — 24 October 2026

The Agent37 request can now include up to two accepted synthetic reference
examples from an explicitly configured local Adaption artifact. These remain
JSON-quoted untrusted examples, separate from current-plan evidence. The final
known-ID selection check and canonical fact rendering are unchanged. The local
summary never calls Adaption or needs its SDK. Provider response/audit evidence
records the artifact hash and selected count or a disabled/rejected fallback.
This does not activate a live Agent37 connection or authorize another AI call.
See ADAPTION_INTEGRATION.md for the exact opt-in, real dataset run, acceptance
normalization, request byte budget, provider quality metrics and limitations.
