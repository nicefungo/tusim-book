# Chapter 7 — Pluggable Dataflows

> **Edition scope.** This chapter describes Tusim at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. WS, OS, and RS are compiled functional plug-ins with distinct deterministic timing formulas. They are not cycle-by-cycle simulations of physical operand movement.
>
> **Status.** Live source audit, enforced formula reconstruction, isolated build, focused suites, existing-sweep challenge, fail-closed reproduction, and three independent skeptical reviews are complete for this first draft.

## Learning objectives

After this chapter, you should be able to:

1. distinguish PE geometry, MMA arithmetic, logical dataflow, and timing as four independent contracts;
2. explain weight-stationary, output-stationary, and row-stationary mappings without treating “stationary” as an absolute property;
3. trace Tusim's plug-in lifecycle from registry construction through direct selection, dispatcher callbacks, and statistics;
4. reproduce bitwise WS/OS/RS equivalence for the audited normal binary16 vectors while retaining the shared MMA-local subnormal defect;
5. derive the pinned WS, OS, and RS MMA-only cycle equations, including K-tile and edge behavior;
6. identify why parsed dataflow configuration and process-global core selection do not reach active execution as expected;
7. challenge a dataflow sweep that reports plausible numbers without executing the intended alternatives;
8. compare dataflows across traffic, storage, area, energy, compiler, control, and verification costs rather than one unqualified cycle ranking;
9. specify the evidence required to add a useful dataflow plug-in.

## Prerequisite graph

```text
Chapter 4: requested config -> active state
                    |
Chapter 5: ownership, globals, cores, counters
                    |
Chapter 6: O += W A, R×C×C tiles, edge and capacity contracts
                    |
                    v
       geometry ── MMA semantics ── logical mapping ── timing
           |             |                 |               |
           +-------------+-----------------+---------------+
                                 |
                                 v
                    pluggable dataflow audit
                                 |
                                 v
             later chapters: memory, scheduling, DSE
```

Chapter 6 fixes the arithmetic orientation:

```text
O[M,N] += W[M,K] × A[K,N]
```

It also fixes the shared tile geometry:

```text
tile_m = R, tile_n = C, tile_k = C
```

Chapter 7 does not reopen those contracts. It asks what changes—and what does not—when the selected plug-in name changes from WS to OS or RS.

## Opening architecture question: what does a dataflow choice buy?

Suppose a compiler can map one matrix multiplication to weight-stationary, output-stationary, or row-stationary hardware. All three produce the same matrix. Which should it choose?

A correct answer needs at least five pieces of information:

1. **reuse interval:** which value remains near a PE, for how long, and across which loop dimensions;
2. **movement boundary:** which storage or network transfers are avoided or added;
3. **resource capacity:** whether local registers, accumulators, SRAM ports, and interconnect can sustain the mapping;
4. **schedule:** when loads, broadcasts, MACs, reductions, stalls, and writes occur;
5. **objective:** latency, throughput, area efficiency, energy, flexibility, or verification risk.

The name alone answers none of these quantitatively.

Tusim appears to offer an easy comparison. It contains three source files, a common interface, a registry, a runtime setter, and different cycle values. On a 4×8 geometry, the Chapter 7 probe reports 342 WS cycles, 72 OS cycles, and 210 RS cycles for a 9×10×9 MMA. It would be tempting to conclude that OS is the best hardware.

That conclusion is unsafe. The three plug-ins execute the same scalar `m,n,k` loop and the same C-array reads. The timing differences come from fixed formulas: OS pays `ceil(k_count/4)`, while WS and RS pay nominal fill and drain. No dataflow-specific traffic, storage capacity, port contention, topology, overlap, frequency, area, or energy is executed. The result establishes a property of Tusim's formulas, not a workload-discovered physical optimum.

The architecture lesson is broader: **functional equivalence is necessary for interchangeable mappings, but a performance distinction is credible only when the model represents the mechanism that causes it**.

## 7.1 Dataflow vocabulary

A loop nest describes operations. A dataflow maps those operations and operands onto space, time, and storage.

For one GEMM element:

```text
O[m,n] += sum_k W[m,k] A[k,n]
```

Reuse opportunities include:

- one `W[m,k]` across multiple output columns `n`;
- one `A[k,n]` across multiple output rows `m`;
- one partial sum `O[m,n]` across multiple reduction positions `k`.

A mapping chooses where each value resides and how reuse is realized. “Stationary” means retained at a specified level over a specified interval. A value may be stationary in a PE register while its containing tile is replaced every K block. The same value may still move between DRAM and SRAM. Therefore every stationarity claim should answer:

```text
which value, at which level, over which loops, for how long?
```

### Weight-stationary

A WS design keeps weights close to compute while activations and partial sums move. A plausible implementation can reduce repeated weight delivery, especially when weights serve many activation positions. It may require preload phases, weight-capacity management, activation distribution, and a partial-sum reduction network.

### Output-stationary

An OS design keeps partial sums local over K. It can avoid repeated FP32 partial-sum SRAM traffic, but each active output lane must receive W and A values and hold an accumulator. Long reductions, accumulator capacity, simultaneous operand bandwidth, and spilling become central.

### Row-stationary

The row-stationary concept introduced by Eyeriss targets convolutional reuse across filter weights, activations, and partial sums through a hierarchical spatial mapping. It is not merely “GEMM with a different enum.” Translating it to GEMM requires an explicit correspondence between convolution loops, PE-local storage, spatial dimensions, multicast, and reduction.

### Logical mapping versus physical schedule

This chapter uses two separate terms:

- **logical dataflow:** intended assignment of stationary and streamed values;
- **physical schedule:** timed resource events implementing that assignment.

A logical mapping may be useful before exact hardware exists. But it cannot support cycle, bandwidth, or energy claims until the relevant events and resource limits are modeled or analytically specified.

## 7.2 Four contracts, not one

Dataflow discussions often mix four independent contracts.

| Contract | Question | Tusim pinned behavior |
|---|---|---|
| geometry | What subproblem reaches one plug-in call? | all plug-ins receive shared `R×C×C` tiles |
| MMA semantics | What numerical operation occurs? | all execute row-major FP16-input/FP32-accumulate `O += WA` |
| logical dataflow | What is intended to remain or move? | source names and comments describe WS/OS/RS |
| timing | How are cycles counted? | dispatcher sums plug-in-specific fixed callbacks per K tile |

Equal numerical output does not prove equal geometry or timing. Different timing does not prove different physical movement. A source filename does not change arithmetic. Keeping these contracts separate prevents several common errors:

1. calling `weight_stationary.c` a PE-level WS simulator because the filename says so;
2. treating bitwise WS/OS/RS equality as evidence that three physical schedules executed;
3. interpreting different cycle returns as measured bandwidth effects;
4. attributing a geometry edge penalty to dataflow semantics;
5. adding DMA and MMA counters merely because both use the unit “cycles.”

The final point carries forward a Chapter 6 defect boundary. Direct W/A/store DMA and global MMA update different cycle objects, while O-load uses another direct term. Tusim does not expose one coherent end-to-end DMA-plus-MMA timeline at this revision.

## 7.3 Source map and integration ladder

The live implementation is concentrated in:

| Source | Role |
|---|---|
| `compute/dataflow/dataflow_interface.h` | IDs, tensors, MMA descriptor, lifecycle/execution/timing callbacks, generic fields |
| `compute/dataflow/dataflow_registry.[ch]` | process-global object registry and lookup |
| `compute/dataflow/dataflow_dispatcher.c` | shared M/N/K tiling, callback order, operation/cycle aggregation |
| `weight_stationary.c` | WS functional kernel and fill/drain formula |
| `output_stationary.c` | OS functional kernel and extra K-step formula |
| `row_stationary.c` | RS functional kernel, private reuse arithmetic, reduced fill/drain formula |
| `tu_cmodel.c` | built-in registration, default/direct selection, public MMA counters |
| `infra/config.c` | string parsing and canonical-to-runtime conversion |
| `tu_core.c` | state snapshot and swap semantics |
| `tests/test_dataflow.c` | focused registry, identity, equivalence, switch, and edge tests |
| `tests/test_dataflow_sweep.c` | existing historical analytical comparison |

The durable [Chapter 7 source/claim ledger](../../notes/chapter-07-source-and-claim-ledger.md) records exact boundaries. Commands, hashes, raw compact output, formulas, and test dispositions are preserved in the [executable audit](../../experiments/ch07-dataflow-audit-2026-07-25.md).

A defensible integration ladder is:

```text
source exists
  -> object is in library
  -> object is registered
  -> selection API finds it
  -> selected pointer reaches executing state
  -> discriminating behavior changes
  -> focused and aggregate tests assert the change
  -> timing/traffic is calibrated for the claimed boundary
```

WS, OS, and RS pass the first five steps on the explicit direct-global path. The external Chapter 7 probe then demonstrates discriminating cycle deltas, but Tusim's focused and aggregate tests do not assert those deltas or the full selection path. Calibration remains absent. Config-selected and core-selected paths break earlier.

## 7.4 The plug-in interface

A plug-in object contains:

- a name and enum ID;
- an optional `init()` callback;
- `execute_tile()` for functional execution and its returned cycles;
- fill, drain, and compute-cycle callbacks;
- generic FLOP, tile, and cycle fields;
- opaque implementation data.

The dispatcher receives complete W/A/O tensor descriptors plus tile dimensions. It decomposes the full operation, constructs an operation descriptor, and for every M/N/K tile performs:

```text
plugin.init()
for each tile:
    cycles += plugin.get_fill_cycles(full tile_n, full tile_k)
    cycles += plugin.execute_tile(valid m,n,k counts)
    cycles += plugin.get_drain_cycles(full tile_m)
```

Two details matter.

First, `get_compute_cycles()` is never called. The cycle contribution labeled compute is whatever `execute_tile()` returns. A new author could implement a correct compute callback and observe no effect.

Second, pipeline depth breaks at two boundaries. JSON parses `pe_pipeline_depth`, but canonical-to-runtime conversion drops it because the runtime structure has no depth field. Public `tu_mma()` therefore writes compile-time `TU_PE_PIPELINE_DEPTH` into the operation descriptor. WS and RS then ignore even that descriptor value, reading private implementation fields that are never populated from it. Both ultimately use depth two. Repairing only the plug-in callback would not make JSON depth effective.

### Ownership mismatch

Constructor comments say the caller owns a returned plug-in and may call its specific destroy function. Once registered, however, the global registry assumes ownership and can free it through a global destroy operation that normal core, DPI, and process teardown do not call. Registered objects therefore persist for process lifetime in ordinary use. Destroying one through its plug-in-specific function would leave a dangling registry pointer; invoking global destruction while snapshots survive would do the same.

Duplicate registration follows a stable-address policy: if an ID already exists, the registry preserves the old object and frees **any** new object with that ID. It does not compare name, callbacks, implementation, or version. This protects `tu_core_t` snapshots from reinitialization-induced pointer churn, but also silently forbids replacement. The Chapter 7 probe verifies stable addresses across reinitialization.

This safety fix does not make plug-in state core-local. The registry and instances remain process-global and non-thread-safe.

## 7.5 What WS, OS, and RS execute

The three source files contain different architecture narratives. Their functional bodies, however, all execute the same loop order:

```text
for m
  for n
    psum = 0
    for k
      w = local_fp16_to_fp32(W[m,k])
      a = local_fp16_to_fp32(A[k,n])
      psum += w*a
    O[m,n] += psum
```

All use identical row strides and index expressions. All group FP32 additions the same way within one K tile. All add one partial sum into O per output element per K tile. Thus bitwise equality for the audited normal values is not surprising.

This loop does **not** execute:

- weight preload into PE registers;
- output retention in physical accumulators;
- activation streams;
- horizontal or vertical neighbor transfers;
- broadcast or multicast;
- partial-sum forwarding or reduction;
- dataflow-specific SRAM reads and writes;
- port conflicts, finite queues, backpressure, or overlap.

Even loop-order comments drift from source. RS prose contrasts its `m,n,k` order with an alleged WS `k,m,n` order, but live WS is also `m,n,k`. The implementation names are logical labels; they are not distinct functional movement traces.

### RS reuse fields

RS derives private `w_reuse_hits` and `w_reuse_misses` from valid tile dimensions. The arithmetic assumes each W value is fetched once and reused across N. The C loop still loads W on every `n,k` iteration. The fields therefore describe intended reuse rather than observed C accesses.

They are also opaque: no public accessor exposes them. Dispatcher invocation calls `rs_init()`, which clears them before every high-level MMA. A local `w_reads` variable increments but is not consumed. No corresponding A or partial-sum event counter exists.

### OS “bandwidth” overhead

OS comments describe simultaneous W/A streaming and claim bandwidth limitation. Its executable extra term is simply:

```text
ceil(k_count / 4)
```

It does not depend on M, N, valid output lanes, bus width, SRAM banks, port count, W bytes, A bytes, or overlap state. Calling this term “bandwidth measured by the model” would be incorrect. It is an uncalibrated implementation-local estimate.

## 7.6 Functional equivalence—and the shared numerical defect

The Chapter 7 probe runs three discriminating normal-value cases on a runtime 4×8 geometry:

| Shape M×N×K | Why selected | Result |
|---|---|---|
| 2×3×2 | nonsymmetric orientation and signs | WS/OS/RS FP32 outputs bitwise equal |
| 9×10×9 | M/N/K edges, K just beyond one tile | bitwise equal |
| 5×17×19 | multiple N and K tiles with irregular edges | bitwise equal |

Bitwise comparison is appropriate here because every plug-in uses the same input conversion logic and reduction grouping. The probe also computes an independent normal-value oracle through the canonical converter with the same FP32 grouping and requires each plug-in to match it bitwise. This is stronger than pairwise tolerance comparison for detecting implementation drift, but its scope remains the selected normal values.

### Equivalence can preserve a bug

Each plug-in duplicates an MMA-local FP16 converter. For raw binary16 subnormal `0x0001`, the canonical value is:

```text
2^-24
```

All three local converters produce:

```text
2^-14
```

The probe multiplies raw `0x0001` by `1.0` and observes the same wrong value from WS, OS, and RS—a factor of 1,024 too large. Thus:

```text
WS == OS == RS
```

is true for the vector, while:

```text
WS == canonical binary16 semantics
```

is false.

Functional equivalence between alternatives must be checked against an independent oracle, not only pairwise. This defect also demonstrates why duplicated numerical primitives raise verification cost: one bug has three copies and can pass every pairwise dataflow test.

## 7.7 Exact pinned timing formulas

Let:

```text
R = runtime PE rows
C = runtime PE columns
T_M = ceil(M/R)
T_N = ceil(N/C)
T_K = ceil(K/C)
k_q = valid K count in K tile q
```

Geometry is shared across plug-ins. The dispatcher charges fill and drain for every K tile and passes full configured `R,C` to those callbacks even on M/N edges.

### Weight-stationary

At effective fallback pipeline depth two:

```text
fill_q    = 2C
execute_q = k_q
drain_q   = 2R
```

Therefore:

```text
C_WS = T_M T_N [T_K(2C + 2R) + K]
```

This is the Chapter 6 equation, now compared against the other plug-ins.

### Output-stationary

OS fill and drain return zero. `execute_tile()` returns:

```text
k_q + ceil(k_q/4)
```

Therefore:

```text
C_OS = T_M T_N [K + sum_q ceil(k_q/4)]
```

The ceiling applies separately to every K tile. Replacing the sum with `ceil(K/4)` can undercount when K is split.

### Row-stationary

At fallback depth two:

```text
fill_q    = C + 1
execute_q = k_q
drain_q   = R
```

Therefore:

```text
C_RS = T_M T_N [T_K(C + 1 + R) + K]
```

### Executable results

For 4×8 geometry:

| Shape | Plug-in invocations (`T_M T_N T_K`) | Useful operations | WS | OS | RS |
|---|---:|---:|---:|---:|---:|
| 2×3×2 | 1 | 24 | 26 | 3 | 15 |
| 9×10×9 | 12 | 1,620 | 342 | 72 | 210 |
| 5×17×19 | 18 | 3,230 | 546 | 144 | 348 |

All values are source-defined MMA-only cycle estimates. They are not host elapsed time, do not include a coherent DMA term, assume no clock, and have no RTL or silicon calibration.

### A ranking built into the equations

For positive `R,C,k_q`, OS pays no fill/drain and only a small K term. RS pays roughly half WS's nominal geometry overhead. The model therefore structurally favors:

```text
OS < RS < WS
```

for the same shared geometry. Workload shape changes the magnitude, but it does not create a physically interesting reversal under these formulas. The ranking reflects assumptions written into the source, not measured reuse or bandwidth.

A pre-spec model should preserve all three alternatives, but it should also make the costs that distinguish them observable. Otherwise a sweep repeatedly confirms its constants.

## 7.8 Selection propagation and state scope

A dataflow option is useful only if the requested value reaches executing state.

### Direct global selection works

After initialization:

```c
tu_set_dataflow(TU_DATAFLOW_OUTPUT_STATIONARY);
tu_mma(...);
```

looks up the registered object, stores its pointer in `g_tu.dataflow`, and dispatches through OS. The probe verifies IDs, numerical output, and distinct cycle deltas for direct selections 0, 1, and 2.

### Parsed configuration does not select execution

JSON recognizes:

```text
weight_stationary -> 0
output_stationary -> 1
row_stationary -> 2
no_local_reuse -> 3
```

Recognized values reach `tu_config_t.dataflow_mode`. An unknown or misspelled name is not rejected: parsing silently returns ID 0, making it indistinguishable from an explicit WS request. For recognized values, `tu_config_to_runtime()` still does not copy dataflow into `tu_runtime_config_t`, which has no such field. The neighboring canonical `dataflow_via_plugin` field likewise does not control this path: plug-in versus legacy dispatch is compile-time `TU_DATAFLOW_DISPATCH_VIA_PLUGIN`, pinned to one. `tu_init_with_config()` then selects compile-time `TU_DATAFLOW_MODE`, normally WS.

The probe requests RS in JSON, verifies canonical value 2, initializes 4×8 geometry, and observes active `weight_stationary`. This is **parsed but not integrated** configuration.

### Global selection does not select a core snapshot

A `tu_core_t` stores a copy of `tu_state_t`, including its plug-in pointer. `tu_core_mma()` swaps that snapshot into `g_tu`, executes, and swaps it back.

The existing sweep calls process-global `tu_set_dataflow(df_id)` and then `tu_core_mma(core,...)`. Swap-in overwrites the process-global pointer with the core's default WS pointer. The Chapter 7 probe separately observes:

```text
process global = output_stationary
core snapshot  = weight_stationary
```

There is no public `tu_core_set_dataflow(core, id)` API in the pinned interface. Selection has two scopes, but only one setter.

### Unsupported NLR silently succeeds as WS

The enum and interface comments declare no-local-reuse ID 3. No NLR source object is registered. Calling `tu_set_dataflow(3)` logs a warning, falls back to WS, and returns success.

A caller that checks only return status can label a WS run as NLR. The DPI binding makes this split concrete: it accepts ID 3, retains requested metadata, and returns success. Its summary then prints `DF=NLR`, while its active-name query reports `weight_stationary` and execution uses WS. The probe reproduces both surfaces. Unsupported architecture alternatives should fail explicitly or return requested and active modes as structured state.

## 7.9 Statistics that change meaning

The interface calls `total_flops`, `total_tiles`, and `total_cycles` lifetime statistics. The public path treats them differently.

The dispatcher adds all three. Then `tu_mma()`:

1. copies plug-in tile and FLOP fields into `g_tu`;
2. adds the returned cycle value directly to `g_tu.estimated_cycles`;
3. clears plug-in tile and FLOP fields;
4. leaves plug-in total cycles cumulative.

Consequences:

- plug-in tile/FLOP fields are per-call scratch after public MMA, not totals;
- plug-in cycle field accumulates across calls and reinitialization;
- one snapshot cannot interpret all three under the same interval;
- shared global plug-ins can mix activity from core snapshots;
- RS reuse fields reset on every dispatcher `init()` and are not public.

A performance-counter structure elsewhere has only WS and OS cycle buckets and is not wired into `g_tu`. Its recorder maps every nonzero ID into OS, but the sole cycle-model caller currently hard-codes ID 0, so even OS activity arriving through that producer is attributed to WS. Snapshot difference and merge operations omit both dataflow buckets. The parallel counter subsystem therefore has defects in storage, production, classification, and composition—not merely a missing RS label.

Counter names are contracts. A robust interface should define ownership, interval, reset, monotonicity, requested versus completed events, and per-core versus process-global scope.

## 7.10 Challenging the existing dataflow sweep

`make test-dataflow-sweep` exits zero and prints a polished WS/OS/RS table for GEMM 128×128×256 on 16×16. It is an executable report, not a gate: output mismatches change printed text but are not accumulated, and `main()` returns zero unconditionally. Completion therefore proves neither functional equality nor active selection. Its plausible appearance makes it a valuable skeptical-review exercise.

### Functional-label defect

Each run creates a core whose snapshot selects WS. The harness changes process-global selection, then calls core MMA. Core swap-in restores WS. Thus all three outputs come from WS.

Their equality is true but non-discriminating. The labels are false evidence about execution.

### Formula drift

The harness separately computes analytical cycles once per spatial M/N tile using full K. The executable dispatcher splits K into sixteen K tiles and charges callbacks for each.

For 128×128×256 on 16×16:

| Source | WS | OS | RS |
|---|---:|---:|---:|
| existing sweep analytics | 20,480 | 16,384 | 18,496 |
| pinned executable formulas | 81,920 | 20,480 | 50,176 |

The differences are not rounding noise. They encode different temporal contracts.

### Cross-domain sum

The sweep adds an analytical DMA byte/bus term to its analytical MMA cycles. As a standalone analytical scenario, that sum could be defined if staged, non-overlapped transfer is an explicit assumption. But it must not be presented as reproduction of `g_tu.estimated_cycles`.

The executable defect is stronger than a generic unit mismatch. Direct W-load, A-load, and O-store call legacy DMA functions that update process-global `g_tu_dma.estimated_cycles`; their wrappers then add and clear the unrelated snapshot-local `g_tu.dma.estimated_cycles`, which those functions did not update. Those three transfers therefore contribute **zero** DMA cycles to `g_tu.estimated_cycles`. O-load bypasses the DMA engine and adds a third ad hoc byte/bus term directly. Core snapshots contain `g_tu.dma`, but not the process-global engine that actually received the legacy transfer cycles. No coherent per-core or end-to-end DMA-plus-MMA timeline exists.

### Review rule

A credible alternative sweep must assert at least:

- active plug-in ID in the state that will execute;
- a dataflow-sensitive counter or trace, not only equal output;
- formulas extracted from the pinned callback path;
- exact K-tile and edge semantics;
- one named cycle domain;
- source hashes or revision enforcement;
- a failure when any alternative silently falls back.

## 7.11 Dataflow regimes and multi-objective costs

The current formulas cannot select hardware, but the alternatives remain physically plausible and useful for exploration.

| Objective | WS regime | OS regime | RS regime |
|---|---|---|---|
| reuse target | weights reused across outputs | partial sums retained across K | several convolutional reuse forms under a concrete mapping |
| named-boundary traffic opportunity | fewer PE-register/local-store W refills if persistence is realized | fewer psum transfers across the chosen accumulator boundary | fewer selected W/A/psum movements across a stated hierarchy if convolution loops and multicast realize the mapping |
| likely pressure | activation/psum network | simultaneous W/A delivery and accumulator capacity | local storage, multicast, mapping complexity |
| latency opportunity | amortized preload under repeated W use | reduced psum spill/reload for long reductions | only the latency induced by specifically eliminated movement events; no generic RS latency claim |
| throughput limit | operand delivery or reduction may bound sustained issue | W/A delivery and accumulator occupancy may bound issue | mapping balance and network/local-store service may bound issue |
| area cost | weight registers and routing | FP32 accumulators per active output | richer local storage, control, and network |
| energy assumption | benefit requires avoided W movement to exceed added storage/control energy | benefit requires avoided psum movement to exceed accumulator and delivery cost | benefit requires named avoided movements to exceed richer mapping/storage/network cost |
| numerical behavior | common current scalar reduction and shared subnormal defect | common current scalar reduction and shared subnormal defect | common current scalar reduction and shared subnormal defect |
| compiler burden | weight placement and tile persistence | output ownership and spill schedule | loop-to-space mapping across convolution dimensions |
| verification burden | preload/refill and reduction ordering | accumulator lifetime and overflow/spill | many reuse paths and topology-dependent movement |
| fidelity/evidence cost | Tusim exposes a name and nominal fill/drain only | Tusim exposes a name and `ceil(k/4)` term only | Tusim exposes a name and opaque shape-derived W reuse only |

### Workload dependence

- **Large repeated-weight batches:** WS may amortize weight placement if A and partial sums can move efficiently.
- **Large-K output tiles:** OS may reduce partial-sum traffic if accumulator capacity is sufficient and both operands can be delivered.
- **Convolution with structured spatial reuse:** RS may reduce movement across several operands, but only with a mapping that represents convolution loops and storage hierarchy.
- **Small or irregular tiles:** fill, edge occupancy, and setup can dominate; a flexible smaller engine may outperform a nominally higher-reuse mapping.
- **Dynamic or sparse workloads:** control, metadata, load balance, and irregular movement can reverse conclusions from dense GEMM formulas.

No alternative should be deleted because one hard-coded cycle table ranks it lower. Instead, a pre-spec model should make each alternative's benefit and sacrifice explicit, then identify the workload and implementation regime where it belongs on a Pareto frontier.

## 7.12 How to add a defensible dataflow plug-in

Adding a `.c` file is only the first step.

### 1. State the architecture hypothesis

Examples:

- NLR can reduce PE-local storage area for bandwidth-rich small GEMMs.
- A persistent-WS schedule can amortize preload across a batch of A tiles.
- A reduction-stationary mapping can improve split-K accumulation under a given network.

Without a question, a fourth enum becomes feature inventory rather than exploration capability.

### 2. Define four contracts

Document separately:

- geometry and tile shape;
- arithmetic and accumulation order;
- logical stationary/streamed values and reuse interval;
- timing/traffic resources and omitted effects.

### 3. Define ownership and state

Specify:

- registry ownership;
- whether implementation state is immutable, per-core, per-operation, or shared;
- initialization and reset semantics;
- behavior under duplicate registration;
- thread safety and destruction order.

### 4. Integrate every live path

Audit:

```text
source -> Makefile object -> registry -> enum/name lookup
       -> canonical config -> runtime config -> global/core/DPI/compiler selection
       -> direct and queued execution -> focused and aggregate tests
```

Reject unsupported values. Do not silently relabel a fallback.

### 5. Make the cause observable

If a plug-in claims reuse, expose traffic or reuse events at named boundaries. If it claims lower latency, connect those events to finite resources or a documented analytical equation. If it claims energy, combine action counts with characterized energy assumptions and uncertainty.

### 6. Verify arithmetic independently

Use:

- nonsymmetric matrices;
- edge and multi-K cases;
- seeded accumulators and bias where supported;
- random finite normals;
- zero, subnormal, infinity, and NaN policy vectors;
- an independent canonical oracle.

Pairwise equality is insufficient when alternatives duplicate code.

### 7. Verify timing with counterexamples

Choose shapes that discriminate:

- one versus multiple K tiles;
- exact versus partial M/N/K edges;
- reuse across multiple high-level calls;
- capacity overflow and spill;
- bandwidth below, at, and above compute demand;
- overlap enabled versus staged execution.

### 8. Calibrate only at a named boundary

Calibration requires a named RTL block, simulator, or silicon counter; workload and configuration; clock; comparison method; and error. A label such as `cycle_accurate` is not calibration.

## 7.13 Verification strategy

The isolated audit enforced twelve source hashes, rebuilt the static library, and ran:

```text
test-dataflow:  9/9 pass
test-config:   20/20 pass
test-multicore:16/16 pass
test-dpi:      13/13 pass
existing sweep: exit 0, challenged rather than accepted
chapter probe: SUMMARY PASS
```

The focused suite is part of aggregate `make test`; the sweep is not. The focused target uses `-L. -ltucmodel`, which can select a stale shared library if one exists while only the archive dependency rebuilds. This audit used a clean tree with no `.so`, and the chapter probe linked `./libtucmodel.a` explicitly.

### What existing tests prove

They prove registry lookup, direct global selection for identity/equivalence cases, switching WS to OS in one global session, and selected edge correctness. DPI selection names also pass. Multicore tests validate existing lifecycle and arithmetic behavior.

### What they do not prove

They do not prove:

- JSON selection propagation;
- core-specific dataflow selection;
- distinct physical movement;
- pinned cycle equations;
- RS edge equivalence in the focused edge test;
- NLR execution;
- subnormal correctness;
- per-dataflow traffic or energy;
- thread-safe statistics;
- RTL or silicon timing.

A passing test suite narrows uncertainty only within its assertions.

## Fidelity box — what “pluggable dataflow” means here

> **Executable:** WS, OS, and RS source objects are linked, globally registered, directly selectable, and numerically exercised through the shared dispatcher.
>
> **Functional model:** the audited normal-value vectors produce bitwise-equal FP32 outputs through identical scalar reduction grouping.
>
> **Numerical defect:** every plug-in's local FP16 converter maps raw minimum subnormal `0x0001` to `2^-14` rather than canonical `2^-24`.
>
> **Logical/intended mapping:** source names and comments describe stationary operands; distinct PE-local movement schedules do not execute.
>
> **Deterministic estimate:** WS, OS, and RS use the source equations in Section 7.7, with per-K-tile overhead and no calibration.
>
> **Integration gaps:** unknown JSON names silently become WS; recognized JSON dataflow and pipeline depth are dropped before runtime; process-global selection does not modify a core snapshot; NLR falls back to WS while returning success, and DPI can report requested NLR beside active WS.
>
> **Timing boundary:** MMA-only. W/A-load and O-store legacy DMA cycles accumulate in process-global `g_tu_dma` but contribute zero to `g_tu.estimated_cycles`; O-load uses a separate direct term. These domains cannot form an executable end-to-end latency.
>
> **Not established:** dataflow-specific SRAM/network traffic, finite ports/queues, overlap, PE wavefronts, active-lane timing, frequency, area, energy, RTL equivalence, or silicon calibration.

## 7.14 Common failure modes

1. **Using a filename as evidence.** `row_stationary.c` does not reproduce Eyeriss movement by name.
2. **Conflating geometry and dataflow.** All three use the same `R×C×C` tiles.
3. **Accepting pairwise equality as oracle correctness.** All three share the subnormal defect.
4. **Treating comments as loop behavior.** WS, OS, and RS live kernels all use `m,n,k`.
5. **Calling OS's constant a bandwidth model.** It ignores bytes, ports, and bus width.
6. **Ignoring K-tile callbacks.** Fill/drain and OS ceilings apply once per K tile.
7. **Using valid edge counts for timing without checking callbacks.** Fill/drain receive full nominal R/C.
8. **Sweeping inert pipeline depth.** JSON depth is dropped before runtime; compile-time descriptor depth then does not populate WS/RS private state.
9. **Assuming parsed config is active config.** Unknown names silently become WS, while recognized dataflow is dropped during runtime conversion.
10. **Selecting global state before core swap-in.** The core's pointer replaces it during execution.
11. **Treating fallback success as requested execution.** NLR request becomes WS.
12. **Destroying a registered plug-in directly.** Registry ownership would be violated.
13. **Reading mixed counter intervals as totals.** cycles accumulate; tile/FLOP fields clear.
14. **Adding DMA and MMA cycles.** Legacy W/A/store cycles land in a different process-global object and contribute zero to `g_tu.estimated_cycles`; O-load uses a third path.
15. **Treating sweep exit zero as a test pass.** The report does not return failure on output mismatch.
16. **Trusting a polished sweep table without an active-state assertion.** Plausibility is not provenance.
17. **Converting cycle ranking to energy ranking.** No movement or action-energy model supports it.
18. **Calling one dataflow universally optimal.** Workload, storage, topology, frequency, and compiler costs matter.

## 7.15 Development implications

The audit exposes concrete research questions rather than silently changing Tusim.

1. Add dataflow to runtime configuration and define global, core, DPI, queue, and compiler selection scopes.
2. Return explicit errors for unsupported IDs; report requested and active modes separately.
3. Replace three local FP16 converters with the canonical precision path and add raw-bit regression vectors.
4. Split the plug-in contract into functional arithmetic, logical mapping, traffic events, and timing policy.
5. Carry pipeline depth through canonical-to-runtime conversion and the MMA descriptor, then decide whether state persists across K tiles or calls; pass valid edges accordingly.
6. Use or remove `get_compute_cycles()` so the interface has one source of timing truth.
7. Define per-core counter snapshots with coherent intervals, reset semantics, real selected-mode production, RS storage/classification, and complete diff/merge behavior.
8. Represent named memory levels, multicast/broadcast, partial-sum movement, finite bandwidth, and overlap before making reuse-performance claims.
9. Repair the existing sweep so each run selects the executing core state and asserts pinned counters.
10. Preserve WS, OS, RS, and any future NLR mode as plausible alternatives only when their distinct mechanisms are observable.

## Summary

- A dataflow maps operations and data across space, time, and storage; “stationary” requires a named level and reuse interval.
- Geometry, MMA arithmetic, logical mapping, and timing are separate contracts.
- Tusim links and registers WS, OS, and RS, and direct global selection executes all three.
- Their functional kernels use the same scalar `m,n,k` loop and C-array accesses; physical movement distinctions do not execute.
- Audited normal values match bitwise, but every plug-in shares the FP16 subnormal defect: `0x0001` becomes `2^-14` instead of `2^-24`.
- The pinned cycle formulas are deterministic, per-K-tile, and uncalibrated. They structurally rank OS before RS before WS.
- Unknown JSON dataflow names silently become WS; recognized names parse but are dropped before runtime, so initialization remains WS.
- Process-global selection does not change a `tu_core_t` snapshot, which invalidates the functional labels in the existing dataflow sweep.
- NLR is declared but unregistered; selection falls back to WS and returns success, while DPI can retain and print the requested NLR label.
- Plug-in cycle, tile, and FLOP fields use inconsistent accumulation intervals.
- Legacy W/A-load and O-store DMA cycles land in process-global `g_tu_dma` and contribute zero to `g_tu.estimated_cycles`; O-load uses a separate direct term. No executable end-to-end latency is defined.
- A useful future comparison needs observable traffic, storage, resource, overlap, area/energy, and compiler contracts—not more enum names.

## Review questions

1. What does “weight stationary” fail to specify unless a storage level and reuse interval are named?
2. Why can WS, OS, and RS be functionally equivalent while having different timing formulas?
3. Why does bitwise pairwise equality fail to detect the shared FP16 subnormal defect?
4. Derive WS, OS, and RS cycles for M=9, N=10, K=9, R=4, C=8.
5. Why must `sum_q ceil(k_q/4)` not always be replaced by `ceil(K/4)`?
6. A new plug-in implements only `get_compute_cycles()`, but observed cycles do not change. Trace the likely contract break and propose one-source-of-truth timing semantics.
7. A JSON experiment compares `row_stationary` with misspelled `row_statoinary`; both execute WS. Identify the distinct parse-stage and conversion-stage failures.
8. A process-global trace says OS immediately before `tu_core_mma()`, while the core snapshot says WS. Predict the executing mode and name the missing API.
9. A DPI dashboard says `DF=NLR`, its active-name query says `weight_stationary`, and the setter returned success. Which field should be authoritative, and how should the API represent fallback?
10. A counter snapshot shows cumulative cycles but zero plug-in tiles after a successful MMA. Explain why this is possible and design an interval-consistent replacement.
11. A sweep prints three matching outputs and exits zero. List the additional assertions required before claiming that three dataflows executed.
12. What additional events would be needed to call OS bandwidth-limited in an executable model?
13. Why can Eyeriss support RS motivation without validating Tusim's RS timing formula?
14. Under what explicit assumptions could analytical DMA and MMA cycles be added safely?

## Design exercises

1. Specify `tu_core_set_dataflow(core,id)` with ownership, error, and counter semantics. Include concurrent cores selecting different plug-ins.
2. Rewrite the 128×128×256 sweep to assert active core IDs and pinned per-K cycle deltas. Explain how to avoid stale shared-library linkage.
3. Design a traffic-event interface for W, A, O, multicast, and partial-sum transfers at PE-register, local-SRAM, and global-buffer boundaries.
4. Propose a minimal persistent-WS experiment that reuses one W tile across several A tiles. State capacity, invalidation, preload, and timing contracts.
5. Map one 2-D convolution loop nest to a defensible row-stationary schedule. Identify what Tusim's generic GEMM descriptor cannot express.
6. Create an independent raw-binary16 oracle suite covering zeros, subnormals, normals, infinities, and NaNs for all plug-ins.
7. Replace the mixed plug-in fields with a per-core snapshot API. Define requested/completed events, monotonicity, reset, and merge.
8. Construct a multi-objective Pareto comparison in which WS, OS, and RS each win one plausible regime. Do not invent silicon numbers; use symbolic or explicitly assumed costs.
9. Define a staged and an overlapped DMA/MMA analytical model. Explain why neither equals the pinned `g_tu.estimated_cycles` without integration work.

## Primary references

1. H. T. Kung, “Why Systolic Architectures?,” *Computer*, 1982. DOI: [10.1109/MC.1982.1653825](https://doi.org/10.1109/MC.1982.1653825). Use for regular local-communication motivation, not Tusim timing validation.
2. Yu-Hsin Chen, Joel Emer, and Vivienne Sze, “Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,” ISCA 2016. DOI: [10.1109/ISCA.2016.40](https://doi.org/10.1109/ISCA.2016.40). Use for convolutional row-stationary reuse reasoning; its architecture and energy results do not transfer to Tusim's GEMM plug-in.
3. Hyoukjun Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” MICRO 2019. DOI: [10.1145/3352460.3358252](https://doi.org/10.1145/3352460.3358252). Use for explicit data-centric mappings and modeled reuse/cost boundaries.
4. Angshuman Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019. DOI: [10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042). Use for separating workload, architecture, mapping, and constraints.
5. Ananda Samajdar et al., “SCALE-Sim: Systolic CNN Accelerator Simulator,” arXiv:1811.02883v2, 2018. DOI: [10.48550/arXiv.1811.02883](https://doi.org/10.48550/arXiv.1811.02883). Use for configurable dataflow-sensitive simulation context; fidelity does not transfer.
6. Samuel Williams, Andrew Waterman, and David Patterson, “Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures,” *CACM*, 2009. DOI: [10.1145/1498765.1498785](https://doi.org/10.1145/1498765.1498785). Use for named bandwidth boundaries and operational-intensity reasoning, not latency simulation.
7. [Verified foundation bibliography](../../references/foundations.md).
8. [Chapter 7 executable audit](../../experiments/ch07-dataflow-audit-2026-07-25.md).
