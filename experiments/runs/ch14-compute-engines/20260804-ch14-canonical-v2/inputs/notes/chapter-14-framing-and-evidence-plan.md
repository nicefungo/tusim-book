# Chapter 14 — Framing and Evidence Plan

**Date:** 2026-08-04
**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (stable-main snapshot; audited read-only)
**Previous chapter:** 13 — Weight Streams (data path: quantization, sparsity, compression)

## 1. Fresh whole-tree reconnaissance (this session, not inherited)

Re-walked the full Tusim tree at the pin: `tu_cmodel/` (core, compute/, memory/, perf/, isa/, infra/, bindings/), `tests/` (73 files), `docs/` (17 module docs + 39 exploration reports), `Makefile` targets.

### 1.1 Surface inventory by coverage

| Surface | Modules | Focused tests | Sweeps | Design docs | Covered by prior chapter? |
|---|---|---|---|---|---|
| Compute engines (conv/softmax/attention/norm/pooling/elementwise) + pipeline controller | 7 `.c` (~3,060 lines) | test_convolution, test_softmax, test_attention, test_normalization, test_pooling, test_elementwise, test_pipeline (~3,070 lines) | 10 sweeps (conv, softmax, attention, pooling, norm, norm-attention, softmax-attention, conv-groups, conv-pool-cascade, mma-activation) | 7 (`*-engine.md`, `elementwise-pipeline.md`, `software-pipelining.md`, `TU_SOFTMAX.md`) | **No** |
| DRAM model | dram_model.c/h (386/184) | test_dram (320) | dram-type-clock, bus-width (2) | dram-model.md, bandwidth-modeling.md | No (DMA ch10 touched descriptors, not DRAM model) |
| Perf counters + event trace + cycle model | perf/*.c (687/228/767) | test_perf_counters, test_trace, test_cycle_model | — | performance-counters.md, event-tracing-vcd.md, cycle-accurate-model.md | Partial (ch2 cycle-model audit; ch11 scheduler) |
| Context switch | tu_context.c/h (634/285) | test_context, test_context_switch_sweep | context-switch-state-scope | multi-context-execution.md | Partial (ch5 lifecycle touched state snapshot) |
| Power/energy | power_model.c/h (641/350) | test_power_model (544) | — | power-energy-model.md | No |
| Double buffering | double_buffer.c/h (184/191) | test_double_buffer (307) | double-buffer-mtiling-recovery | TU_DOUBLE_BUFFER.md | Partial (ch10 DMA; ch9 SRAM) |
| Error handling / debug / logging / status | tu_debug.c (821), logging.c, tu_status.c, error paths | test_error_handling, test_debug, test_logging | — | exception-handling.md, debug-observability.md, TU_LOGGING.md | No |

### 1.2 Reachability reconnaissance (grep of non-test callers inside the library)

- `elementwise_pipeline` ← **wired into the command queue** (`tu_cmdq_submit_elementwise`, `tu_cmodel.c:354` → `TU_CMD_ELEMENTWISE`) and DPI.
- `softmax_engine`, `normalization_engine` ← exposed via **DPI** (`tu_dpi.c`).
- `attention_engine` ← internally composes the softmax engine, elementwise pipeline, and pluggable dataflow (documented in its header); **no non-test caller**.
- `convolution_engine`, `pooling_engine`, `pipeline_controller` ← **zero non-test callers**; exercised only by their tests.
- The MMA core (`tu_mma`) is called by `tu_conv2d_im2col_gemm` (conv engine) and by the attention engine via the dataflow dispatcher.

### 1.3 Test-provenance reconnaissance

`make test` aggregates: test-elementwise, test-norm, test-conv, test-attention, test-pool, test-pipeline (6 of the 7 engine suites). **test-softmax is a standalone Makefile target only** (like ch13's `test_int8_sweep.c` pattern). Sweeps are standalone targets.

## 2. Ranked scope candidates (evidence-derived from §1)

1. **Operator compute engines — functional semantics + engine metrics + integration map** (§1.1 row 1, §1.2, §1.3). Largest untouched functional surface: 7 modules, 7 focused suites, 10 sweeps, 7 docs. Chapter-defining finding available: only elementwise is queue-reachable; conv/attention/pooling/pipeline have no library caller; engine return values span heterogeneous domains (stall cycles, int64 success codes, stats structs with compute/dma/total cycles) — the fidelity matrix's "never sum heterogeneous return values" rule can be grounded in a real cross-engine metric census.
2. **DRAM model** (dram_model.c/h + test_dram + 2 sweeps). Configurable bandwidth/latency/preset effects; small, focused; but thin for a full chapter alone and it is the third candidate list's own surface (ch13 list).
3. **Power/energy model** (power_model.c/h + test_power_model). Table-based relative estimates; 641-line model + 544-line test is substantial, but a single-model chapter has narrow architecture breadth; best as a later "estimation surfaces" pairing with perf counters.
4. **Context switch / multi-context execution** (tu_context.c/h + test_context + sweep). Retained-state byte model + save/restore; medium size; overlaps ch5 lifecycle territory.

## 3. Selected scope: Chapter 14 — Operator Compute Engines

**Title:** *Operator Compute Engines: Functional Semantics and Engine Metrics*

**Reader decision:** How much trust does an operator-level compute model earn — for functional semantics, for returned metrics, and for integration into a running system — and how should a reader read each engine's return value?

**Why this scope:** (a) It is the largest uncovered surface at the pin, derived from this session's inventory (§1.1), not from Chapter 13's deferral list — though it coincides with candidate #1 of that list, the evidence here is the fresh module/test/doc census and the reachability grep; (b) it completes the Part-2 arc data path (ch13) → compute path (ch14); (c) it has a strong chapter-defining negative finding (integration gaps) and a positive finding (attention engine is the only composition point, and it is itself unreachable from any non-test caller); (d) the fidelity matrix already carries a "Compute engines" row whose safe/unsafe boundary this chapter operationalizes.

**Inclusions**
- Six operator engines' contracts: parameters, functional semantics, return-value semantics (exact probe-verified byte effects and returned metrics).
- Pipeline controller: bounded multi-tile pipeline state machine and overlap stats.
- Integration map: command queue → elementwise; DPI → softmax/norm/elementwise; attention internal composition; standalone conv/pooling/pipeline.
- Metric census: what each engine returns (stall cycles vs stats struct vs int64 status vs estimate API), the no-sum rule, cycle-domain boundaries.
- Test provenance: `make test` membership (softmax standalone-only) and the sweep landscape.
- Worked example: exact values for every engine from the pinned equations, hand-recomputed.
- One forced-mutation failure to prove the gates are real.

**Exclusions (explicit non-claims)**
- No whole-pipeline operator execution: there is no config → runtime → operator dispatch path; the chapter will NOT claim one.
- No calibration claims for any engine metric; all cycle values are estimates from pinned equations.
- No DRAM model, power model, perf counters, context switch (those remain future surfaces; listed in the handoff as candidates, not as Chapter 14 deferrals).
- No new references beyond verified entries added to `references/foundations.md` (one FlashAttention entry if metadata verifies; otherwise attention claims cite the engine's own header as executable-contract evidence).

**Evidence plan (fail-closed, following `references/audit-runner-pattern.md`)**
1. `ch14_source_audit.py`: pin-locked SHA-256 hashes for the 7 engine modules + 7 test files + Makefile + config JSON; structural predicates (module functions present; metric fields present in attention/pipeline stats); reachability predicates (elementwise referenced by command_queue.c; softmax+norm+elementwise by tu_dpi.c; conv/attention/pooling/pipeline absent from non-test library callers); test-membership predicates (softmax absent from `make test` aggregate).
2. `ch14_compute_engines_probe.c`: exact functional values + returned metrics per engine, values hand-recomputed from pinned source equations; prints `KEY=value` lines the runner greps verbatim.
3. `run_ch14_compute_engines_audit.sh`: provenance before/after, disposable `git archive` build, static-link gates (7 binaries + probe), focused suites under timeout with exact summary-line greps, one forced mutation (fails), manifest sealing, finalization, predraft validation.
4. Predraft validator binds bundled inputs to the canonical input commit; asserts gate strings, manifest member sets, no-audit-PASS line.
5. Manuscript validator: words/links/anchors per the ch13 pattern.

**Continuity trade-offs:** Broad-but-shallow risk (7 engines) mitigated by grouping claims per engine with a shared census frame; context budget managed by reading engine sources selectively and hand-computing probe values once. No new source pin; `edition.yaml` untouched.

**What this chapter must NOT claim (fidelity boundary):** measured latency, calibrated throughput, integrated operator dispatch, cross-engine cycle summation, hardware equivalence.
