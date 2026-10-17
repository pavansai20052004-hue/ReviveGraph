# Synthetic fixture v1

Status: **pre-event preparation, 16 October 2026**. The files in [`datasets/synthetic-v1/`](../datasets/synthetic-v1/) are invented demonstration inputs, not diagnostic readings, technician-approved assessments, vendor quotes, solver output or evidence of repaired computers. This document and the Python validator describe a constrained simulation. The Figma prototype remains illustrative and unchanged.

## Contract and provenance

The two CSV files use **exactly** the proposed CSV schema v1 columns in [ARCHITECTURE.md](ARCHITECTURE.md#api-contracts-proposed-apiv1). Empty `location_asset_id` means institution-owned stock; otherwise it must reference one of the 12 computers. No CSV import contract change is requested. The four JSON sidecars are preparation metadata for fixture loading, board rules, resource assumptions and expected examples; they are **not** fields accepted by the proposed two-file import endpoint. The application must load/pin these sidecars or supply equivalent versioned rules before running a scenario. The import design must eventually define how board profiles and scenario metadata are registered; that endpoint behavior is not implemented.

All CSV rows have `synthetic:` provenance. Each component assessment has a unique `SYN-V1-*` evidence reference; the [manifest](../datasets/synthetic-v1/manifest.json) gives their common authored source, date, reviewer label and simulation-only scope. Base-condition provenance is in each computer row. This common context is **not** a per-assessment timestamp or individual human review. Architecture's full evidence entity will need an evidence sidecar or an explicit later CSV/schema extension before the backend can store source, timestamp and reviewer per assessment; CSV v1 alone cannot provide that fidelity. Each board profile has a synthetic source and evidence reference. [Operation costs](../datasets/synthetic-v1/operation_costs.json) identify an invented cost/time source. No numeric health score, manufacturer compatibility certification, physical observation or AI assessment is implied. All 31 physical components have one ID, one owner (`RG-INST-01`) and one initial location. The initial location is the fixture's origin record; stock has no source computer. Transfers are within one owner. A failed donor remains physically at its source in the scenario overlay until hypothetical work is approved and executed.

This toy desktop model moves whole RAM modules and whole 2.5-inch SATA drives only. CPU, motherboard, cooler, PSU, chassis and required display capability are a fixed base. One keyboard, display and boot/install media are assumed available outside allocation. The demo usefulness policy requires an accepted healthy base, **at least 8 GiB** compatible RAM and **one at least 240 GB decimal** compatible SATA drive. An initially usable computer would not count as newly recovered. None is certifiably usable in this synthetic starting state: eight have a known faulty/missing blocker, while four have an unknown assessment or decisive profile field. “Unusable” in the manifest means *ineligible for the demo's initial usable count*, not a claim that every uncertain physical machine was proven broken.

| Profile | Supported RAM | Limits | Storage | Special rule |
| --- | --- | --- | --- | --- |
| `RG-BOARD-D4-A` | DDR4 1.2 V, full-size non-ECC unbuffered UDIMM, 2133/2400 MT/s | Two slots, 8 GiB/slot, 16 GiB total | One bootable 2.5-inch SATA drive; port, bay, data/power declared | Mixed module speed/capacity not allowed |
| `RG-BOARD-D4-B` | DDR4 1.2 V UDIMM, **2400 MT/s only** | One slot, 8 GiB total | Same declared SATA support | Makes slow DDR4 RAM incompatible with `RG-PC-04` |
| `RG-BOARD-D3-A` | DDR3 1.5 V UDIMM, 1333/1600 MT/s | Two slots, 8 GiB/slot, 16 GiB total | Same declared SATA support | DDR4 cannot be used |
| `RG-BOARD-D4-UNKNOWN` | DDR4 1.2 V UDIMM, 2400 MT/s | One slot, 8 GiB total | SATA boot support **unknown** | Allocation to `RG-PC-09` blocked |

The profiles are toy assumptions, not a catalogue of real motherboards. DDR3L-only, DDR5, SO-DIMM, ECC/registered memory, NVMe/M.2, adapters and proprietary assemblies are outside scope. A known disqualifier is incompatible; a missing decisive field is unknown; neither feeds allocation. Even healthy synthetic evidence is eligible only for this simulation.

## Initial fleet

The table is derived from the CSV plus board policy and mirrored in the manifest. `RG-PC-11` and `RG-PC-12` can donate separately assessed healthy parts but their bases cannot be recovered by moving RAM/storage.

| Computer | Base/profile | Concrete initial blocker | Starting classification |
| --- | --- | --- | --- |
| `RG-PC-01` | healthy / D4-A | `RG-SSD-01` faulty | Unusable |
| `RG-PC-02` | healthy / D4-A | `RG-RAM-02` faulty | Unusable |
| `RG-PC-03` | healthy / D4-A | `RG-SSD-03` faulty | Unusable |
| `RG-PC-04` | healthy / D4-B | `RG-RAM-04` health unknown; not eligible | Uncertified, counted unusable for planning |
| `RG-PC-05` | healthy / D4-A | No installed storage | Unusable |
| `RG-PC-06` | healthy / D3-A | `RG-RAM-06` faulty | Unusable |
| `RG-PC-07` | healthy / D4-A | `RG-SSD-08` faulty | Unusable |
| `RG-PC-08` | healthy / D3-A | `RG-SSD-09` faulty | Unusable |
| `RG-PC-09` | healthy / D4-UNKNOWN | SATA boot support unknown; complete configuration cannot be certified | Uncertified, counted unusable for planning |
| `RG-PC-10` | healthy / D4-A | `RG-SSD-13` health unknown; not eligible | Uncertified, counted unusable for planning |
| `RG-PC-11` | faulty / D4-A | Fixed base faulty | Unusable; donor only |
| `RG-PC-12` | unknown / D3-A | Fixed base health unknown; not eligible | Uncertified; donor only |

Initial count: **0 certifiably usable, 8 with a known faulty/missing blocker, 4 uncertain, 12 not certifiably usable** under the simulation policy. This is a policy classification of synthetic assertions, not physical diagnostic evidence. `RG-SSD-16` is a healthy 128 GB spare that fails the 240 GB usefulness threshold.

## Operations and two feasible examples

All values are invented, nonnegative **INR paise** and technician **minutes**; they are not estimates from a shop or a timed repair. Cash represents assumed consumables/shop overhead only; technician effort is separately constrained without a second wage charge. The single technician pool is effort, not a completion schedule. Retained parts incur no removal/install cost. Every removed installed part, including faulty/unknown displaced parts and healthy donor parts, is charged once; stock has no extraction. Every incoming part is installed once. Each selected target gets one preparation and verification operation. Simulated verification is an operation allowance, not a completed pass.

| Operation | Paise | Minutes |
| --- | ---: | ---: |
| Prepare target | 10,000 | 10 |
| Remove RAM | 2,000 | 5 |
| Remove storage | 3,000 | 6 |
| Install RAM | 5,000 | 8 |
| Install storage | 7,000 | 10 |
| Verify target | 12,000 | 18 |

The main scenario limit is **250,000 paise (₹2,500)** and **330 technician minutes**. These final configurations are **feasible examples only**, not proven fleet optima or executed repairs. RAM and storage IDs that already sit in the same target are retained. The donor failure is applied **before approval/work**, so the before and after plans are separate proposed revisions with unchanged physical locations.

| Target | Before: RAM / storage | After `RG-RAM-07` failure: RAM / storage |
| --- | --- | --- |
| `RG-PC-01` | `RG-RAM-01` / `RG-SSD-06` | Same |
| `RG-PC-02` | `RG-RAM-11` / `RG-SSD-02` | Same |
| `RG-PC-03` | `RG-RAM-03` / `RG-SSD-11` | Same |
| `RG-PC-04` | `RG-RAM-07` / `RG-SSD-05` | **`RG-RAM-15`** / `RG-SSD-05` |
| `RG-PC-05` | `RG-RAM-05` / `RG-SSD-12` | Same |
| `RG-PC-06` | `RG-RAM-12` / `RG-SSD-07` | Same |
| `RG-PC-07` | `RG-RAM-08` / `RG-SSD-15` | Same |

`RG-RAM-07` starts inside faulty-base `RG-PC-11`, so its removal is required before the first proposed installation in `RG-PC-04`. `RG-SSD-11` also comes from `RG-PC-11`. The simulated failure makes `RG-RAM-07` faulty/ineligible; the alternate uses stock `RG-RAM-15`, still 2400 MT/s for D4-B. No part is allocated to two targets, and neither donor is counted recovered.

| Operation count | Before | After |
| --- | ---: | ---: |
| Prepare target / verify target | 7 / 7 | 7 / 7 |
| Remove RAM / storage | 4 / 4 | 3 / 4 |
| Install RAM / storage | 3 / 4 | 3 / 4 |

Before: `7×(10,000+12,000) + 4×2,000 + 4×3,000 + 3×5,000 + 4×7,000 = 217,000 paise (₹2,170)`; time `7×(10+18) + 4×5 + 4×6 + 3×8 + 4×10 = 304 minutes`. After: remove one fewer donor RAM, so **215,000 paise (₹2,150), 299 minutes**. The alternate happens to be cheaper/faster because its replacement is already in stock; a failure does not inherently raise cost in this toy model. Both fit the declared limits. These operation counts are recomputed from final IDs and starting locations by the validator, then compared with the frozen expectations in `scenarios.json`.

## Independent small cases and proof scope

[`scripts/validate_synthetic_fixture.py`](../scripts/validate_synthetic_fixture.py) exhaustively enumerates **restricted tiny cases** with one 8 GiB RAM module and one drive per target, chosen from retained healthy parts plus each case's listed pool. It recomputes eligibility and the same physical operation costs, tests the unique-part and resource constraints, and compares the result with these expectations. This is a **preparation oracle**, not the future CP-SAT optimizer. Exhaustive results prove the stated maxima only inside each tiny case's restricted candidates and target set, never for the main 12-computer fleet.

| Tiny case | Expected maximum | Manual reason |
| --- | ---: | --- |
| Greedy trap | 2; documented greedy baseline gets 1 | Targets `RG-PC-02` (D4-A) and `RG-PC-04` (D4-B) compete for stock `RG-RAM-15` (2400); only PC-02 also accepts stock `RG-RAM-16` (2133). In ID order the equal-cost greedy choice takes RAM-15 for PC-02 and strands PC-04. PC-02→RAM-16 and PC-04→RAM-15 costs **58,000 paise / 82 min**. Two targets are an upper bound, so 2 is exact for this tiny case. |
| One physical part | 1 | PC-01 and PC-03 each need storage, but the pool holds only `RG-SSD-06`; two uses of one ID are forbidden. Either single repair costs 32,000 paise / 44 min. |
| No compatible spare | 0 | PC-05 needs ≥240 GB; its only candidate `RG-SSD-16` is 128 GB. |
| Unknown health | 0 | PC-02 cannot use unknown `RG-RAM-04` even though its basic DDR4 form is compatible. |
| DDR3/DDR4 mismatch | 0 | DDR3 PC-06 cannot use DDR4 `RG-RAM-11`. |
| Unknown board boot support | 0 | PC-09 cannot be allocated while the decisive SATA boot field is null. |
| Zero budget; zero time | 0; 0 | PC-05 + SSD-06 needs strictly positive cash and effort, so either zero limit blocks it. |
| Exact boundary | 1 | PC-05 + SSD-06 costs `10,000+7,000+12,000 = 29,000` paise and `10+10+18 = 38` min, exactly the case limits. |
| One paise short; one minute short | 0; 0 | Limits of 28,999 paise/38 min and 29,000 paise/37 min each exclude that sole option. |

The greedy trap is deliberately restricted to `RG-RAM-15`/`RG-RAM-16` to prove an algorithmic point; it is not the full-fleet baseline result. The documented baseline breaks equal cash/time options by component ID. The production optimizer, full graph visualization, plan API and approval flow remain onsite implementation work. The later disclosed registration/import/inventory/inspection foundation is documented separately in [FOUNDATION_CONTRACT.md](FOUNDATION_CONTRACT.md); it does not use these handwritten allocations as computed results.

## Validation and design synchronization

Run from the project root:

```powershell
& 'C:\Users\pavan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\validate_synthetic_fixture.py
```

The script checks exact CSV headers/counts, uniqueness, owner/location/profile references, supported part form and installed layout, explicit synthetic provenance, blockers, nonnegative integer operation inputs, selected configuration eligibility, one-use physical IDs, donor-failure exclusion and recomputed resource totals. It enumerates only the listed tiny cases. It does **not** test an import transaction, a solver, API behavior, actual hardware, Figma interaction or physical repair.

The [Figma frames](UI_PLAN.md#native-figma-design-created-on-16-october-2026) still contain independent illustrative content and must be reconciled **after** a real solver is implemented: R1/R2 “4 recoverable” labels, ₹11,200/310 min and ₹12,400/345 min, the R1→R2 allocation of `RG-RAM-07`/`RG-RAM-11`, and any derived dashboard/chart, work-order, approval or simulation labels. The fixture instead documents feasible 7-target examples at ₹2,170/304 min and ₹2,150/299 min, without a proven main-fleet optimum. Do not simply paste these feasible counts into a “solver optimum” frame.
