# Chapter 6 Source and Claim Ledger

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Audit:** [`../experiments/ch06-geometry-tiling-audit-2026-07-25.md`](../experiments/ch06-geometry-tiling-audit-2026-07-25.md)
- **Probe:** [`../experiments/ch06_geometry_probe.c`](../experiments/ch06_geometry_probe.c)
- **Enforced derivation:** [`../experiments/ch06_tiling_audit.py`](../experiments/ch06_tiling_audit.py)

## Reader decision

Given a workload shape and candidate PE geometry, determine what Tusim executes, what its counters mean, whether operands fit, and which utilization/timing conclusions are safe before using the result in architecture or compiler decisions.

## Source map

| Source | Evidence supplied | Caveat |
|---|---|---|
| `tu_cmodel/tu_cmodel.[ch]` | public contract, whole-operand bounds, bias expansion, runtime geometry, counters | comments contain stale 16×16 and failure-contract language |
| `compute/dataflow/dataflow_dispatcher.c` | `M/N/K` decomposition and per-tile accounting | full tile dimensions used for edge fill/drain; fill/drain inside K loop |
| `compute/dataflow/weight_stationary.c` | row-major MAC loops and WS cycle helpers | functional loops are not a spatial schedule; helper pipeline depth defaults to 2 |
| `tu_cmodel/tu_config.h` | compile defaults: 16×16, pipeline depth 2, SRAM sizes | compile constants and runtime fields have different reachability |
| `tests/test_cmodel.c` | 19 focused tests including arbitrary geometry, edge tiles, bias | mostly correctness; no slot-utilization assertion or unsafe limit tests |
| `tests/test_dataflow.c` | 9 plug-in tests including edge equivalence | mixes Chapter 7 dataflow scope; timing formulas not asserted |
| `tests/test_golden.c` and reference data | 11 tolerance-based in-process-oracle cases including irregular shapes and bias | executable does not parse committed JSON fixtures; not geometry/cycle-effect evidence |
| `tests/test_random.c` | broad randomized and prime-shape cases | separate nightly target; not in `make test`; quick mode passed, full mode not run |
| `docs/parametric-pe-array.md` | historical rationale and intended parameterization | stale API name and stronger “fully parameterized” wording than live paths support |
| `scripts/sweep_aspect_ratio.py` and exploration reports | historical analytical questions | formulas do not reproduce current dispatcher and may omit FP32 O bytes/capacity |

## Claim ledger

| Claim | Evidence | Label | Safe boundary |
|---|---|---|---|
| `O[M,N] += W[M,K] × A[K,N]`, row-major | source loops; nonsymmetric executable probe | executable functional model | FP16 W/A to FP32 accumulation; no physical PE timing claim |
| repeated MMA accumulates rather than overwrites | seeded/repeated probe | executable | caller must initialize O or use packed-bias path |
| bias is packed FP16 at O offset and expanded in reverse to FP32 | source and probe | executable | final `4MN` O extent must fit |
| tile sizes are `R × C × C` | dispatcher call from runtime `R,C` | integrated | K tile is coupled to PE columns in current implementation |
| tile count is `ceil(M/R)ceil(N/C)ceil(K/C)` | source, counters, enforced cases | executable | nonzero geometry assumed |
| useful work counter is `2MNK` “FLOPs” | dispatcher and probe | executable accounting | operation count, not MAC count; no padding work counted |
| direct O storage and `tu_dma_store_o()` are FP32 | source path and byte probe | executable | header overview's FP16-on-store statement is stale; conversion is separate |
| MMA-local FP16 subnormal conversion is wrong | source; raw `0x0001` probe gives `2^-14` instead of `2^-24` | executable defect | normal-value tests do not cover this path |
| `U_slot = MNK / (T_M T_N T_K R C²)` | explicit derivation | analytical | occupancy proxy, not runtime counter or energy model |
| 4×16 can fit 4×32×16 better than 8×8 at equal PE count | probe: 100% vs 50% slot proxy, 112 vs 320 estimated cycles | executable + analytical | fixed active WS model; ignores physical bandwidth/frequency/area layout |
| 16×16 has lower utilization than 8×8 for 9×9×8 | probe: 15.82% vs 31.64% | analytical, runtime-confirmed dimensions | 16×16 still has lower estimated cycles (72 vs 160); utilization is not latency |
| pinned WS estimate is `T_M T_N [T_K(2C+2R)+K]` | source reconstruction and probe | deterministic estimate | pipeline fallback 2; per-K fill/drain; no calibration |
| whole operands must fit W/A/O | source pointer model and enforced byte derivation | integrated/source-proven | no internal operand streaming/spilling in direct MMA |
| arbitrary runtime geometry is fully safe | contradicted by missing direct validation and integer limits | rejected | only positive, capacity-fitting practical cases demonstrated |
| historical sweep tables are current runtime measurements | scripts/reports contradict | rejected | retain as historical analytical questions only |
| direct DMA and MMA estimates form one cycle domain | contradicted by `g_tu_dma` versus `g_tu.dma` source paths | rejected | chapter reports MMA-only deltas |

## Terminology

- **PE geometry:** runtime rows `R` and columns `C` used to choose software tile extents.
- **Spatial tile:** one `M × N` output block; current dispatcher further invokes the plug-in once per K tile.
- **Edge tile:** a final tile whose valid `m_count`, `n_count`, or `k_count` is less than configured extent.
- **Useful MAC:** one valid `W×A` product accumulated into a valid output element.
- **Useful operations:** two per useful MAC under this book's multiply-plus-add convention.
- **Output-edge occupancy:** valid M-by-N outputs divided by the padded output-tile envelope.
- **K-slot occupancy:** valid reduction positions divided by the padded K-tile envelope.
- **Slot utilization:** product of output-edge and K-slot occupancy; useful MACs divided by configured PE/reduction slots in the analytical tile envelope.
- **Estimated cycles:** Tusim's deterministic source-defined count, not elapsed host time or calibrated hardware latency.

## Open development questions

1. Should tile K be independently configurable from PE columns?
2. Should fill/drain be charged per K tile, per spatial tile, or through an explicit overlap/state model?
3. How should runtime pipeline depth reach plug-in implementation state, and how should frequency trade-offs be represented?
4. Should the public API return status and stop before pointer arithmetic on capacity failure?
5. Should a compiler/runtime API expose operand-level tiling and spill/reload rather than requiring whole matrices resident?
6. Should counters separately report useful MACs, padded/available MAC slots, active cycles, and modeled traffic?
7. Which historical exploration scripts should be retired or rebuilt against an enforced pinned extractor?
8. Should all MMA plug-ins call the canonical FP16 converter, with raw-subnormal regression vectors?
9. Should byte offsets be rejected unless aligned for their operand type?
10. How should DMA engine and wrapper cycle state be unified before end-to-end latency is reported?

## Primary literature claim scopes

- **[KUN82]:** regular local-communication arrays motivate systolic organization; no Tusim cycle equation follows automatically.
- **[JOU17]:** matrix hardware and software-managed storage demonstrate workload/memory dependence of achieved performance; silicon numbers do not transfer.
- **[CHE16]:** dataflow and reuse choices affect movement and energy; Chapter 7 owns Tusim's WS/OS/RS comparison.
- **[SAM18], [PAR19], [KWO19]:** configurable mapping/model tools motivate explicit workload–architecture–mapping separation; their fidelity does not transfer to Tusim.
