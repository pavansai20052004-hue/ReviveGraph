# Travel freeze and manual synthetic rehearsal

Preparation date: **21 October 2026**. Feature development is frozen. This runbook and the new local checkpoint disclose all existing implementation as pre-event work. No result here certifies physical hardware.

## Separate rehearsal environment

- Normal app: `http://127.0.0.1:5173`, backend 8000, database `data/revivegraph.sqlite3`. Do not use it for this rehearsal.
- Manual synthetic rehearsal: **http://127.0.0.1:15174/#dashboard**, backend 18080, database `backups/travel-readiness-20261021T051413834938Z/manual-synthetic-rehearsal.sqlite3`.
- A consistent SQLite backup of the original normal database is in that same directory as `normal-database-snapshot.sqlite3`; `normal-after-preview-preserved.sqlite3` separately preserves its later preview metadata. It is a local data backup, excluded from source control and the source ZIP.
- The rehearsal starts empty. Startup smoke checks have not imported inventory, approved a plan or completed work. Manual rehearsal is **in progress**, not passed. The participant confirmed a valid uncommitted preview. A preservation check found that the first preview reached the normal instance; a second snapshot preserves that state. No inventory had been imported there at that check. The isolated instance subsequently received its own preview. The participant subsequently confirmed :15174, imported 12/31 there and inspected unknown RG-PC-04 evidence with no technician review. Backend revision 1 corroborates 0 usable / 8 unusable / 4 uncertain; normal inventory remains empty. Compatibility/calculation and later manual steps are still pending.

The current rehearsal services were launched with preparation-only external connection guards. Their scripts and receipts are in the ignored travel directory. They are not application changes or an OS network sandbox. If these temporary processes stop, restart an isolated rehearsal from the project root in two PowerShell terminals:

```powershell
$env:REVIVEGRAPH_DB = Join-Path $PWD 'backups/travel-readiness-20261021T051413834938Z/manual-synthetic-rehearsal.sqlite3'
.\.venv\Scripts\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 18080
```

```powershell
$env:REVIVEGRAPH_API_TARGET = 'http://127.0.0.1:18080'
npm --offline --prefix frontend run dev -- --port 15174 --strictPort
```

These variables apply to those terminals only. Do not run `setup.ps1`, `npm ci`, dependency upgrades or a reset before the rehearsal. Leave the installed `.venv` and `frontend/node_modules` on this laptop. If the ports are occupied, inspect the existing processes rather than stopping unrelated services. The UI's generic backend connection error mentions port 8000; this isolated rehearsal intentionally uses 18080.

## One manual rehearsal

Use the disclosure: **“Synthetic demo — illustrative data. All execution and verification outcomes are simulated; no physical repairs have been performed.”** The local operator label is not authenticated technician identity.

1. **Preview before import.** Choose Start synthetic import → Prepare demo preview. Confirm Validation passed, 12 computers and 31 component IDs. Before committing, the underlying fleet must still be empty. Report any field errors instead of bypassing validation.
2. **Import explicitly.** Choose Commit batch → View imported inventory. Confirm 12 computers / 31 components and initial classification 0 usable, 8 unusable, 4 uncertain. These are authored assertions, not diagnostic measurements.
3. **Inspect evidence.** Open RG-PC-04 and its assessment evidence; RG-RAM-04 has unknown health. Show that no technician review is recorded. In Compatibility, show a DDR3/DDR4 mismatch (RG-RAM-11 against RG-PC-06), then unknown-health exclusion. Do not promote either part to healthy.
4. **Calculate.** In Recovery Optimizer use a new context, such as `travel-manual-20261021`, budget ₹2,500 and 330 minutes. Click Calculate plan. Read and record the returned plan ID, solver status, final/new counts, cash and minutes. Previously executed runs returned 7 / ₹2,150 / 299 minutes; those are comparison references, not a promise or a new measurement. A real error or different result must be recorded as observed.
5. **Fail an actual donor before work starts.** Open Simulation and select a transferred component from this actual plan. RG-SSD-10 was used in earlier canonical runs; do not inject a hard-coded donor absent from the current allocation. Inject failure and replan. Inspect the highlighted IDs and actual count/cash/time differences. Earlier runs substituted RG-SSD-11 at the same totals; check the current output.
6. **Check stale protection.** Select the original plan. Confirm Review approval is disabled. Return to the current revised plan and confirm that acknowledgement of a different revision is not carried over.
7. **Make the manual decision.** Read the exact revision and assumptions. Check the simulation-only authorization box yourself, then approve the exact simulation plan. Do not describe the local actor as a technician who examined hardware. Rejection is available, but rejecting this rehearsal plan prevents its execution; use a separate context if demonstrating rejection.
8. **Create and follow work orders.** Create simulation work orders. Use Show next available task and named dependency links. For every recorded operation, personally check the requested **simulation** items and supply an authored reference such as `synthetic:manual-travel-20261021-step-01`. Do not claim that a real drive was wiped, power was physically isolated or hardware was installed. Complete preparation/removal prerequisites before installation; some prerequisites belong to another order.
9. **Verify a simulated target.** Once a target's prerequisite work is complete, review each simulation verification item, supply a reference such as `synthetic:manual-travel-20261021-PC01`, and explicitly choose pass, fail or inconclusive as appropriate to the simulated exercise. A simulated pass requires all required checks. Confirm physical passes remain 0. Do not claim every work order passed if only one was completed.
10. **Reload and export.** Refresh and reopen a completed step: saved checks/evidence should remain visible. Export audit JSON and preserve it in the ignored travel directory. Read back the actual plan IDs, decision and simulated outcome. Record what was completed and what remains; stop if an error appears.

Do **not** inject another failure after recording a work step in this pre-event rehearsal. Current code safely pauses started work; post-start recovery/reconciliation, renewed approval and their new tests are reserved for onsite implementation.

## Offline startup evidence and limits

Executed on 21 October with currently installed dependencies:

- Backend startup at 18080 and Vite development startup at 15174 succeeded with preparation process guards rejecting non-loopback socket/DNS connections. Both external-connection self-checks passed.
- A targeted installed-Chromium smoke loaded Dashboard, import dialog, Inventory, Compatibility, Optimizer, Simulation and Reports. Non-local browser requests were blocked; there were **0 external page requests, 0 failed page requests and 0 page errors**. This was an empty-fleet startup smoke, not the manual rehearsal or a rerun of the full suite.
- `python -m pip check`: no broken requirements; all **33** backend lockfile versions match installed metadata; OR-Tools CP-SAT import passed.
- `npm --offline --prefix frontend ls --depth=0`: all direct frontend dependencies present, no reported missing/invalid dependencies. No dependency installation/download was performed.
- Python 3.14.7, Node 24.19.0 and npm 11.17.0 were used. Fonts are served from installed local assets. AI is unconfigured.

The laptop's Wi-Fi/firewall was not changed. Process guards are instrumentation, not proof of every possible native networking path or OS-level airplane mode. The existing production build passed previously; it was not rebuilt or separately smoke-tested in this travel pass. Check the actual laptop once in airplane mode before travel if practical.

Fresh dependency installation on a replacement laptop may need internet; availability of all cached wheels/npm tarballs has not been established. Figma, official event pages and external links need internet. The new ZIP is **source only, requires dependency installation, and is not an offline dependency bundle**. Preserve the installed runtimes/dependencies on this laptop and optionally copy the new ZIP and receipt to another device yourself.

## Checkpoint and reserved onsite work

The new local commit/tag and archive receipt identify the frozen tree; their hashes are recorded outside the committed document to avoid self-reference. Intended new tag: `pre-event-travel-freeze-2026-10-21`. Preserve the existing foundation commit/tag, original ZIP, checksum and receipt byte-for-byte. No push, publication or deployment is authorized.

The freeze contains the implemented synthetic import, deterministic inspection, CP-SAT/greedy allocation, **pre-work** failure replanning, exact-plan approval/reservations, simulation orders/evidence and reporting. Previous backend/browser validations remain historical evidence in PRE_EVENT_WORK; already-passing suites were not rerun.

**Reserved onsite:** recover/reconcile from actual started-work scenario locations after failure, reconcile reservations/dependencies, require renewed approval of the changed plan, resume safely, and add focused correctness/concurrency/restart tests for that new behavior. Current safe pause and its existing tests are disclosed pre-event work. No new recovery/resume or renewed-approval implementation/tests were added for travel.

Physical assessments/repairs, live AI, authentication and environmental estimates retain their documented limitations. Fetch scheduling overlap is unresolved; exact hours remain unconfirmed.


## Superseding validation - 22 October 2026

The initial manual rehearsal above remains separate and incomplete; read-only inspection found three completed steps and no verification. A new isolated automated browser rehearsal completed all 12 stages, 28/28 steps, seven simulated passes and zero physical repairs, including both-service restart under scoped network restrictions. Normal/manual databases and earlier backup files are unchanged. See FINAL_REHEARSAL_2026_10_22.md for actual results, offline limitations, new evidence location and the short manual repeat script. No application feature or dependency changed.
