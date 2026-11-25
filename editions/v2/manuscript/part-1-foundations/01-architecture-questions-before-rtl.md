# Chapter 1 — Architecture Questions Before RTL

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-1)

> **Evidence boundary.** The Tusim observations in this chapter come from the July 25, 2026 first-edition audit (`e918c80`), not a run on the November 18, 2026 edition pin (`7a094ff`). The worked roof arithmetic was checked separately; 32 B/cycle is an assumed budget, not measured DMA bandwidth.

## 1.1 A tensor unit is a set of negotiated constraints

Imagine that an architecture team is asked to design a tensor unit for a future system-on-chip. A product requirement may provide a model family, a latency target, a power envelope, and a memory interface. The first proposal often starts with a compute array:

- choose the number of processing elements;
- choose a clock frequency;
- multiply the two;
- report a peak number of operations per second.

That calculation is necessary, but it is not an architecture.

A useful tensor unit must repeatedly bring operands to the compute array, keep enough of them near the processing elements to exploit reuse, preserve partial sums, obey numerical semantics, schedule dependent operations, and return results through a finite memory system. The host, compiler, runtime, command processor, DMA engines, scratchpads, interconnect, and compute engines participate in one execution contract. If any part is undersized or mismatched to the workload, advertised peak arithmetic throughput can remain mostly idle.

The architecture is therefore a negotiated set of constraints:

- **workload constraints:** tensor dimensions, operators, dependencies, batch size, sparsity, and latency distribution;
- **arithmetic constraints:** format, accumulator width, rounding, saturation, and acceptable error;
- **spatial constraints:** array dimensions, dataflow, local storage, and interconnect;
- **memory constraints:** capacity, banking, ports, bandwidth, latency, and transfer granularity;
- **system constraints:** host interaction, synchronization, context switching, and multi-core communication;
- **implementation constraints:** area, power, timing closure, verification effort, and programmability.

The phrase *design-space exploration* should not mean trying many integers until a benchmark becomes faster. It means learning how these constraints interact, identifying Pareto-efficient regions, and making explicit which costs purchase each benefit.

A configuration can be valid at several different levels:

1. **syntactically valid:** the parser accepts it;
2. **semantically coherent:** its fields define non-contradictory behavior;
3. **physically plausible:** bandwidth, ports, wiring, storage, pipeline, and control could support the claimed mechanisms;
4. **economically implementable:** area, power, schedule, verification, and product constraints make it worth building.

A parameterized simulator usually proves only the first two automatically. More PEs require operand delivery and reduction capacity; wider buses require ports and wiring; larger SRAM can affect area, access time, energy, and clock; ideal overlap requires buffers, independent ports, queues, and dependency information. The book will therefore treat configuration plausibility as an argument supported by models and evidence, not as a consequence of parsing JSON.

### Historical perspective: regular computation and regular movement

Systolic architectures were proposed as regular arrays of simple processing elements through which data moves rhythmically [KUN82]. Their enduring appeal comes from more than parallel arithmetic. A regular array can expose local communication, repeated data use, and predictable control. Matrix multiplication maps naturally onto such structures because the same input elements participate in many multiply–accumulate operations.

Modern machine-learning accelerators inherit this principle but embed it in a much larger system. A production tensor processor may use software-managed on-chip memory, DMA, compiler-selected mappings, multiple numerical formats, and a service-level latency objective. The first-generation datacenter TPU, for example, combined a large matrix multiply unit with software-managed memory and deterministic execution; its published analysis also showed that utilization and memory bandwidth materially affected achieved performance [JOU17]. The lesson is not that every tensor unit should copy that design. The lesson is that arithmetic, memory, workload, and system objectives must be evaluated together.

---

## 1.2 Five quantities that must not be confused

Accelerator discussions often use *performance* as if it were one number. At least five quantities must be separated.

### Peak throughput

If an array contains `R × C` processing elements, each performs one multiply–accumulate per cycle, and one MAC is counted as two operations, an idealized peak is

$$
P_{peak}=2RCf,
$$

where `f` is clock frequency.

For a 16×16 array at 1 GHz, this convention gives 512 billion operations per second. This is a capacity statement under ideal issue and occupancy. It says nothing about whether operands arrive, whether the workload fills the array, or whether useful work is performed every cycle.

Operation-count conventions must always be stated. Some documents report one MAC as one operation; others report a multiply and an addition separately. Comparing TOPS without reconciling this convention can create an apparent factor-of-two difference where none exists.

### Achieved throughput

Achieved throughput is useful operations divided by elapsed time. It includes inefficiencies caused by tile edges, fill/drain, data movement, dependencies, and stalls—provided the elapsed-time model actually includes those effects.

A simulator can report achieved throughput only relative to its modeled time. A value derived from an analytical estimate is not a silicon measurement, even when expressed in familiar units such as TOPS.

### Latency

Latency is the time from a defined start event to a defined completion event. The definition matters. Kernel latency, accelerator-command latency, model latency, host-observed latency, and tail latency are different measurements. Batching can improve throughput while making an individual request wait longer.

### Utilization

Utilization is a ratio, but the numerator and denominator vary. Possible definitions include:

- cycles in which the compute engine is active divided by total modeled cycles;
- active PEs divided by available PEs;
- issued MACs divided by peak issue slots;
- useful MACs divided by all executed MACs, including padding.

A reported 100% “active-cycle utilization” can coexist with poor MAC efficiency if only a fraction of the array performs useful work. A textbook or tool must name the definition rather than relying on the word *utilization*.

### Energy efficiency

Energy efficiency relates useful work to energy, commonly operations per joule. It depends on what is included: compute, SRAM, DRAM, NoC, control, leakage, host overhead, and data conversion. Reducing arithmetic may fail to reduce energy if metadata or irregular accesses increase data movement. Conversely, a mapping with more operations can sometimes reduce total energy by improving locality and avoiding expensive memory transfers.

**Checkpoint 1.1**
A design reports 1 TOPS peak, 0.2 TOPS achieved, and 95% active-cycle utilization. Is this contradictory? No. The counters may indicate that the engine is active during most modeled cycles while only part of the array performs useful operations, or the achieved metric may include costs outside the active-cycle denominator. The definitions must be audited.

---

## 1.3 First-order balance: compute and data movement

The Roofline model provides a useful first question [WAT09]. Let

- `P_peak` be peak arithmetic throughput;
- `B` be sustainable memory bandwidth;
- `I` be operational intensity, useful operations per byte transferred across a specified boundary.

Then a first-order performance upper bound is

$$
P \le \min(P_{peak}, B I).
$$

If `BI < P_peak`, the chosen memory boundary imposes the lower roof. If `BI > P_peak`, arithmetic capacity imposes the lower roof. This classification is not a cycle simulation. It is a bound that tells us where to investigate next.

### The boundary is part of the definition

Operational intensity is meaningless without a memory boundary. Bytes transferred from DRAM differ from bytes read from a global buffer, scratchpad, register file, or PE-local storage. Reuse can increase intensity at one boundary while leaving another unchanged.

For a dense matrix multiplication

$$
O_{M\times N}=W_{M\times K}A_{K\times N},
$$

an ideal compulsory-traffic estimate with FP16 inputs and FP32 output is

$$
Q = 2MK + 2KN + 4MN \quad \text{bytes},
$$

and useful arithmetic under the two-operations-per-MAC convention is

$$
F=2MNK.
$$

The corresponding ideal operational intensity is

$$
I=\frac{2MNK}{2MK+2KN+4MN}.
$$

This estimate assumes each matrix crosses the chosen boundary only once. Real tiling can reload operands; write allocation, alignment, metadata, and partial-sum spills can add traffic. Thus the equation is a useful upper bound on intensity, not a guarantee.

### Worked comparison

Use a notional 16×16 array at 1 GHz and a 256-bit transfer path, or 32 bytes per cycle. Under the assumptions above:

| GEMM `(M,N,K)` | Useful operations | Ideal bytes | Ideal intensity | Bandwidth roof |
|---|---:|---:|---:|---:|
| `(128,128,128)` | 4,194,304 | 131,072 | 32 ops/B | 1,024 GOPS |
| `(16,16,16)` | 8,192 | 2,048 | 4 ops/B | 128 GOPS |
| `(16,128,128)` | 524,288 | 45,056 | 11.64 ops/B | 372.36 GOPS |

The ideal compute peak is 512 GOPS. The large square GEMM is compute-limited under this simplified boundary model, while the 16³ case is bandwidth-limited. The rectangular case is also below the compute roof. Yet this table still omits array occupancy, pipeline fill/drain, burst behavior, scratchpad tiling, and command overhead.

The important conclusion is conditional:

> With the stated data types, boundary, single-transfer assumption, bus width, clock, and operation convention, the smaller or more rectangular examples have insufficient ideal operational intensity to reach the array’s ideal compute roof.

It would be unsafe to conclude that the real kernel reaches the roof shown in the table.

---

## 1.4 Why workload shape changes the architecture answer

Two layers with the same operation count can stress hardware differently.

### Array alignment

A spatial array is easiest to occupy when tile dimensions align with its rows and columns. If one dimension is smaller than the corresponding array dimension, some processing elements lack useful work. If dimensions are not multiples of tile sizes, edge tiles can contain inactive lanes.

A larger array increases peak throughput and can reduce the number of tiles. It also increases the penalty when the workload cannot fill it. Array size is therefore a workload-distribution decision, not a monotonic performance knob.

### The reduction dimension

The reduction dimension `K` affects reuse and the ability to amortize setup costs. Large `K` can keep an array computing after weights or partial sums are placed. Small `K` makes fill, drain, command, and transfer overheads more visible.

### Batch and sequence dimensions

Batching can turn many small matrix operations into shapes that occupy the array more effectively. Interactive or real-time systems may not be allowed to wait for a large batch. Transformer prefill and autoregressive decode illustrate this distinction: the same model can generate large matrix operations during prefill and narrow, latency-sensitive operations during token-by-token decode.

### Operator mix

A model is not one GEMM. Convolution, attention, normalization, softmax, elementwise activation, pooling, layout conversion, and host operations have different reuse and numerical patterns. Accelerating the dominant arithmetic kernel can expose another bottleneck. Amdahl’s law remains relevant: reducing one component cannot improve end-to-end latency beyond the fraction that component originally consumed.

### Dependency structure

Independent tiles can overlap DMA and compute; dependent operators may require barriers or preserve intermediate state. A scheduler can reduce idle time only if the hardware provides queues, buffers, and dependency mechanisms to make overlap legal.

These effects motivate workload suites rather than a single “representative” matrix. The suite should cover distributions of dimensions, operators, and service constraints. Timeloop and MAESTRO were developed in part to make architecture and dataflow evaluation systematic rather than anecdotal [PAR19, KWO19]. SCALE-Sim similarly exposes array, dataflow, aspect-ratio, and bandwidth choices for systolic accelerator studies [SAM18]. Their existence is evidence that mapping and architecture cannot be separated; it is not evidence that their cost models are interchangeable.

### From a graph operator to tensor-unit work

An operator name is not yet an accelerator workload. Before a framework-level matrix multiplication can execute, the compiler/runtime path must determine:

1. concrete tensor shapes, layouts, strides, and datatypes;
2. whether operands are transposed or repacked;
3. accumulation and output semantics;
4. tile dimensions and edge behavior;
5. which dimensions map spatially across PEs and temporally across cycles;
6. scratchpad allocation and whether intermediates are materialized or streamed;
7. DMA descriptors, command order, dependencies, barriers, and legal overlap;
8. output placement and any conversion or requantization.

For `W[M,K] × A[K,N] = O[M,N]`, the semantic path is:

```text
framework operator
   → shapes and numerical contract
   → layout and lowering
   → loop nest and tile schedule
   → W/A/O scratchpad allocation
   → DMA and compute commands
   → architectural state transitions
   → observable operations, bytes, stalls, and results
   → derived metrics under a declared model contract
```

Every arrow is a contract. A compiler schedule can change traffic and occupancy without changing hardware. SRAM capacity can force a different schedule. A sweep that silently changes both cannot identify the cause. TVM provides a broad example of why graph transformations, tensor scheduling, target-specific code generation, and schedule search belong in hardware/software reasoning [CHE18].

---

## 1.9 Formulating a good exploration question

A vague question such as “What is the best PE array?” has no answer. A useful question identifies the workload, alternatives, metric, constraints, and model limits.

A practical template is:

> For workload distribution **W**, under memory configuration **M** and numerical contract **N**, how does architecture choice **A** change metrics **Y**, and which omitted costs could reverse the conclusion?

Example:

> For GEMMs drawn from transformer prefill and decode, under a 32-byte/cycle external transfer path and fixed total SRAM capacity, how do 16×16, 32×8, and 8×32 arrays change modeled utilization, cycles, and traffic? Which conclusions depend on the fill/drain equation, and what area/routing costs are not represented?

A trustworthy experiment then requires:

1. **Hypothesis.** State the expected regime and why.
2. **Controlled alternatives.** Change the intended variable while holding other assumptions explicit.
3. **Executable path.** Prove the configuration is parsed, propagated, consumed, and tested.
4. **Workload coverage.** Include shapes likely to support and falsify the hypothesis.
5. **Metrics.** Name counter source, units, and cycle domain.
6. **Multi-objective interpretation.** Report costs as well as gains.
7. **Fidelity statement.** List modeled and omitted effects.
8. **Reproduction record.** Pin source, config, command, and output.

This method is central to Tusim. The gap-analysis document in the repository is background, not a requirement to implement every imaginable accelerator feature. A feature is justified when it answers an active architecture question or strengthens the model contract.

[Next: Chapter 2 — How an Executable Model Earns Trust](02-how-an-executable-model-earns-trust.md)
