# Chapter 14 Skeptical Review Dispositions

- **Chapter boundary:** Operator Compute Engines: Functional Semantics and Engine Metrics
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Review stage:** pre-draft evidence/scope gate
- **Method:** adversarial source, caller, configuration, Makefile, probe, and provenance review over the sealed canonical-v2 bundle, with an independent rebuild of the probe against a fresh disposable pinned tree
- **Current canonical target:** `experiments/runs/ch14-compute-engines/20260804-ch14-canonical-v2` (superseded at closure by the v3 reseal that bundles the review amendments and the verified `[DAO22]` reference — see R8)

## Gate question

Can a skeptical reader use the planned evidence to distinguish, per engine, functional byte effects (exact outputs), deterministic analytical estimates (stall returns, cycle counts, stats-struct fields — all from pinned equations, never calibrated), reachability (which engines have non-test library callers), the known attention staging defect (UB-dependent corruption), and calibration absence — without silently importing stronger claims from headers, exploration docs, or test titles?

## Dispositions

### R1 — “One integrated operator dispatch path” implication

**Finding:** The seven engine modules share headers, a `compute/` directory, and Gap-tracker identifiers that could be read as one operator runtime with a config-selected dispatch path.

**Disposition:** **Resolved.** C14.24 and framing exclusion #1 state there is no config → runtime → engine selection path; the reachability predicates (`reach-cmdq-elementwise`, `reach-dpi-softmax`, `reach-dpi-elementwise`, `reach-dpi-norm-include-only`) plus the C14.20 caller inventory prove only elementwise is queue-wired and softmax/elementwise are DPI-wired. The manuscript's 14.10 integration map table and the audit's “adjacent surfaces, not one configured operator dispatch path” fidelity label keep the seams visible. The aggregate `make test` membership of six suites is presented as a reachability fact, not as integration evidence.

### R2 — Stall/cycle returns read as measured latency

**Finding:** “Softmax costs 96 cycles” could be read as a measured latency.

**Disposition:** **Resolved.** C14.2/C14.23 and the audit fidelity labels classify every return as a deterministic analytical estimate from pinned equations; the manuscript's 14.1 no-sum rule and 14.12 fidelity box state explicitly that none is measured or calibrated. The word “stall cycles” is scoped to the SRAM budget model's penalty accounting, and the pipeline/conv/attention totals are equation evaluations, not timers.

### R3 — Heterogeneous returns summed

**Finding:** A reader could total the engines' returns into a pipeline latency.

**Disposition:** **Resolved.** The census (C14.3) makes the heterogeneity visible in three engines sharing one SRAM model (96 read+write stalls / 80 write-only stalls / 40 refilled-budget write-labeled events); the manuscript's 14.2 table and failure-mode #1 forbid the sum. The fidelity matrix's “Compute engines” row is operationalized rather than merely quoted.

### R4 — Normalization's discarded read return

**Finding:** “Normalization: 80 stall cycles” is a partial ledger; a reader could compare it directly with softmax's 96 as a cost ranking.

**Disposition:** **Resolved.** C14.3 documents the exact defect (`normalization_engine.c` load helper: `uint64_t s = 0;` then `tu_sram_read(...)` without assignment, `total_stall += s`). The manuscript 14.4 explains that the loads still consume bank budget (the store stalls are identical to softmax's) and that only the load-stall component (16) is dropped — so the 80 is write-only accounting, not “softmax minus 16.”

### R5 — Elementwise post-hoc accounting and the in-place half-metering quirk

**Finding:** The ledger described elementwise's post-hoc `words_available` accounting and the `tu_sram_advance_cycle` refill, but not the in-place `i/2` indexing: the loop computes `words = elem_count` yet addresses `off += (i/2)·sizeof(float)`, so a 40-element census meters only elements 0..19 (each twice) — 20 served + 20 stalled on 20 banks. The returned 40 is therefore not 40 physical accesses and not “one stall per element.”

**Disposition:** **Resolved by qualification (additive).** C14.3 now carries the `i/2` half-metering wording and the 20-served/20-stalled decomposition; the manuscript 14.2/14.5 state it and failure-mode #4 warns against reading 40 as a per-element cost. No re-run is needed for this wording, but it is bundled into the v3 reseal so the sealed ledger carries it (R8).

### R6 — Attention suite qualified gating: honesty of the invariant

**Finding:** The exact failing attention test varies by build (v1 run: 6/9 with `test_deterministic_small`, `test_causal`, `test_scale`; v2 run: 8/9 with `test_scale`; mid-audit build: 8/9 with `test_scale`; rebuild: 7/9 with `test_deterministic_small` + `test_causal`). A gate pinned to one failing test or one count would be dishonest.

**Disposition:** **Resolved.** The runner gates the invariants — rc=1, at least one FAIL line, never 9/9 — with a `[1-8]/9` count regex and prints `ATTENTIONSUITEQUALIFIED PASS rc=1 summary=<observed> failing_subset_ub_dependent=yes`. v1 (6/9) failed the earlier stricter `[78]/9` gate and is retained as immutable history; v2 (8/9) sealed. C14.8/C14.22 record the observed 6–8/9 range and the UB-dependent failing subset; the manuscript 14.8 and answer key #5 explain why the specific failing test is not a stable claim.

### R7 — Probe values vs pinned source equations

**Finding:** Probe values could be stale or mis-derived; the sealed transcript's own CHECKs are not independent evidence.

**Disposition:** **Resolved.** An independent reviewer rebuilt the probe from a fresh disposable pinned archive and confirmed **all** sealed values reproduce exactly, including `CONV dims oh=3 ow=3 im2col_rows=3 im2col_cols=9`, `estimate_cycles=69`, `SOFTMAX zeros … stall=8`, census 96, `invalid=18446744073709551615`, `NORM layernorm … mean=1.000000 var=0.000000 stall=8`, RMS 0.999995, census 80, `EW chain … stall=2`, census 40, `POOL max … cycles=18`, `avg … cycles=34`, `ATTN tiny rc=0 out=0.099976 0.199951 dma=16 tiles=2 flops=8 cc=145 dc=2 tc=147 u=0.9864`, `ATTN corrupt` all zeros, `deviates=1 scales_equal=1`, `PIPE depth1 sequential_total=204`, `PIPE depth2 sequential_total=402 saved=200`. The reviewer additionally hand-derived the census mechanisms from `tu_sram.c` (`sram_bw_consume`, `tu_sram_advance_cycle`, 32 banks × 4 B, penalty 2), matching C14.3's 96/80/40 decomposition. C14.3/C14.11/C14.14–C14.19 stand as verified.

### R8 — Provenance and seal binding

**Finding:** The book HEAD moved past the v2 sealing commit (a7881be) after the seal: `references/foundations.md` gained a verified `[DAO22]` FlashAttention entry (metadata verified against the arXiv API on 2026-08-04) and the review's ledger amendment (R5) is uncommitted. The sealed `input-hashes.txt` still verifies at a7881be and the run's bundled `inputs/` still bind to that commit, but the *current* book inputs no longer hash-match the v2 seal.

**Disposition:** **Resolved by reseal.** The final canonical seal is the **v3 reseal** (`20260804-ch14-canonical-v3`), which bundles the amended ledger, the framing/report text, and the `[DAO22]`-bearing `foundations.md` — so the seal matches the current book inputs at the sealing commit and no post-seal bundled-input amendment is needed. v1 (truncated at the attention gate — the exact retained-failure pattern) and v2 remain immutable history. The audit report's canonical-run line is amended post-seal to name v3, with the seal-definition sentence binding the seal to v3's sealing commit; the bundled copies under `inputs/` remain the binding evidence.

### R9 — Audit-script coverage gap: values vs structure

**Finding:** The source-audit script enforces structural facts (28 hashes, entry points, stats-struct fields, defect markers, stall-asymmetry markers, reachability, test membership) but contains no predicate that re-derives an engine equation. The exact values (96/80/40/18/34/69/145/2/147/0.9864/204/402/200) are enforced only by the probe's own CHECKs and the runner's verbatim greps; a source-equation drift that happened to leave the probe values unchanged would escape the audit script (though it would still fail the runner's exact-value greps).

**Disposition:** **Non-blocking, noted.** The value claims are gate-enforced at the behavioral layer (probe CHECKs + runner `EXPECTED_FINDING MATCH` greps), which is the intended division: structural drift is caught by the hash/entry-point gates, behavioral drift by the probe. A future audit extension could add per-engine equation predicates (e.g. an `ew-half-meter-i2` marker for the `i/2` indexing, and a `norm-read-stall-discard` companion on the store path). This does not affect the current seal.

### R10 — Arithmetic and UB hazards

**Finding:** The attention corruption magnitudes are UB-dependent (4-byte copies read stack garbage); engine equations use unguarded uint64 arithmetic at extreme dimensions; elementwise and attention stats depend on prior global/SRAM state.

**Disposition:** **Resolved by qualification.** C14.8/C14.10 are qualified: the chapter gates robust properties (`deviates=1`, `scales_equal=1`, rc=1, never 9/9) and explicitly rejects arbitrary-input FP16 attention correctness (C14.25, manuscript 14.8/14.12). C14.11 states attention stats are deterministic only on fresh state. The manuscript 14.12 fidelity box limits all claims to the tested shapes and value domains; the probe CHECKs stay within them.

## Verdict

**Current verdict:** **PASS.** The gate question answers affirmatively: byte effects, analytical estimates, reachability (including the include-only gap), the UB-dependent attention defect, and calibration absence are all distinguishable from the sealed evidence without importing stronger claims. Required changes were additive: C14.3 gained the elementwise `i/2` half-metering decomposition (R5), the manuscript gained failure-mode #4 and the corrected smallest-row wording, and the canonical seal is re-run as v3 to bundle the amendments plus the verified `[DAO22]` reference (R8). The audit-script coverage note (R9) is recorded as non-blocking.
