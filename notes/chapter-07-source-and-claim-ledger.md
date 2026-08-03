# Chapter 7 Source and Claim Ledger

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Audit:** [`../experiments/ch07-dataflow-audit-2026-07-25.md`](../experiments/ch07-dataflow-audit-2026-07-25.md)
- **Probe:** [`../experiments/ch07_dataflow_probe.c`](../experiments/ch07_dataflow_probe.c)
- **Enforced source/formula audit:** [`../experiments/ch07_dataflow_audit.py`](../experiments/ch07_dataflow_audit.py)
- **Fail-closed reproducer and transcript:** [`../experiments/ch07_reproduce.sh`](../experiments/ch07_reproduce.sh), [`../experiments/ch07-reproduction-2026-07-25.log`](../experiments/ch07-reproduction-2026-07-25.log)

## Reader decision

Given a candidate WS, OS, or RS mapping, decide which differences Tusim executes, which are only logical descriptions or deterministic formulas, how selection reaches active state, and what evidence is still required before making bandwidth, reuse, latency, or hardware recommendations.

## Contract separation

| Contract | Pinned behavior | Must not be inferred |
|---|---|---|
| Geometry | shared `R×C×C` dispatcher tiles | a dataflow-specific mapping shape |
| MMA semantics | same `m,n,k` scalar FP16-input/FP32-accumulate loop in WS/OS/RS | physical PE transfers or canonical subnormal handling |
| Logical dataflow | plug-in identity, comments, RS-private shape arithmetic | executed stationary storage, streams, multicast, or traffic reduction |
| Timing | hard-coded per-K-tile fill/execute/drain sums | coherent DMA+MMA latency, calibrated cycles, frequency, area, or energy |

## Source map

| Source | Evidence | Caveat |
|---|---|---|
| `compute/dataflow/dataflow_interface.h` | enum, descriptor, callbacks, generic stats | declares unimplemented NLR; ownership and “total” wording drift from behavior |
| `dataflow_registry.[ch]` | global registry, lookup, duplicate-address stability, destroy | same-ID replacement discarded without equivalence check; destroy not integrated; instances shared by cores |
| `dataflow_dispatcher.c` | shared tiling, callback order, generic counter updates | never calls `get_compute_cycles`; full nominal edge sizes reach fill/drain |
| `weight_stationary.c` | WS scalar kernel and cycle helpers | no spatial schedule; local defective FP16 converter; depth falls back to 2 |
| `output_stationary.c` | OS scalar kernel and `k+ceil(k/4)` return | “bandwidth” term ignores M/N/bus width/ports/traffic |
| `row_stationary.c` | RS scalar kernel, shape-derived reuse fields, reduced overhead | same loop as WS/OS; reuse fields opaque and reset each dispatch |
| `tu_cmodel.c` | registration, direct selection, public counter transfer/reset, DMA wrappers | init selects compile-time mode; plug-in tile/FLOP fields are scratch; W/A/store wrappers read the wrong DMA state |
| `dma_descriptor.c` | legacy transfer cycles accumulate in `g_tu_dma` | engine is process-global and not the snapshot-local object read by wrappers |
| `infra/config.c` | JSON parses dataflow and pipeline depth | unknown names become WS; conversion drops both fields |
| `tu_core.c` | core snapshots and swap-in/out | global selection outside core does not select core dataflow |
| `bindings/tu_dpi.c` | instance requested-mode metadata and active-name API | NLR summary can disagree with fallback WS execution |
| `perf/{cycle_model,performance_counters}.*` | parallel dataflow-cycle buckets and producer | producer hard-codes WS; no RS bucket; diff/merge omit buckets |
| `tests/test_dataflow.c` | nine focused registry/equivalence/switch tests | no timing/config/subnormal/core-selection assertions; RS omitted from edge comparison |
| `tests/test_dataflow_sweep.c` | historical comparison question | non-gating zero exit; all core runs remain WS; formulas differ from dispatcher |
| `Makefile` | library membership and test targets | sweep excluded from aggregate; several targets can link stale `.so` if present |

## Claim ledger

| Claim | Evidence | Label | Safe boundary |
|---|---|---|---|
| WS/OS/RS are compiled and registered | Makefile, registry, probe | executable | three built-ins only |
| Direct `tu_set_dataflow(0..2)` changes active global plug-in | source and probe | integrated/executable | process-global state, explicit call after init |
| JSON dataflow selects active plug-in | contradicted by conversion and probe | rejected | unknown names silently become WS; recognized names parse but active init remains compile-time WS |
| process-global selection changes a `tu_core_t` | contradicted by swap path and probe | rejected | select in the state actually used by the core; no public core-specific selector exists |
| NLR is supported | enum/comment only; lookup misses and falls back | rejected | fallback returns success; DPI can report requested NLR while active name is WS |
| WS/OS/RS produce equal audited normal outputs | bitwise probe over nonsymmetric/edge/multi-K cases | executable functional model | same reduction grouping and local conversion code |
| WS/OS/RS implement distinct physical movement | contradicted by identical scalar loops and absent traffic state | rejected | names/comments describe intended logical mappings only |
| all three share the FP16 subnormal defect | raw `0x0001 × 1` probe | executable defect | observed `2^-14`; canonical is `2^-24` |
| pinned WS cycles are `T_M T_N[T_K(2C+2R)+K]` | source and executable probe | deterministic estimate | depth fallback 2; per-K full fill/drain; uncalibrated |
| pinned OS cycles are `T_M T_N[K+Σceil(k_q/4)]` | source and executable probe | deterministic estimate | ad hoc extra term, not measured bandwidth |
| pinned RS cycles are `T_M T_N[T_K(C+1+R)+K]` | source and executable probe | deterministic estimate | shape-independent nominal overhead; uncalibrated |
| pinned ranking proves OS physically fastest | hard-coded formulas structurally force ordering | rejected | only formula ranking; no realistic traffic/area/frequency model |
| existing dataflow sweep executes three plug-ins | core/global selection audit | rejected | its three core executions remain WS |
| existing sweep formulas reproduce pinned timing | equation comparison | rejected | it omits K-tile fill/drain multiplicity and OS per-K overhead |
| plug-in tile/FLOP fields are lifetime totals | source and probe | rejected | fields are consumed and reset after each `tu_mma()` |
| plug-in total cycles are per-call | source and delta probe | rejected | field accumulates globally across calls/reinitialization |
| configured pipeline depth drives WS/RS formulas | conversion and plug-in-state trace | rejected | parsed depth is dropped, compile-time descriptor depth is ignored, fallback is 2 |
| parallel perf counters classify selected dataflow | cycle-model producer and diff/merge trace | rejected | producer hard-codes WS, RS storage is absent, and diff/merge omit both buckets |
| DMA+MMA totals can be added | wrapper/legacy-engine audit carried forward | rejected | W/A/store cycles land in `g_tu_dma` and add zero to `g_tu.estimated_cycles`; O-load is separate |

## Exact audited results

For runtime geometry 4×8:

| Shape M×N×K | Plug-in invocations | Useful operations | WS cycles | OS cycles | RS cycles | Normal output |
|---|---:|---:|---:|---:|---:|---|
| 2×3×2 | 1 | 24 | 26 | 3 | 15 | bitwise equal |
| 9×10×9 | 12 | 1,620 | 342 | 72 | 210 | bitwise equal |
| 5×17×19 | 18 | 3,230 | 546 | 144 | 348 | bitwise equal |

These are MMA-only deterministic estimates at the pinned revision. No clock, physical traffic, overlap, or calibration is implied.

## Terminology

- **Dataflow:** a mapping of computation and data movement across space, time, and storage.
- **Stationary:** retained at a named storage/compute level over a stated reuse interval; never an absolute property.
- **Functional equivalence:** equal numerical output under a defined input domain and accumulation order.
- **Logical dataflow:** intended assignment of stationary and streamed values, independent of whether transfers execute in the model.
- **Physical schedule:** timed loads, transfers, broadcasts, MACs, reductions, stalls, and writes on named resources.
- **Traffic event:** a read, write, transfer, multicast, or reduction at a stated memory/network boundary.
- **Plug-in:** registry object implementing the common tile callback and timing hooks.
- **Cycle estimate:** source-defined deterministic counter, not host elapsed time or calibrated hardware latency.

## Primary literature claim scopes

- **[KUN82]:** regular local communication motivates systolic organization; it does not validate Tusim's WS equation.
- **[CHE16]:** row-stationary mappings target convolutional reuse across weights, activations, and partial sums; Tusim's GEMM-named RS plug-in does not reproduce Eyeriss movement or energy evidence.
- **[PAR19]:** workload, architecture, mapping, and constraints should be separate; a plug-in enum alone is not a mapping model.
- **[KWO19]:** data-centric mappings can support reuse/performance/cost analysis when directives and resources are explicit; that fidelity does not transfer to Tusim.
- **[SAM18]:** configurable systolic simulation motivates dataflow-sensitive traffic/timing audits; SCALE-Sim's fidelity does not transfer.
- **[WAT09]:** bandwidth claims require a named byte boundary and operational intensity; OS's constant overhead is not a Roofline analysis.

## Open development questions

1. How should dataflow selection propagate through canonical config, runtime config, global state, cores, DPI, command queue, and compiler lowering?
2. Should unsupported IDs return an error without mutating selection?
3. What minimal movement-event model would discriminate reuse while remaining useful for pre-spec exploration?
4. Should logical mapping, functional arithmetic, timing, and traffic be separate plug-in interfaces?
5. How should valid edge extents and K-tile persistence alter fill/drain?
6. What public per-core snapshot/reset contract should replace mixed cumulative/scratch plug-in fields?
7. How should RS represent convolution dimensions rather than inheriting a generic GEMM loop and Eyeriss name?
8. Which storage, network, frequency, and area assumptions are needed for a nontrivial WS/OS/RS Pareto comparison?
9. How should the existing sweep be corrected and made discriminating?
10. How should DMA and MMA cycle state be unified before any end-to-end timing report?
