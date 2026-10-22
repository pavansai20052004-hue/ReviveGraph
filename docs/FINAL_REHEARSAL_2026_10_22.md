# Final pre-travel rehearsal - 22 October 2026

Feature development remains paused until the 24 October event. This is disclosed pre-event validation and backup work. No production code, dependency version, schema, fixture, native Figma design or application feature changed in this pass. No blocking application defect was found.

## Automated browser rehearsal

A new isolated database was used, separate from normal inventory and the participant's unfinished manual rehearsal. All lifecycle writes were performed through actual browser controls. Read-only API requests corroborated the resulting persisted records. The test driver intercepted its own browser mutation headers to record actor **automated-pretravel-browser-20261022**; evidence references start **synthetic:automated-pretravel-browser-20261022:**. These are automated test approval/check entries, not participant-entered records or technician hardware evidence. The UI's fixed local-demo label does not authenticate either identity.

| Stage | Check actually performed | Result |
| --- | --- | --- |
| 1 | Preview 12 computers / 31 components without inventory writes | PASS |
| 2 | Explicit browser import commit | PASS |
| 3 | Synthetic evidence, DDR mismatch, unknown and physical eligibility | PASS |
| 4 | Calculate under 250000 paise / 330 minutes | PASS |
| 5 | Actual allocations, operation ledger and greedy comparison | PASS |
| 6 | Fail an actually transferred donor before work starts | PASS |
| 7 | Original/revised comparison and disabled stale approval | PASS |
| 8 | Explicit automated simulation approval | PASS |
| 9 | Create work orders and enforce prerequisite ordering | PASS |
| 10 | Record explicitly authored automated simulation checklists | PASS |
| 11 | Simulated verification and audit export | PASS |
| 12 | Restart backend/frontend and restore saved evidence | PASS |

Original plan: `plan_4414008ecc514b67ab1a64ff9d9e71c9`. Revised plan: `plan_baee240b22884f6cbfadb7f65db37ce4`. Both solver results report **OPTIMAL**, with all four objectives and returned tie objectives proven. No expected recovery count or allocation was inserted into the results. The operation ledger was independently summed by the preparation driver and matched the returned totals; allocations and donor selection were read from the actual backend.

| Actual result | Original | Revised | Same-input original greedy |
| --- | --- | --- | --- |
| Usable final / newly recovered candidates | 7 / 7 | 7 / 7 | 7 / 7 |
| Assumed cash | 215000 paise / INR 2150 | 215000 paise / INR 2150 | 215000 paise / INR 2150 |
| Technician effort | 299 min | 299 min | 299 min |
| Transfers | 7 | 7 | 7 |

No main-fleet improvement over greedy is claimed. Cash, duration, profiles and component assessments are synthetic assumptions, not vendor quotes, observed diagnostic results or measured repair times.

| Target | Selected RAM | Original storage | Revised storage |
| --- | --- | --- | --- |
| RG-PC-01 | RG-RAM-01 | RG-SSD-06 | RG-SSD-06 |
| RG-PC-02 | RG-RAM-11 | RG-SSD-02 | RG-SSD-02 |
| RG-PC-03 | RG-RAM-03 | RG-SSD-10 | RG-SSD-11 |
| RG-PC-04 | RG-RAM-15 | RG-SSD-05 | RG-SSD-05 |
| RG-PC-05 | RG-RAM-05 | RG-SSD-12 | RG-SSD-12 |
| RG-PC-06 | RG-RAM-12 | RG-SSD-07 | RG-SSD-07 |
| RG-PC-07 | RG-RAM-08 | RG-SSD-15 | RG-SSD-15 |

The failed donor was selected from the computed removal ledger: **RG-SSD-10, RG-PC-09 -> RG-PC-03**. Revised RG-PC-03 uses **RG-SSD-11 from RG-PC-11**. The original was preserved as stale and its Review approval control was disabled. The revised exact plan was approved by the automated test actor before orders were created. No post-start failure, reconciliation, resumed recovery or renewed approval was implemented or tested.

Both plans' operation counts are 7 preparation, 3 RAM removal, 4 storage removal, 3 RAM installation, 4 storage installation and 7 verification. Hand-checkable totals from pinned assumptions:

- Cash paise: `7*10000 + 3*2000 + 4*3000 + 3*5000 + 4*7000 + 7*12000 = 215000`.
- Technician minutes: `7*10 + 3*5 + 4*6 + 3*8 + 4*10 + 7*18 = 299`.

The browser recorded all **21 non-verification steps** in prerequisite order and then **7 simulated verification passes**, totaling **28/28** completed steps. Physical repair totals remained **0**. Imported computer/component JSON, including physical locations and assessment evidence, was identical before and after simulated execution.

## Actual restart and scoped offline evidence

Both test services were stopped and restarted against the same SQLite database. PIDs changed from backend/frontend **26036/34700** to **21032/22912**. A new Chromium context recovered the same revised plan automatically. Deep comparisons of the full saved plan, decisions, work orders, every step/evidence field and state passed. The UI restored checked read-only checklist items, authored evidence and simulated pass. Audit JSON was downloaded through browser controls before and after restart; its persisted plan matched exactly. The automated database passed SQLite integrity_check.

Existing installed dependencies were used; no install, dependency upgrade, production rebuild or already-passing test suite was run. This was the specifically requested complete rehearsal. Python/FastAPI and the installed Vite development server ran on loopback ports **18220/15220**.

Scoped network restriction used Python and Node socket/DNS guards allowing loopback, plus a Chromium process-only proxy directed to a closed local port for non-bypassed external traffic, resolver restrictions, blocked non-local page/WebSocket routes and disabled service workers. Both service guard self-checks passed. Each browser phase deliberately attempted `https://offline-check.invalid` and confirmed rejection. Both the complete deterministic flow and restarted flow had **0 unexpected external page/WebSocket requests, 0 failed application requests and 0 page errors**. Fonts and required assets were local; no AI provider was used.

This establishes the deterministic demo under those scoped restrictions on this laptop. System firewall/Wi-Fi settings were not changed. It is **not** an OS network namespace or proof of every native/subprocess networking path; whole-device airplane mode and fresh-machine offline installation remain unverified. Figma/event sites and fresh dependency downloads may need internet. The source ZIP is not an offline installation bundle; preserve this laptop's installed runtimes, .venv and frontend/node_modules.

Two preparation-only setup faults were corrected before the passing run: the Vite launcher initially used the repository folder rather than frontend, causing a 404; the browser's wildcard resolver restriction initially included 127.0.0.1, so that loopback address was explicitly excluded. Failed-attempt logs are preserved. No application defect was hidden and no production source fix was made.

## Participant's manual rehearsal remains separate

Read-only inspection on 22 October found **12 computers, 31 components, 2 plans, 7 work orders, 3 completed steps and 0 verification records** in the participant's existing isolated manual database. The earlier screenshots/replies establish participant import/evidence inspection, computed planning, donor failure, explicit revised-plan approval and initial authored simulation steps. The agent did not complete the participant's remaining work or relabel automated evidence as manual. That entire manual database and the normal database remained byte-identical during this new rehearsal.

## Repeat it manually - short click script

Use a **fresh, separately named rehearsal database** to repeat from import, or resume the existing manual database without importing/resetting it. Choose an unused path if the example already exists. In two project-root PowerShell terminals, using already-installed dependencies:

```powershell
$env:REVIVEGRAPH_DB = Join-Path $PWD 'backups/manual-demo-20261022.sqlite3'
.\.venv\Scripts\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 18080
```

```powershell
$env:REVIVEGRAPH_API_TARGET = 'http://127.0.0.1:18080'
npm --offline --prefix frontend run dev -- --port 15174 --strictPort
```

Open `http://127.0.0.1:15174/#dashboard`. These ordinary repeat commands do not install the automated rehearsal's network guards. Check for occupied ports first; do not stop unrelated services. To resume the participant's existing three-step run instead, use its preserved database path in TRAVEL_READINESS.md.

1. Say: **Synthetic demo; no physical repairs.** Start synthetic import -> Prepare demo preview. Check 12/31 and Validation passed, then explicitly Commit batch -> View imported inventory.
2. Open RG-PC-04 -> Assessment evidence. Show unknown health/no technician review. In Compatibility, show RG-RAM-11 vs RG-PC-06's DDR mismatch and unknown/synthetic physical exclusions.
3. Optimizer -> choose a new context, enter INR 2500 / 330 minutes -> Calculate plan. Read the actual status, allocations, ledger and greedy comparison. Do not force seven if the run returns another result.
4. Simulation -> choose a transferred donor from this actual allocation -> Inject failure and replan. Review changed IDs/totals. Select original -> confirm stale approval disabled -> return to revised.
5. Review approval -> read exact revision -> personally check simulation-only authorization -> Approve exact simulation plan -> Create simulation work orders.
6. Show next available task -> review and check only the simulation items -> enter a distinct `synthetic:manual-demo-20261022:...` reference -> Record. Repeat ready tasks; prerequisites may belong to another order.
7. At each ready Simulated verification, review the simulated boot/memory/storage/data checks, enter your own simulation reference, select the appropriate simulated outcome and record it. Do not describe it as observed real hardware verification. Confirm physical repairs stay 0.
8. Reports -> Export audit JSON. Stop both rehearsal terminals with Ctrl+C; restart both with the **same** database -> reopen the saved plan/step. Check your evidence and progress remain, then export again. Do not inject a post-start failure in this pre-event demonstration.

## Evidence, preservation and checkpoint

Evidence directory: `backups/final-pretravel-20261022T072337024021Z/`. It contains automated-rehearsal.json (stage receipts and full results), process-restart.json, verified-summary.json, downloaded automated-audit-before-restart.json / automated-audit-after-restart.json, actual PNG previews, guarded launch/driver scripts and logs, the automated SQLite file, and separately preserved normal/manual snapshots. These runtime artifacts and databases are ignored and excluded from the source archive. All 26 earlier backup-directory files and their receipts/checksums were verified unchanged.

The normal database still has no imported computers/components. Its existing preview metadata was preserved as-is. The earlier manual database is untouched; no reset/restore was performed. Earlier tags, archives and receipts remain unchanged. The new local checkpoint/archive identify the current reviewed source; their final commit/tag/archive hashes are in the external receipt, avoiding self-reference here. The archive includes source, locks, tests, fixture, docs and intended previews; it excludes credentials, databases, environments, dependencies, generated runtime files and .git. **Dependency installation is required after source-only restoration.** No push or publication was performed.

Travel readiness: all automated stages passed, no missing runtime dependency or blocking app defect was observed in the exercised flow. Manual completion, whole-device offline operation and replacement-machine installation are not claimed. Post-start recovery/reconciliation, renewed approval and their new tests remain reserved for onsite development. Exact Fetch hours remain unconfirmed.
