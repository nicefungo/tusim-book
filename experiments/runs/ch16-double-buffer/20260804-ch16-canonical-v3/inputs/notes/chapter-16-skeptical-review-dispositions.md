# Chapter 16 — Skeptical Pre-Draft Review Dispositions

**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`

**Reviewed seal:** `experiments/runs/ch16-double-buffer/20260804-ch16-canonical-v1`

**Sealing input commit:** `06ce91f03c022b9e580b15ac10f69d9867b08c6e`

**Method:** independent pinned-source read, caller/config/Makefile inventory, manifest verification, fresh disposable static rebuild, hand recomputation of every probe line, and independent report arithmetic.

## Gate question

Can a skeptical reader distinguish standalone SRAM ownership and legal swaps, descriptor-DMA byte effects, controller accounting, and ideal overlap equations without inferring a workload-reachable integrated pipeline?

**v1 verdict: BLOCK.** The evidence correctly rejected the apparent DMA-to-shadow bridge, but the review found additional lifecycle, no-load, accounting, report-equation, plan-boundary, and evidence-coverage requirements. Canonical v1 remains immutable and is superseded for drafting by the required post-review seal. The first post-review attempt, `20260804-ch16-canonical-v2`, retained all amended executable evidence but failed closed because the validator still expected v1's source-audit counts; it is also immutable and not drafting authority.

## Dispositions

1. **R1 — Provenance and immutability: RESOLVED.** The v1 bundle hashes verify; the source is detached and clean at the edition pin; the book's sealing input is the parent of the retained-run commit. The validator passes normally and under `python -O`. v1 remains a valid record of its inputs.

2. **R2 — Surface separation and reachability: QUALIFIED.** The pipeline controller is the only non-test source caller that combines descriptor and double-buffer APIs, but no non-test caller invokes the pipeline controller. Ordinary CModel execution uses separate legacy/global paths. The Chapter 16 boundary is now explicit in `PLAN.md`: Chapter 16 owns the standalone state machine and cross-surface legality matrix, not a second descriptor or controller tutorial.

3. **R3 — Ownership/validity protocol: QUALIFIED.** `shadow_dirty` is caller-supplied notification state, not a valid bit, freshness proof, byte-count bound, descriptor binding, or completion token. A clean swap is legal in source. The retained wording is now in C16.5 and the audit report: swap legality must be imposed and verified by a caller.

4. **R4 — Configuration and hierarchy reachability: QUALIFIED.** Shipped JSON/YAML/runtime conversion contain no standalone double-buffer selector. `tu_mem_level_config_t.double_buffered` defaults local SPAD true and can be overridden, but hierarchy construction never materializes the standalone state. `pipeline_depth` is a separate PE field. No configuration bridge is claimed.

5. **R5 — Executable bridge behavior: RESOLVED/NEGATIVE.** Fresh rebuild and hand derivation reproduce `desc_cycles=53`, DMA cycle 1, controller cycle 0, fresh `0x7a` in the old active allocation, stale `0x22` exposed active after swap, and post-swap dirty attribution to the new shadow. This proves an invalid bridge, not legal overlap.

6. **R6 — Controller legality and ledgers: NEW FINDING.** A depth-1, three-cycle tile with no load still enters PRELOAD and swaps an enabled region. It reports `5/3 = 1.666667x` while both overlap credits and saved cycles are zero because the sequential baseline alone charges absent DMA operations. A depth-2, five-cycle first tile starts directly in COMPUTE but skips `total_compute_cycles`, producing `7/0` and infinite speedup. The amended probe and ledger gate both cases. Controller speedup is not overlap evidence.

7. **R7 — Lifecycle/context: NEW FINDING.** Context restore overwrites a live region's `db` pointer with `NULL` without freeing it. It exposes restored primary bytes and discards active role, shadow bytes, dirty state, swaps, and ledgers. C16.22 is rejected; context switching is not an integration bridge.

8. **R8 — Analytical report: NEW FINDING.** The report's reproduced table is only one ideal model. Its `m_tile >= 20` threshold does not solve its tile-dependent equation: continuous algebra gives `18.285714...`; ceiling-aware timing first passes at row 17. The 16 KiB role consumes 32 KiB physical when doubled, the reported 512 B/cycle premise conflicts with 256 PEs x two FP16 operands (1,024 B/cycle before reuse assumptions), and the area/compiler/universal claims remain rejected. Other PE/depth reports remain separate unreconciled analytical surfaces.

9. **R9 — Test/build provenance and audit integrity: QUALIFIED.** `test-double` has no rule and is not aggregate; direct static execution is 10/10 and its assertion mutation fails 9/10. `test-pipeline` has a rule and aggregate membership but requests four channels against fixed three-entry storage, so it is not run as a green gate. The bounded one-channel probe does not stand in for the full suite. The scheduler's “double-buffered” test is a distinct instruction-order/address-range model and calls neither Chapter 16 API family.

10. **R10 — Clock and completion bridge: QUALIFIED.** Descriptor completion and `cycles_completed`, DMA current cycle, controller current cycle, SRAM refill cycle, and manually supplied double-buffer cycles remain distinct. `cmd_id` is stored but not dispatched. `enable_triple_overlap` and `tile_timeout_cycles` are decorative. No common-clock or compute-visibility bridge exists.

## Required amendments before drafting

- retain v1 unchanged;
- amend `PLAN.md`, framing, ledger, and report with the boundary/lifecycle/accounting/report findings;
- extend the focused probe with depth-1 no-load and compute-only accounting cases;
- gate the corrected threshold recomputation and all new exact probe lines;
- include this skeptical review in the next bundle;
- seal and validate a fresh canonical v3 after retaining the validator-blocked v2; only v3 may authorize drafting.

**Post-amendment gate:** pending canonical v3 at the time of this review document. No manuscript drafting is authorized by v1 or failed v2.
