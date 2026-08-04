# Chapter 15 Skeptical Pre-Draft Review — 2026-08-04

**Review input:** canonical v1 (`experiments/runs/ch15-dram/20260804-ch15-canonical/`) plus independent inspection of pinned Tusim `e918c80`.  
**Initial verdict:** **DRAFT_ALLOWED: NO.**  
**Reason:** the v1 values are reproducible and the bundle is sealed correctly, but material state-machine defects, sweep contradictions, configuration/caller distinctions, and runner exit semantics were missing.

## Findings and dispositions

### 1. Historical sweep arithmetic contradicts its own constants — blocker

The report states `196608` DMA bytes, `16416` compute cycles, 32 B/cycle bus, and `TOPS = ops × clock / total`. Recomputing gives at 8 GHz:

- HBM2: 2.975 TOPS, not 2.839;
- DDR5: 1.424 TOPS, not 0.776;
- DDR4: 0.862 TOPS, not 0.435.

At 1 GHz DDR4 is about 6.4% below ideal, contradicting the report's “DRAM type is a don't-care / identical performance” conclusion.

**Disposition:** C15.23 changed from qualified historical evidence to rejected decision evidence. Added `ch15_sweep_recompute.py` and a retained v2 sweep log gate.

### 2. Bandwidth admission double-counts traffic — blocker

`pending_read_bytes + pending_write_bytes + request` is compared against `bandwidth_available`, while the latter is also decremented after each request. For HBM2 after refill, 64-B fixed-time requests first receive the bandwidth-window stall on request 2,001 after only 128,000 prior bytes, not after the nominal 256,000-B window.

**Disposition:** added C15.29, a 2,001-request probe, source predicates, and prohibited faithful-token-bucket/enforced-256-GB/s wording.

### 3. Reset retains stale window state — blocker

`tu_dram_reset()` zeros `current_cycle`, budget, pending counters, channel state, and stats but not `bw_window_start` or `bw_window_size_cycles`. If the start moved to 1,000 before reset, the next `ensure_bandwidth()` computes unsigned `0 - 1000`, refills immediately, and the first post-reset access avoids the initial window stall. Reset is history-dependent.

**Disposition:** added C15.30, source absence predicates, and a moved-window reset probe.

### 4. No non-test hierarchy-wrapper caller is demonstrated — major

The hierarchy implementation calls standalone DRAM, but no other non-test C source calls `tu_mem_hierarchy_init/read/write/tick`. The surface is linked and focused-tested, not shown in ordinary execution.

**Disposition:** added C15.32 and a whole-`tu_cmodel` caller predicate. Replaced “last off-chip feeding surface” with “last substantial linked off-chip accounting/model surface.”

### 5. Configuration paths were conflated — major

The full loader reads JSON. The separate YAML generator emits DRAM latency macros but not DRAM type, bandwidth, channels, row mode, or core clock. Compiled constants, full-config direct consumers, runtime conversion, and standalone construction are distinct. In addition, `tu_power_model_from_config()` directly consumes full-config `dram_bandwidth_gbps` as a 1-vs-2-GHz heuristic even though runtime conversion and standalone DRAM construction do not.

**Disposition:** rewrote C15.16/C15.17; added generator/power hashes and predicates. Chapter 17 owns detailed power semantics.

### 6. GDB process status did not gate inferior failure — major

GDB batch mode returns zero even when the inferior exits code 1. Canonical v1 retained the correct `11/12` mutation output, but its shell status alone was not a live negative gate.

**Disposition:** v2 requires `exited normally` for passing DRAM/hierarchy/probe binaries and `exited with code 01` for the expected mutation.

### 7. Official hierarchy suite was not executed in v1 — major

The custom probe established a discriminating byte/stall boundary but did not replace focused-suite provenance.

**Disposition:** v2 statically links and requires the official `test_memory_hierarchy.c` `10/10` result and normal inferior exit.

### 8. Custom parameters are not validated — moderate

Zero channels, zero burst length with multiple channels, non-finite/negative bandwidth, and degenerate geometry can enter unsafe paths. Executing them is unnecessary and risks undefined behavior.

**Disposition:** added static C15.31 and source predicates; the manuscript will classify rather than execute unsafe cases.

### 9. Focused reset coverage was overstated — moderate

The suite's reset test does not first move the bandwidth-window start, so it cannot expose stale-window behavior.

**Disposition:** C15.21 now says superficial reset coverage and enumerates the missing stateful cases.

### 10. Plan rationale needed a coverage correction — moderate

The initial 21-chapter replan treated double buffering as covered by Chapters 9/10/14. Independent manuscript review showed those chapters establish prerequisites and negative boundaries but do not teach `double_buffer.[ch]`.

**Disposition:** `PLAN.md` and the replanning record now govern a 22-chapter first edition with Double Buffering and Legal Overlap as Chapter 16.

## Closure rule

Drafting remains blocked until canonical v2:

1. bundles the amended inputs from one clean book commit;
2. passes the 17-hash/53-predicate source audit and live mutation;
3. passes static link, DRAM 12/12, hierarchy 10/10, GDB inferior-status gates, expanded probe, and sweep recomputation;
4. passes immutable manifest/predraft validation and repository containment;
5. updates this review with a final **DRAFT_ALLOWED: YES** disposition.
