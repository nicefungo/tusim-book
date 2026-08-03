# Chapter 6 — PE Arrays, MMA Semantics, and Tiling

> **Edition scope.** This chapter describes Tusim at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. The direct global MMA path is a functional matrix implementation with deterministic accounting. It does not simulate values moving cycle by cycle through physical PEs.
>
> **Status.** Live source audit, enforced geometry derivation, isolated clean build, focused tests, and the chapter probe are complete for this first draft.

## Learning objectives

After this chapter, you should be able to:

1. state Tusim's row-major `O += W × A` contract without transposing `M`, `N`, or `K`;
2. derive the current `R × C × C` tile decomposition and distinguish valid edge work from configured tile capacity;
3. interpret tile, operation, and cycle counters without calling them measured hardware utilization;
4. compare PE geometries for a workload while keeping throughput, occupancy, memory, area, frequency, and model fidelity separate;
5. calculate W-, A-, and O-buffer requirements, including the in-place FP16-to-FP32 bias expansion;
6. identify where runtime geometry is effective, where pipeline depth is not, and where historical exploration formulas differ from the pinned executable path;
7. design architecture-sensitive correctness and accounting tests for array shape and tiling.

## Prerequisite graph

```text
Chapter 1: workload shape, operations, utilization
                   |
                   v
Chapter 4: requested geometry -> active runtime state
                   |
                   v
Chapter 5: g_tu ownership, errors, and counters
                   |
                   v
matrix orientation -> tile envelope -> edge work
                   |                    |
                   v                    v
       capacity and bias       estimated cycles
                   \                    /
                    v                  v
              geometry trade-offs
                        |
                        v
          Chapter 7: pluggable dataflows
```

## Opening architecture question: when is a larger array actually better?

A compiler has one `4 × 32 × 16` matrix multiplication and two candidate arrays. Both contain 64 PEs: one is `8 × 8`, the other `4 × 16`. Which should it target?

PE count alone cannot answer. In Tusim's current mapping, array rows bound the M tile, array columns bound both the N tile and K tile. The `4 × 16` geometry matches all three dimensions of this workload: it uses two tiles. The `8 × 8` geometry uses eight tiles because half its rows are outside the workload and both N and K require more partitions. The Chapter 6 probe reproduces 112 versus 320 MMA-only estimated cycles and an analytical slot-utilization proxy of 100% versus 50%.

That does not prove the `4 × 16` hardware would be superior. A long array may require different wiring, banking, multicast, timing closure, placement, and compiler packing. Tusim's functional loop models none of those physical costs. The defensible conclusion is narrower: **under the pinned mapping and counter equations, workload–geometry alignment changes tile count and deterministic estimates even when PE count is fixed**.

This distinction—executable contract first, hardware conclusion second—is the organizing principle of the chapter.

## 6.1 Matrix contract and notation

Let:

- `W` be an M-by-K weight matrix;
- `A` be a K-by-N activation matrix;
- `O` be an M-by-N FP32 accumulator matrix.

Tusim's public contract is:

```text
O[M,N] += W[M,K] × A[K,N]
```

Elementwise:

```text
O[m,n] <- O[m,n] + sum over k of W[m,k] A[k,n]
```

All three matrices are row-major in their logical dimensions. The direct API takes byte offsets into separate W, A, and O SRAM regions; it does not take host pointers or strides. The source forms:

```text
W[(m) K + k]
A[(k) N + n]
O[(m) N + n]
```

This orientation contradicts `docs/TU_CMODEL.md`, which describes `O[N][M]` and assigns M to output columns. For this edition, the public header, executable indices, nonsymmetric probe, and golden oracle take precedence over that stale prose.

The distinction between mathematics and storage names matters. `W`, `A`, and `O` are not generic matrix letters in this API; they also identify physically separate model regions. A compiler that lowers a framework GEMM with transposition flags must materialize the layout that this contract expects or use a different implementation path. Tusim's direct call has no transpose operand.

### Accumulate means accumulate

Without bias, `tu_mma()` does not clear O. Each K tile computes a temporary FP32 sum and adds it to the existing accumulator. Calling the same MMA twice doubles the matrix-product contribution. This behavior supports reduction across K tiles, but it also creates a caller obligation: initialize O before the first accumulation.

The chapter probe uses nonsymmetric matrices so a transpose cannot accidentally pass:

```text
W = [1 2]      A = [5  6  7]
    [3 4]          [8  9 10]

W A = [21 24 27]
      [47 54 61]
```

A seeded O is preserved and incremented; a second call adds the same product again. This is stronger orientation evidence than an identity or all-ones case.

### MACs, operations, and the counter name

One useful multiply-accumulate contributes one product and one addition. This book therefore counts:

```text
useful MACs       = M N K
useful operations = 2 M N K
```

The dispatcher increments `total_mma_flops` by two per valid MAC. `tu_print_stats()` prints that field as “MMA FLOPS” and then annotates it “FP16 MACs.” The two descriptions are inconsistent. For this edition, interpret the field as a source-defined **two-operations-per-valid-MAC count**. It is not a count of padded array slots, elapsed floating-point instructions on the host, or measured hardware work.

## 6.2 From an array to a tile envelope

A rectangular PE array has runtime geometry:

```text
R = pe_rows
C = pe_cols
```

The pinned direct path gives the dispatcher tile extents:

```text
TILE_M = R
TILE_N = C
TILE_K = C
```

Thus array columns serve two roles: output-column parallelism and reduction depth per plug-in invocation. Tile K is not an independent architecture parameter.

For positive dimensions and geometry:

```text
T_M = ceil(M / R)
T_N = ceil(N / C)
T_K = ceil(K / C)
T   = T_M T_N T_K
```

The dispatcher traverses M tiles, then N tiles, then K tiles. At each boundary it computes valid counts:

```text
m_count = min(R, M - m_start)
n_count = min(C, N - n_start)
k_count = min(C, K - k_start)
```

Only those valid ranges enter the scalar functional loops. An edge tile therefore preserves numerical correctness without explicit zero padding. The model does not execute multiplications for invalid padded elements.

### Logical tiling is not operand streaming

This decomposition tiles computation, not residency. Before dispatch, `tu_mma()` obtains pointers to complete row-major W, A, and O images. It checks byte extents for the full logical matrices. The dispatcher never reloads an operand tile, changes a base address, spills a partial sum, or packs a strided slice.

This produces two different meanings of “tile”:

1. **internal compute tile:** a software loop partition within already resident operands;
2. **external memory tile:** a compiler/runtime-managed subproblem loaded into limited SRAM.

Tusim implements the first in `tu_mma()`. A compiler must implement the second when the full operands do not fit.

## 6.3 Source map and evidence ladder

The live implementation is concentrated in:

| Source | Role in this chapter |
|---|---|
| `tu_cmodel/tu_cmodel.[ch]` | public MMA contract, offsets, bounds requests, bias expansion, runtime geometry, counters |
| `tu_cmodel/compute/dataflow/dataflow_dispatcher.c` | M/N/K decomposition, edge counts, plug-in calls, operation and cycle aggregation |
| `tu_cmodel/compute/dataflow/weight_stationary.c` | active default numerical loops and WS cycle helpers |
| `tu_cmodel/tu_config.h` | compile defaults: 16×16, pipeline depth 2, 128/64/64 KiB W/A/O |
| `tests/test_cmodel.c` | 19 focused tests: arbitrary geometry, known values, bias, edge tiles |
| `tests/test_dataflow.c` | nine registry, equivalence, switch, and edge tests |
| `tests/test_random.c` | broader randomized and prime-shape tests in a separate target |
| `docs/parametric-pe-array.md` | historical intent and earlier test inventory |
| exploration reports and `scripts/sweep_aspect_ratio.py` | historical analytical questions, not accepted current runtime results |

The durable source/claim ledger is [`notes/chapter-06-source-and-claim-ledger.md`](../../notes/chapter-06-source-and-claim-ledger.md). Exact commands, hashes, output, and derivations are in the [Chapter 6 audit](../../experiments/ch06-geometry-tiling-audit-2026-07-25.md).

The evidence ladder for geometry is:

```text
runtime field exists
  -> copied into g_tu.rt_cfg
  -> read by tu_mma
  -> passed as tile extents
  -> changes tile counters/cycles on a discriminating shape
  -> preserves the numerical result
```

Chapter 4 established the first four steps. Chapter 6 closes the behavioral step with cases that cannot produce the same tile count under both geometries.

## 6.4 Implementation walk-through

The direct path performs nine material steps.

1. Check that global state is initialized.
2. Read `pe_rows` and `pe_cols` from `g_tu.rt_cfg`.
3. Increment the MMA-call counter.
4. Calculate whole-matrix byte requirements: `2MK`, `2KN`, and `4MN`.
5. Report bounds errors if an extent exceeds its SRAM region.
6. Form typed pointers into W, A, and O regions.
7. If bias is enabled, expand packed FP16 values in O to FP32 in reverse order.
8. Dispatch `R × C × C` tiles through the selected plug-in.
9. Accumulate plug-in tiles, operations, and estimated cycles into global counters.

The reverse bias traversal is necessary because source and destination overlap. Forward expansion would overwrite packed FP16 elements that had not yet been read.

### Functional execution inside the WS plug-in

For one tile, the active default plug-in loops over valid `m_count`, `n_count`, and `k_count`. It converts each FP16 operand to a host `float`, forms products, accumulates a local FP32 partial sum, and adds that partial sum to O.

This code establishes numerical semantics. It does not instantiate `R × C` PE objects, route values between neighbors, advance a systolic wavefront, arbitrate SRAM requests per MAC, or track individual idle lanes. “Weight-stationary” names the selected plug-in contract and its analytical helpers; it is not evidence of a cycle-by-cycle hardware implementation.

The plug-ins also duplicate a local FP16 converter instead of calling the canonical precision implementation. Independent review found a subnormal defect, and the revised probe reproduced it: raw binary16 `0x0001` is correctly `2^-24` through `fp16_to_fp32()`, but the WS MMA path produces `2^-14`, a factor of 1,024 too large. Existing subnormal tests exercise the canonical converter, not this MMA-local copy. Normal finite values used elsewhere in the chapter still pass, but “FP16 input semantics” must not be generalized to correct subnormal handling.

### Edge work and accounting

For each invocation, the dispatcher adds:

```text
2 m_count n_count k_count
```

operations. Summed over all tiles, this is exactly `2MNK`. Padded slots are absent from the counter. This is why the existing operation count cannot be divided by itself to infer occupancy: a denominator representing available slots must be supplied separately.

## 6.5 A reproducible geometry audit

The audit builds an untouched `git archive` extraction, not the Tusim checkout. It checks eight source hashes, performs a clean static-library build, runs focused suites, compiles [`ch06_geometry_probe.c`](../../experiments/ch06_geometry_probe.c), and compares executable counters against [`ch06_tiling_audit.py`](../../experiments/ch06_tiling_audit.py).

Observed gates were:

```text
source hashes:  8/8 pass
test-cmodel:   19/19 pass
test-dataflow:  9/9 pass
test-golden:   11/11 pass
test-random:    quick mode, 9/9 categories pass
chapter probe: PASS
```

The probe covers:

- nonsymmetric matrix orientation;
- seeded and repeated accumulation;
- packed FP16 bias expansion;
- edge tiles in M, N, and K;
- non-square and square geometries;
- equal-PE-count aspect ratios;
- a workload on which a larger array has lower slot utilization;
- exact tile, operation, and MMA-only cycle counters.

### Worked derivation: 9 × 9 × 9 on 4 × 8

For `M=N=K=9`, `R=4`, and `C=8`:

```text
T_M = ceil(9/4) = 3
T_N = ceil(9/8) = 2
T_K = ceil(9/8) = 2
tiles = 3 * 2 * 2 = 12
useful MACs = 9 * 9 * 9 = 729
operations = 1458
```

The executable counter reports 12 tiles and the output remains exactly 9 for all-one inputs. A `16 × 16` geometry reports one tile and the same output. Numerical equivalence alone would not distinguish the two architectures; the tile counter does.

## 6.6 Defining edge utilization without overclaiming

“Utilization” is incomplete until its numerator, denominator, and interval are named. Tusim does not expose a direct active-PE occupancy counter for this path. The chapter therefore defines an analytical **slot-utilization proxy**.

Each configured tile envelope contains `R C` PEs over `C` reduction slots, or `R C²` MAC slots. Across all internal tiles:

```text
U_slot = M N K / (T_M T_N T_K R C²)
```

It is useful to factor this into two named quantities:

```text
U_output = M N / [(T_M R)(T_N C)]
U_K      = K / (T_K C)
U_slot   = U_output U_K
```

`U_output` captures output-edge occupancy; `U_K` captures reduction-slot occupancy. Neither includes pipeline or memory idleness. This factorization prevents an N/K-coupled wide array from hiding the cause of its waste behind one percentage.

This metric answers: *what fraction of the configured output-lane and reduction-slot envelope corresponds to valid matrix work?* It does not answer:

- how many physical PEs toggle in each hardware cycle;
- whether zero padding is executed;
- how fill and drain overlap;
- whether memory starvation idles the array;
- how clock gating changes energy;
- whether the implementation sustains one MAC per PE per cycle.

The functional model skips invalid iterations, while the denominator imagines a fully provisioned tile envelope. The metric is therefore analytical, even when its dimensions and tile count are runtime-confirmed.

### Why a remainder can be expensive

If M is just above a multiple of R, the final tile row may use few valid rows. The same applies to N and K. Because the current K tile equals C, a wider array can improve N coverage while worsening K-edge waste. Geometry selection is a three-dimensional mapping decision, not just alignment of the output matrix.

For `9 × 9 × 8`:

| Geometry | Tiles | Slot utilization |
|---|---:|---:|
| 8×8 | 4 | 31.6406% |
| 16×16 | 1 | 15.8203% |

The larger array halves this occupancy proxy. Yet its pinned MMA-only estimate is 72 cycles versus 160. Lower utilization does not imply higher latency: one larger underfilled tile can still replace several smaller tiles. It may, however, imply poorer throughput per PE, area efficiency, or energy efficiency—questions Tusim cannot settle without additional models.

There is also a pinned regime where larger is both less occupied and slower. For an exact `16³` workload, all three geometries use one tile, but fill/drain is charged using the full configured dimensions:

| Geometry | Output occupancy | K occupancy | Slot utilization | MMA-only cycles |
|---|---:|---:|---:|---:|
| 16×16 | 100% | 100% | 100% | 80 |
| 32×32 | 25% | 50% | 12.5% | 144 |
| 64×64 | 6.25% | 25% | 1.5625% | 272 |

This is exact behavior of the pinned estimate, not a claim that every physical oversized array must run slower. A hardware scheduler could gate unused structure, use a smaller logical tile, or overlap wavefronts differently.

## 6.7 Aspect ratio and workload matching

Array aspect ratio determines which workload dimensions receive capacity.

For `4 × 32 × 16`, compare two 64-PE arrays:

| Geometry | Tile shape | Tiles | Slot utilization | Pinned MMA-only cycles |
|---|---|---:|---:|---:|
| 8×8 | 8×8×8 | 8 | 50% | 320 |
| 4×16 | 4×16×16 | 2 | 100% | 112 |

The wide geometry matches M exactly and covers twice as much N and K per tile. Under this mapping it is the clear model winner.

A hardware recommendation must add costs omitted by the table:

| Dimension | Wider 4×16 may gain | Wider 4×16 may cost |
|---|---|---|
| throughput/latency | fewer Tusim tiles for wide N and K | long-M workloads may need more tile rows |
| utilization | better fit for short-wide outputs | poor fit for tall-narrow outputs |
| traffic | fewer externally scheduled tiles may improve reuse | current direct path does not model tile traffic |
| area/power | same PE count in this comparison | longer broadcast/reduction paths and wiring may cost power/area |
| frequency | no benefit represented | timing closure may be harder; Tusim holds frequency outside geometry |
| compiler | regular target-specific packing | more shape-sensitive mapping choices and transposes |
| verification | fewer model invocations | more aspect-ratio corner cases and physical topology checks |

No single aspect ratio is optimal across all layers. A pre-spec exploration should retain distinct plausible geometries and identify their workload regimes rather than deleting every option except one local winner.

## 6.8 What the cycle estimate actually counts

The active default path calls the plug-in once for every M/N/K tile. For each call, the dispatcher adds plug-in fill, compute, and drain estimates.

The weight-stationary helpers use pipeline depth `p=2` in the pinned execution. They charge:

```text
fill  = p C
compute = k_count
drain = p R
```

Because fill and drain are inside the K-tile loop, summing all K tiles gives:

```text
cycles_WS = T_M T_N [T_K p(C+R) + K]
```

At the pinned fallback `p=2`:

```text
cycles_WS = T_M T_N [T_K(2C+2R) + K]
```

For `9³` on `4×8`:

```text
cycles = 3 * 2 * [2*(16+8) + 9]
       = 6 * 57
       = 342
```

The executable probe reports 342 MMA-only cycles. DMA cycles are excluded by sampling `estimated_cycles` immediately before and after `tu_mma()`.

That exclusion is not merely experimental convenience. Independent source review found that the legacy DMA engine records estimates in process-global `g_tu_dma`, while direct wrappers read and clear the separate `g_tu.dma.estimated_cycles`. Consequently W/A/store transfers generally do not enter `g_tu.estimated_cycles` through those wrappers; `tu_dma_load_o()` uses yet another direct `ceil(bytes/32)` term. A final `g_tu.estimated_cycles` value is therefore not a coherent end-to-end DMA-plus-MMA latency domain in this snapshot.

### Pipeline depth is not an effective runtime knob here

The full configuration structure contains `pe_pipeline_depth`, but `tu_runtime_config_t` does not. The global MMA call passes compile-time `TU_PE_PIPELINE_DEPTH` to the dispatcher. The dispatcher stores that value in an operation descriptor, but the WS fill/drain helpers read separate plug-in implementation state. That state is zero-initialized and never populated from the descriptor, so the helpers fall back to 2.

The default compile-time constant is also 2, which masks the disconnected path. A report that sweeps the full-config field analytically does not demonstrate a runtime effect in global MMA.

### Why deeper pipelines are still an architecture question

In hardware, deeper arithmetic pipelines may raise achievable frequency while increasing fill/drain latency, registers, bypass complexity, and verification state. Comparing only cycles at a fixed 1 GHz penalizes depth without modeling its possible frequency benefit. Comparing only peak frequency ignores short-tile overhead.

Tusim currently models neither frequency as a function of depth nor an effective depth sweep on this path. The safe use of pipeline depth in Chapter 6 is therefore:

- **executable:** the pinned estimate behaves as if WS depth were 2;
- **analytical:** formulas can ask “what if p changed?”;
- **future work:** connect p to executable state and a calibrated or explicitly estimated frequency/area model.

### Historical formula drift

Several exploration reports charge fill and drain once per spatial output tile—or even once per tile row/column globally—rather than once per K tile. One report explicitly identifies the dispatcher discrepancy. `scripts/sweep_aspect_ratio.py` also omits K-tile multiplicity from its tile count and uses a two-byte O traffic term despite FP32 accumulators.

These artifacts remain useful records of architecture questions. They are **historical analytical models**, not current executable evidence. Their tables must not be combined with pinned counters unless the formula, byte convention, and capacity assumptions are reconciled first.

## 6.9 SRAM capacity and the bias trap

For zero offsets, whole-operand requirements are:

```text
W bytes = 2 M K
A bytes = 2 K N
O bytes = 4 M N
```

With offsets:

```text
w_offset + 2 M K <= W capacity
a_offset + 2 K N <= A capacity
o_offset + 4 M N <= O capacity
```

The default capacities are:

| Region | Capacity |
|---|---:|
| W | 128 KiB |
| A | 64 KiB |
| O | 64 KiB |

A `128³` call requires 32 KiB W, 32 KiB A, and exactly 64 KiB O. It fits. A `256³` call requires 128 KiB W, 128 KiB A, and 256 KiB O. W fits exactly; A and O do not.

The architecture overview comment in `tu_cmodel.h` says output is FP16 and rounded on store, but the direct `tu_dma_store_o()` path copies bytes from the FP32 O region. FP32-to-FP16 conversion is a separate helper, not an implicit part of direct store. Capacity and traffic analysis for this API must therefore use four O bytes per element unless the caller explicitly invokes a conversion path.

Internal `16×16×16` PE tiling does not rescue the `256³` call. The caller must form smaller resident subproblems. For example, M blocks of 64 and N blocks of 128 with K=256 require 32 KiB W, 64 KiB A, and 32 KiB O per block. But N slicing makes each A block strided in the original K-by-256 layout, so a compiler must pack it or support strides. Output placement and cross-block reuse also become explicit scheduling decisions.

### Bias is an image, not a broadcast vector

When `has_bias=true`, Tusim interprets the bytes at `o_offset` as `M N` packed FP16 values. It expands every element in place to FP32, then accumulates the matrix product. It does not broadcast one N-element bias vector across M rows.

Therefore:

- bias payload loaded: `2MN` bytes;
- accumulator extent required: `4MN` bytes;
- a framework's per-output-channel bias must be expanded to M-by-N by the caller;
- reverse traversal preserves overlapping source data during expansion.

A capacity check based only on packed bias bytes is wrong. The final FP32 image controls O-buffer fit.

### Bounds reporting is not safe rejection

As established in Chapter 5, the bounds helper records an error and returns to its caller, but `tu_mma()` continues pointer formation and execution. The chapter audit exercises fitting and exact-boundary derivations only. It does not use an expected warning as evidence of safe overflow handling.

Other limit hazards include zero runtime rows or columns, 32-bit byte-product and offset-sum overflow, and extreme `uint16_t` loop arithmetic. The declared types are not a promise that every representable value is safe.

Offsets are byte-granular but are cast directly to typed FP16 or FP32 pointers. Odd W/A offsets and O offsets not divisible by four can therefore create misaligned typed accesses and undefined C behavior even when the byte extent fits. Full-file configuration validation limits parsed PE dimensions to 1–1024, but direct `tu_init_with_config()` bypasses that validation.

## 6.10 Choosing a geometry: regimes and costs

A useful design review separates at least five objectives.

| Objective | Favor larger/wider arrays when… | Favor smaller/narrower arrays when… |
|---|---|---|
| absolute latency | large tiles replace many sequential model invocations | edges dominate or memory cannot feed added PEs |
| throughput per area | workload alignment keeps lanes active and frequency holds | extra lanes are usually idle or routing dominates |
| energy | fewer control/tile events outweigh extra wiring and leakage | fine-grain gating makes compact arrays cheaper |
| compiler simplicity | common dimensions divide geometry cleanly | model portfolio contains irregular and dynamic shapes |
| verification risk | topology remains regular and bounded | very wide/tall fabrics add timing, multicast, and corner states |

Three practical regimes follow.

1. **Small or irregular GEMMs.** Edge occupancy can collapse as geometry grows. Smaller arrays may offer better throughput per PE and lower area/power, even if a larger array finishes one isolated call in fewer estimated cycles.
2. **Large aligned GEMMs.** Larger arrays can reduce tile count and improve absolute latency, provided storage and bandwidth scale. Tusim's current whole-operand constraints may block the very workloads intended to amortize the array.
3. **Shape-skewed GEMMs.** A rectangular array can outperform a square array with equal PE count under the pinned `R×C×C` mapping. The winning orientation depends on M, N, K, packing, and physical communication.

The model cannot convert slot utilization directly into energy or silicon value. A candidate should be carried forward when it serves a materially distinct workload or implementation regime, with its costs recorded.

## 6.11 Verification strategy

A geometry test should be discriminating, not merely correct.

### Numerical tests

Use:

- nonsymmetric values to expose transposes;
- seeded O to expose overwrite versus accumulate;
- repeated calls to expose reduction behavior;
- prime or boundary dimensions to exercise all edge axes;
- packed, nonuniform bias to expose expansion order and layout;
- a high-precision oracle with named tolerance for non-integer data.

### Architecture-sensitive tests

For two geometries, choose dimensions that cross one or more tile boundaries. Assert:

- active geometry after initialization;
- predicted tile count;
- identical output;
- operation count `2MNK`;
- source-reconstructed cycle delta;
- separately derived slot-utilization denominator.

An `8×8` MMA on an `8×8` matrix is weak geometry evidence because many larger arrays also produce one correct tile. The `9×9×9` 4×8-versus-16×16 case is discriminating: 12 versus one tile.

### Capacity tests

Test exact fit and one-past-boundary only after the API has failure-atomic rejection. In the pinned edition, one-past cases can proceed to unsafe memory access. Prefer arithmetic/source audits or an isolated sanitizer experiment that treats the crash as a defect, not a successful negative test.

### Existing coverage

`test_cmodel` covers seven geometry/shape configurations, known values, bias, and a `7×5×9` edge case; it passed 19/19. `test_dataflow` covers WS/OS/RS identity and equivalence plus a `31×31×17` edge case; it passed 9/9. `test_golden` passed 11/11, including edge, non-square, prime, scalar, vector, bias, and 50 bulk-random cases. Despite comments suggesting committed JSON references, this executable builds and compares an in-process FP32 oracle; it does not parse those JSON fixtures. `test_random` includes prime dimensions and many randomized cases, but it is a separate `test-random` target and is not included in aggregate `make test`. Its quick mode passed all nine categories, including 500/500 FP16 MMA and 200/200 BF16 MMA iterations. This is not evidence that the full non-quick target ran. Aggregate `make test` excludes all sweeps and random testing; `test-quick` is narrower still, and geometry sweeps are not CI gates.

## Fidelity box — what “PE array” means in this edition

> **Executable functional model:** row-major FP16-input/FP32-accumulator MMA, edge-safe numerical loops for fitting operands, bias expansion, runtime geometry consumption, tile/operation counters.
>
> **Numerical exception:** MMA-local WS/OS/RS converters misdecode FP16 subnormals; normal finite probe values pass, but arbitrary binary16 correctness is not established.
>
> **Deterministic estimate:** sequential sum of source-defined plug-in fill, compute, and drain terms. The pinned WS estimate uses effective depth 2 and charges fill/drain per K tile. Direct DMA and MMA estimates are not integrated into one coherent cycle domain.
>
> **Analytical:** slot utilization, candidate physical occupancy, external SRAM tiling, area/frequency/energy trade-offs.
>
> **Not established:** PE-level wavefront timing, backpressure, inter-PE routing, sustained issue, memory/compute overlap, clock frequency, area, energy, RTL equivalence, or silicon calibration.

The label `weight_stationary` does not upgrade a scalar loop into a spatial timing model. The enum and source comments describe intended organization; evidence must still show which physical effects are represented.

## 6.12 Common failure modes

1. **Transposing the API mentally.** Framework GEMM notation may name operands differently; trace row-major indices.
2. **Clearing O implicitly.** `has_bias=false` means accumulate into existing FP32 O, not initialize it.
3. **Treating bias as N-element broadcast.** Tusim expects an M-by-N packed FP16 image.
4. **Using PE count without aspect ratio.** Equal counts can produce different M/N/K partitions.
5. **Ignoring K edges.** Current tile K equals PE columns; N-friendly width may waste reduction slots.
6. **Calling useful-operation count utilization.** It has no available-slot or elapsed-cycle denominator.
7. **Equating lower utilization with higher latency.** A larger underfilled array may still use fewer tiles.
8. **Assuming internal tiling solves SRAM fit.** Full operand images must be resident.
9. **Sweeping an inert pipeline field.** Analytical variation is not runtime-effect evidence.
10. **Combining historical and current cycle domains.** Reconcile per-K versus per-spatial fill/drain first.
11. **Trusting a warning-only bounds check.** The pinned call can continue after reporting overflow.
12. **Converting cycles to TOPS without a clock contract.** Frequency is not derived from geometry or depth.
13. **Assuming every FP16 bit pattern uses canonical conversion.** MMA-local WS/OS/RS converters mishandle subnormals.
14. **Using byte-fitting but misaligned offsets.** Typed pointer casts impose alignment obligations absent from the API checks.
15. **Adding DMA and MMA counters as one latency.** The direct wrappers and DMA engine do not update one coherent cycle object.

## 6.13 Development implications

The audit turns several blind spots into concrete design questions.

1. Decouple tile K from PE columns so mapping can represent different reduction buffering and array topologies.
2. Define whether fill/drain belongs to each K tile, each spatial tile, or an explicit persistent pipeline state.
3. Propagate pipeline depth into executable plug-in state and pair it with an explicit frequency/area assumption.
4. Return status before pointer arithmetic or counter success accounting on invalid dimensions and capacities.
5. Add an operand-tile API with strides, packing contracts, partial-sum lifetime, reload traffic, and spill accounting.
6. Separate counters for useful MACs, available MAC slots, active cycles, padded work, and traffic.
7. Replace or version historical sweep scripts against enforced source hashes and current byte/cycle formulas.
8. Add geometry tests to an aggregate gate and keep broad randomized coverage visible rather than hiding it behind a separate target.

These are research and engineering questions, not silent corrections to the pinned edition. Chapter 7 will first audit how WS, OS, and RS share the dispatcher and where their functional equivalence diverges from their performance estimates.

## Summary

- Tusim executes row-major `O[M,N] += W[M,K] × A[K,N]` with FP16 inputs and FP32 accumulation.
- Runtime `R×C` geometry creates `R×C×C` internal tiles; K depth is coupled to PE columns.
- Edge loops compute only valid elements, and the useful-operation counter sums to `2MNK`.
- Slot utilization requires an explicit analytical denominator; it is not a built-in counter.
- Aspect ratio matters: equal PE counts can yield very different tiling for the same M/N/K shape.
- A larger array can have lower slot utilization and still lower estimated latency, so utilization and latency must not be conflated.
- The pinned WS estimate is a deterministic sequential formula with effective depth 2 and per-K-tile fill/drain, not calibrated hardware timing.
- Full W, A, and FP32 O images must fit SRAM. Internal compute tiling does not implement operand streaming.
- Bias is an M-by-N packed FP16 image expanded in place to a `4MN`-byte FP32 accumulator image.
- Historical sweeps preserve useful questions but use formulas that do not uniformly match the pinned dispatcher.
- MMA-local FP16 conversion is numerically wrong for subnormals; raw `0x0001` reproduced a 1,024× error.
- Direct DMA and MMA estimates do not form one coherent end-to-end cycle domain.

## Review questions

1. For M=23, N=35, K=17 on R=8, C=16, derive `T_M`, `T_N`, `T_K`, total tiles, useful MACs, useful operations, and `U_slot`.
2. Why does an all-ones test fail to prove matrix orientation as strongly as the nonsymmetric Chapter 6 probe?
3. What initial O contents are required when `has_bias=false`? What changes when it is true?
4. Why is `total_mma_flops / (2MNK) = 1` not a utilization measurement?
5. Under the pinned WS path, where is fill/drain charged? How does that differ from several historical reports?
6. Why can a 16×16 array have lower slot utilization but lower estimated latency than an 8×8 array?
7. Which whole-operand inequalities must hold for nonzero offsets?
8. Why can a packed bias load fit while the MMA result does not?
9. What physical costs could make a model-winning 4×16 array lose to 8×8 hardware?
10. Which evidence would be required before calling a pipeline-depth sweep calibrated?

## Design exercises

1. Build a geometry selector that minimizes tile count subject to W/A/O capacity and a maximum aspect ratio. Report Pareto candidates rather than one unqualified optimum.
2. Extend the slot metric into separate M-edge, N-edge, and K-edge efficiencies. Show how their product relates to `U_slot`.
3. Design an external tiling schedule for `256³` under default capacities. Include packing, accumulator initialization, A reuse, output placement, and traffic bytes.
4. Specify a failure-atomic MMA API for invalid dimensions, integer overflow, alignment, and capacity. Define which counters may change on rejection.
5. Propose two pipeline models: per-K-tile refill and persistent spatial-tile pipeline. Give discriminating workloads and expected counter differences.
6. Create a test matrix that distinguishes `4×16`, `8×8`, and `16×4` using numerical equality plus tile and cycle assertions.

## Primary references

1. H. T. Kung, “Why Systolic Architectures?,” *Computer*, 1982. DOI: [10.1109/MC.1982.1653825](https://doi.org/10.1109/MC.1982.1653825). Regular local-communication arrays motivate the organization; the paper does not validate Tusim's cycle equation.
2. Norman P. Jouppi et al., “In-Datacenter Performance Analysis of a Tensor Processing Unit,” ISCA 2017. DOI: [10.1145/3079856.3080246](https://doi.org/10.1145/3079856.3080246). Use for workload, storage, and software effects on achieved matrix-unit performance, not numerical transfer to Tusim.
3. Yu-Hsin Chen, Joel Emer, and Vivienne Sze, “Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,” ISCA 2016. DOI: [10.1109/ISCA.2016.40](https://doi.org/10.1109/ISCA.2016.40). Use for data-movement and reuse reasoning; Chapter 7 handles Tusim's dataflow implementations.
4. Ananda Samajdar et al., “SCALE-Sim: Systolic CNN Accelerator Simulator,” arXiv:1811.02883v2, 2018. DOI: [10.48550/arXiv.1811.02883](https://doi.org/10.48550/arXiv.1811.02883). Use for configurable array/mapping simulation context, not fidelity transfer.
5. Angshuman Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019. DOI: [10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042). Use for separating workload, architecture, mapping, and constraints.
6. Hyoukjun Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” MICRO 2019. DOI: [10.1145/3352460.3358252](https://doi.org/10.1145/3352460.3358252). Use for mapping/reuse analysis with explicit model boundaries.
7. [Verified foundation bibliography](../../references/foundations.md).
8. [Chapter 6 executable audit](../../experiments/ch06-geometry-tiling-audit-2026-07-25.md).
