# Adaption explanation dataset — 24 October 2026

## User benefit and scope

ReviveGraph's assistant selects authoritative fact IDs from a saved recovery
plan. This increment improves the *reference dataset for that selection task*:
synthetic questions cover blockers, compatibility versus eligibility, uncertain
evidence and safe next actions. Adaption rephrases these questions while their
expected fact selections remain bound to validated source data. Optional examples
help Agent37 map differently worded questions to relevant current-plan facts.

No compatibility rule, allocation, CP-SAT result, technician evidence, health,
approval or physical repair is supplied by Adaption. Displayed explanations still
come from the current plan's canonical facts. No model fine-tuning or AutoScientist
job was requested. There was no live Agent37 call in this task.

The provider's reported dataset score improved in the real run below. Actual
held-out Agent37 answer improvement remains **unmeasured**; provider data scores
are not hardware validation or application selection accuracy.

## Dataset and reproducibility

`datasets/explanation-synthetic-v1/` contains:

- `train.jsonl`: 12 examples, the only examples uploaded.
- `holdout.jsonl`: four example pairs held out from adaptation.
- `manifest.json`: version, explicit synthetic provenance, rule/assistant pins,
  fixture hashes, row counts, file hashes and dataset identity.

Each prompt has a canonical JSON context with
`hardware_configuration_and_blocker`, `compatibility_explanation`,
`evidence_uncertainty` and `recommended_safe_next_action`. Its completion is
`{"fact_ids":[...]}`, matching the existing Agent37 explanation contract.
Source facts include the section explanations; the completion selects references
rather than introducing generated hardware claims.

The builder reuses the unchanged preparation oracle to validate original
inventory, all 11 tiny cases and both documented feasible main allocations.
It uses the unchanged deterministic inspection functions for individual parts.
Handwritten main examples remain feasible preparation evidence, not optimizer
results. All 12 computers appear across the split, plus four collective cases
covering competition, donor failure, greedy allocation and resource boundaries.
The holdout is at example-pair level, not a claim of disjoint hardware knowledge
or broad statistical generalization.

```powershell
.\.venv\Scripts\python.exe scripts/build_explanation_dataset.py --check
```

This checks exact reproducible bytes without rewriting a changed version.
Omit `--check` only when initially generating the versioned files; existing
different bytes are refused. Never edit `synthetic-v1` to fit an adaptation.

## Official SDK and credentials

The optional official Python SDK is pinned separately to `adaption==0.15.0`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-adaption.lock.txt
```

The original core lock is unchanged. The adapter reads `ADAPTION_API_KEY` only
from its process environment. It does not read `.env`, `.env.onsite`, a CLI key
argument or a credential file. Do not paste a key into chat or commit it. A hidden
PowerShell prompt avoids putting the literal key into terminal command history:

```powershell
$adaptionSecret = Read-Host "Adaption API key" -AsSecureString
$env:ADAPTION_API_KEY = [System.Net.NetworkCredential]::new('', $adaptionSecret).Password
Remove-Variable adaptionSecret
```

Remove the environment value after your commands:

```powershell
Remove-Item Env:ADAPTION_API_KEY
```

The client uses the official production API, explicit request deadlines, zero
SDK/HTTP retries and no redirects. Dataset creation and upload completion use
official SDK methods. The intervening signed S3 PUT uses a separate bounded HTTP
client without the API authorization header. Signed URLs and provider exception
bodies are excluded from receipts. Unrecognized storage hosts stop the upload
instead of guessing how a new provider workflow should work.

## Commands and spending boundary

Use a new evidence directory for a new upload. Existing attempts are preserved.
The following names are examples; the actual run directory already exists and
must not be overwritten.

```powershell
.\.venv\Scripts\python.exe scripts/adapt_explanations.py estimate `
  --evidence data/adaption/my-new-estimate --timeout-seconds 180
```

`estimate` uploads only `train.jsonl`, waits for its exact row count and calls
`datasets.adapt(..., estimate=True)`. It returns the saved quote and
`estimate_hash`; it does not launch adaptation. After an ingestion/status timeout,
resume quoting the same uploaded dataset without another upload:

```powershell
.\.venv\Scripts\python.exe scripts/adapt_explanations.py quote `
  --evidence data/adaption/my-new-estimate --timeout-seconds 180
```

Only after an operator approves that exact quote and its estimated-credit limit:

```powershell
.\.venv\Scripts\python.exe scripts/adapt_explanations.py run `
  --evidence data/adaption/my-new-estimate --approve-paid-run `
  --estimate-hash <hash-from-that-estimate> --max-estimated-credits <approved-limit> `
  --timeout-seconds 600
```

This requotes the unchanged recipe immediately before launch and refuses a quote
above the approved threshold. It writes an exclusive launch marker before the
paid call and supplies an official job idempotency key. It permits one launch,
never an automatic resubmission. The recipe caps training rows at 12, disables
language expansion/deduplication/reasoning traces and requests synthetic-only
grounded fact-ID completions. It does not enable web grounding.

**The credit threshold gates the estimate; the API exposes no separate hard
billing-cap field.** Actual consumed credits are left null because the documented
dataset responses did not provide billing usage. The earlier Nodus budget does
not authorize an Adaption run. This task's participant separately authorized one
Adaption run with a refreshed estimate of at most one credit.

On timeout, stop local waiting and keep the run handle. Timeout is not remote
cancellation. Resume only status/download/evaluation collection:

```powershell
.\.venv\Scripts\python.exe scripts/adapt_explanations.py collect `
  --evidence data/adaption/my-new-estimate --timeout-seconds 600
```

No Dataset cancellation endpoint was documented, so none was invented. A launch
with an uncertain response must be inspected at the provider before any new paid
attempt. Local polling uses a total deadline of at most 600 seconds per command,
with each request bounded by the remaining time and at most 30 seconds.

## Download acceptance and optional Agent37 examples

The script downloads JSONL through the SDK streaming interface, at most 512 KiB,
and retrieves dedicated evaluation metrics and the optional summary. It checks
the saved run ID before and after download. The raw output remains quarantined.

Inspect the actual export columns; names below were confirmed in this run and
are explicit arguments rather than assumptions about future versions:

```powershell
.\.venv\Scripts\python.exe scripts/adapt_explanations.py accept `
  --evidence data/adaption/onsite-estimate-20261024 `
  --id-column row_id --prompt-column enhanced_prompt `
  --completion-column enhanced_completion
```

The recorded run has already been accepted, so repeating this command refuses
to overwrite its accepted artifact. Acceptance requires all 12 original training
IDs exactly once, no held-out rows, successful non-degrading numeric provider
scores, exact original canonical fact-ID completions, bounded prompts and no
unrelated hardware IDs. Only one complete surrounding JSON code fence may be
normalized; prose outside it, extra keys and narrative are rejected. Source
contexts remain original and hashed. The provider's `persona_injection` and
other extra columns are discarded.

Actual prompts were 2,388–5,942 characters. The reviewed boundary is 6,000 chars,
at most two reference examples, and 32 KiB serialized UTF-8 including their full
contexts and completions. Nothing is truncated to force acceptance.

Enable only the accepted artifact in the backend process, then restart that
backend using its existing database/startup command:

```powershell
$env:REVIVEGRAPH_ADAPTION_EXAMPLES = (Resolve-Path `
  data/adaption/onsite-estimate-20261024/accepted-examples.json).Path
```

This variable contains a local artifact path, never an API key. Runtime accepts
only versioned JSON beneath `data/adaption`, validates source/artifact hashes,
and selects examples whose expected IDs exist in the current evidence. They are
JSON-quoted untrusted reference examples, not current plan facts or instructions.
The assistant's current-ID output validation remains unchanged. Provider response
evidence records the accepted artifact hash and example count, or an explicit
disabled/rejected fallback status.

Adaption is never called during an explanation. With no configured path, missing
SDK, unavailable Adaption, missing/corrupt/mismatched artifact or no applicable
examples, the original explanation flow continues with zero examples. Local
evidence summaries remain independent of both providers. Runtime examples are
opt-in; the normal application was not restarted or reconfigured in this task.

## Evaluation and actual hackathon evidence

Real dataset ID: `02f181dc-af5e-41f4-8537-439de55fb813`.

Real run ID: `dataset-02f181dc-af5e-41f4-8537-439de55fb813-1792850855309`.

The first upload succeeded but a subsequent ingestion status call timed out.
The saved dataset was requoted without reuploading. Quote: **1 credit**, estimated
11 minutes. The participant explicitly approved one run, estimate at most one
credit. The refreshed quote stayed at one credit and one paid launch succeeded.

Dedicated provider evaluation: **4.0 → 8.6**, **D → B**, reported relative
improvement **115%**, reported percentile after **31.5**. These are Adaption's
dataset quality metrics. Four completion code fences were normalized; all 12
accepted selections still exactly match their original source answers.

Versioned sanitized evidence: `docs/evidence/adaption-20261024.json`. Complete
local receipt, exclusive launch marker, immutable raw JSONL, acceptance artifact
and actual runtime check are under ignored
`data/adaption/onsite-estimate-20261024/`. They contain no API key or signed URL.
Keep that generated evidence separately if restoring from source: it is not
automatically included in a source-only archive.

To score separately obtained held-out predictions without making API calls:

```powershell
.\.venv\Scripts\python.exe scripts/adapt_explanations.py score `
  --predictions <prediction-jsonl-file>
```

Each line must be `{"row_id":"...","fact_ids":[...]}` for one of the four held-out
rows. It reports exact ordered selection accuracy, unsupported-ID rate and
malformed-output rate. Known-but-insufficient selections do not count as correct.
No real before/after held-out Agent37 predictions have been collected.

Relevant checks were run with the Adaption client/transport mocked, including
the installed SDK's actual request serialization; tests spend no credits.
The final combined Adaption/assistant run passed **52 tests**. An additional
isolated actual local solve loaded the real accepted artifact and verified its
Agent37 prompt integration with a mocked AI response: two examples, 16,146 bytes,
current DDR mismatch fact selected, zero physical repairs. The first local check
used incorrect multipart field names; that check driver was corrected before
the passing check. No application import contract was changed to accommodate it.

## Official references checked during implementation

- [Official Python SDK repository](https://github.com/Numi-Labs/adaption-python)
  and installed SDK 0.15.0 define the actual methods and response types.
- [Create/import a dataset](https://docs.adaptionlabs.ai/adaptive-data/create-a-dataset/)
  describes uploading and asynchronous ingestion.
- [Adapt or estimate](https://docs.adaptionlabs.ai/api/python/resources/datasets/methods/adapt/)
  documents `estimate`, recipes, row limits and job idempotency.
  The older `/run` operation is deprecated.
- [SDK quickstart and downloads](https://docs.adaptionlabs.ai/adaptive-data-quickstart/)
  specifies binary/streaming downloads rather than assuming a returned URL.
- [Evaluation response](https://docs.adaptionlabs.ai/api/python/resources/datasets/methods/get_evaluation/)
  defines evaluation status and quality metrics, which can finish after adaptation.
