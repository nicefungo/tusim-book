# Chapter 7 — Pluggable Dataflows

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-7)

A core runs the same matrix multiplication three times. Every output bit agrees, but the counter advances by 246 cycles for weight-stationary, 72 for output-stationary, and 162 for row-stationary. What changed? Not the number of multiplies, and not a measured stream of weights. The core selected a different implementation of the tile cost. This chapter shows how to tell those explanations apart.

**Edition and scope.** The examples use public Tusim commit `7a094ff6c5527eff8e4318de676f0c0221c448b4`. A cycle here is an increment of the simulator's estimated-cycle counter across one MMA call, not host elapsed time or a hardware clock measurement.

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

To isolate compute, place the operands in SRAM before taking the first counter reading and take the second immediately after MMA. No DMA term enters the subtraction. To predict job latency one would also need a transfer path, a clock convention and an ordering or overlap rule.

## 7.3 From a mode to code that runs

Follow these anchors in the public source. Paths in the table are relative to `tu_cmodel/`.

| Question | Source | What to look for |
|---|---|---|
| What can configuration carry? | `infra/config.c`: `parse_dataflow_str`, `tu_config_to_runtime` | WS/OS/RS have IDs 0/1/2; mode and depth reach runtime configuration. Validation rejects reserved and unknown modes. See Chapter 4 for JSON ingress. |
| What objects exist? | `tu_cmodel.c`: `tu_init_with_config`, `tu_set_dataflow`; `compute/dataflow/dataflow_registry.c` | Initialization registers the three compiled-in objects, then selects the requested ID. This is not dynamic loading. |
| Whose pointer changes? | `tu_core.c`: `tu_core_set_dataflow`, `core_swap_in`, `tu_core_mma`, `core_swap_out` | A core holds a selected pointer, not a private copy of the registered object. |
| What reaches the plug-in? | `tu_cmodel.c`: `tu_mma`; `compute/dataflow/dataflow_dispatcher.c`: `tu_dataflow_execute_mma` | Follow the row strides, tile origins, valid counts, runtime depth and returned cycle total. |
| What distinguishes the labels? | `weight_stationary.c`, `output_stationary.c`, `row_stationary.c` in `compute/dataflow/` | Compare the inner loads and multiply-adds, then compare the callback returns. |

A library member is not necessarily registered. A registered object is not necessarily selected. A selected object may still compute the wrong answer. At each step ask for an observation that would differ if *that particular* step failed.

## 7.5 What WS, OS, and RS execute

For all three built-ins the functional body is equivalent to the following, with row-major indexing and byte strides supplied by the caller:

```text
for each valid m, n:
    partial = FP32 zero
    for each valid k in this K tile:
        partial += tu_fp16_to_fp32(W[m,k]) * tu_fp16_to_fp32(A[k,n])
    O[m,n] += partial
```

The K tile boundary matters: adding a partial sum into O once per block need not round the same way as a single unblocked dot product. Bias expansion, if requested, precedes dispatch; the examples here do not request bias. A seeded O still checks that the kernel **adds**, rather than overwrites.

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

## 7.6 Functional equivalence: choose an oracle that can disagree

The public single-state sweep computes expected FP32 results separately from the tile kernel, with the same K grouping. That checks indexing and accumulation. Its input generator and oracle use Tusim precision helpers, however. A common conversion error could survive both this check and a comparison among the three plug-ins.

Use an identity multiplication to remove the reduction as a source of ambiguity. Set W to the 2×2 identity, O to zero, and A to the following 2×3 matrix. The product must copy A into O, widening each entry to FP32:

```text
A = [ 2^-24  -2   3 ]       input A[0,0] word:  0x0001 (binary16)
    [ 4       5  -6 ]       output O[0,0] word: 0x33800000 (binary32)
```

Both cores produced that word and the five other expected words in each mode. The fixture generator uses Python binary packing, not Tusim conversion. A second fixture uses signed, small integer matrices of shape 9×9 and 9×10 and opposite nonzero FP32 seeds on the two cores. Products and sums are exactly representable. Integer dot products plus those seeds therefore predict all 90 output words without copying the dispatcher's accumulation code. A transposition, missing K tail or overwrite of O has somewhere to show up.

At the first-edition pin (`e918c80b6fce833cd1fcae97730fa841c2176f25`), the three private decoders had agreed on the *wrong* value for the smallest positive half subnormal. At this edition's pin the three kernels call `tu_fp16_to_fp32`, and the identity fixture returned the expected value. That establishes one raw-bit case, not general conformance for subnormals, rounding modes, signed zeros or NaNs. Chapter 8 treats the precision contract separately.

## 7.7 Deriving the MMA delta

Let the PE array have `R` rows and `C` columns. An interior tile has shape `R×C×C`; at any tile origin let `m,n,k` denote the **valid** extents and `d` the runtime pipeline depth. Sum one row of this table over *all* tile triples, including each K tail:

| Mode | Fill | Execute | Drain |
|---|---:|---:|---:|
| WS | `d*n` | `k` | `d*m` |
| OS | `0` | `k + ceil(k/4)` | `0` |
| RS, `d=1` | `0` | `k` | `0` |
| RS, `d>1` | `(d-1)*n + 1` | `k` | `(d-1)*m` |

**Work it by hand.** For `M×N×K = 9×10×9` on `4×8`, the M counts are `[4,4,1]`, N counts `[8,2]`, K counts `[8,1]`. There are six spatial tiles, twelve tile triples and `2MNK = 1,620` useful operations (two per MAC). All modes pay a base of `6×(8+1) = 54`. Sum `m+n` across the six spatial tiles: every M count appears twice and every N count three times, giving `2×9 + 3×10 = 48`. Both K tiles incur spatial overhead for WS and RS, so the extent sum is 96. At depth two:

| Mode | Independent prediction | Observed delta, core 0 | Observed delta, core 1 |
|---|---:|---:|---:|
| WS | `54 + 2×96 = 246` | 246 | 246 |
| OS | `54 + 6×(2+1) = 72` | 72 | 72 |
| RS | `54 + 96 + 12 = 162` | 162 | 162 |

The twelve in the RS row is one fill increment per tile triple. For the final `(m,n,k)=(1,2,1)` tile, WS pays for two valid columns and one valid row, not eight and four. Conversely, a short K tail does **not** make fill and drain disappear. The first edition's 342-cycle WS result charged nominal edges; using it as the expected value here would reject the current implementation.

Depth changes can even reverse a ranking. For `31×19×17` on `16×16`, the public depth sweep returned:

| Depth | WS | OS | RS |
|---:|---:|---:|---:|
| 1 | 268 | 88 | 68 |
| 2 | 468 | 88 | 276 |
| 4 | 868 | 88 | 676 |

At depth one RS pays only the base and beats OS; at depth two OS wins this comparison. OS stayed at 88 because its callback does not read depth. No improvement in measured operand bandwidth is needed to explain either result.

## 7.8 Who owns a selection?

`tu_set_dataflow(id)` changes the object selected in the direct state `g_tu`. Pair it with `tu_mma`. To change a core use `tu_core_set_dataflow(core,id)` and pair it with `tu_core_mma(core,...)`. The latter saves the surrounding `g_tu`, installs the core's state for the call, writes it back into the core, and restores the surrounding state. Two lookups can return the very same registry object without making the two *selections* the same variable.

The experiment kept two cores alive. Before either ran, it selected a different mode on each and the remaining mode on the direct path. Each core ran both fixtures; the direct path ran the edge fixture. Entries show **active mode / edge-MMA delta**, not requests copied from labels.

| Round | Core 0 | Core 1 | Direct state |
|---:|---|---|---|
| 1 | WS / 246 | OS / 72 | RS / 162 |
| 2 | OS / 72 | RS / 162 | WS / 246 |
| 3 | RS / 162 | WS / 246 | OS / 72 |

The probe checked the selected ID, registry pointer and name before dispatch, the ID and delta afterward, and the idle peer's unchanged ID and counter. For example, core 0 entered its second edge call with 258 estimated cycles and left with 330. The **72-cycle difference** identifies the OS estimate; comparing cumulative totals across cores would obscure it. The calls were sequential. Neither simultaneous execution nor thread isolation follows.

In each round the direct and core setters rejected the reserved no-local-reuse ID (`-1` return) and preserved their previous selections. There is no fourth executable NLR object in this registry. This setter result is not evidence about parsing a JSON string, a DPI dashboard, or the behavior of an unchecked runtime initializer. [Chapter 4](04-configuration-as-the-architecture-contract.md) traces configuration validation; the public single-state sweep here starts with a runtime struct, not a JSON document.

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
| numerical behavior | same scalar reduction and shared conversion helper | same scalar reduction and shared conversion helper | same scalar reduction and shared conversion helper |
| compiler burden | weight placement and tile persistence | output ownership and spill schedule | loop-to-space mapping across convolution dimensions |
| verification burden | preload/refill and reduction ordering | accumulator lifetime and overflow/spill | many reuse paths and topology-dependent movement |
| fidelity/evidence cost | Tusim exposes a valid-extent fill/drain estimate, not transfer events | Tusim exposes a `ceil(k/4)` surcharge, not a port or bus model | Tusim exposes a fill/drain estimate and opaque shape-derived W reuse |

### Workload dependence

- **Large repeated-weight batches:** WS may amortize weight placement if A and partial sums can move efficiently.
- **Large-K output tiles:** OS may reduce partial-sum traffic if accumulator capacity is sufficient and both operands can be delivered.
- **Convolution with structured spatial reuse:** RS may reduce movement across several operands, but only with a mapping that represents convolution loops and storage hierarchy.
- **Small or irregular tiles:** fill, edge occupancy, and setup can dominate; a flexible smaller engine may outperform a nominally higher-reuse mapping.
- **Dynamic or sparse workloads:** control, metadata, load balance, and irregular movement can reverse conclusions from dense GEMM formulas.

No alternative should be deleted because one hard-coded cycle table ranks it lower. Instead, a pre-spec model should make each alternative's benefit and sacrifice explicit, then identify the workload and implementation regime where it belongs on a Pareto frontier.

[Next: Chapter 8 — Floating-Point Foundations](08-floating-point-foundations.md)
