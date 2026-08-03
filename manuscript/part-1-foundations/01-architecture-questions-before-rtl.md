# Chapter 1 — Architecture Questions Before RTL

> **Edition scope:** Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`  
> **Evidence status:** conceptual foundations supported by primary literature; Tusim-specific statements supported by the pinned repository and initial executable audit.

## Learning objectives

After this chapter, you should be able to:

1. explain why a tensor accelerator is a data-movement system rather than merely a collection of multiply–accumulate units;
2. distinguish peak throughput from achieved throughput, latency, utilization, and energy efficiency;
3. use operational intensity to identify a first-order compute or bandwidth limit;
4. explain why workload shape, mapping, memory hierarchy, dataflow, precision, and scheduling must be explored together;
5. formulate an architecture question that a CModel can answer without pretending that it is RTL;
6. place Tusim within a heterogeneous accelerator and compiler stack;
7. identify conclusions that are safe at the pre-spec stage and conclusions that require more detailed models or physical implementation.

## Prerequisites

This chapter assumes matrix multiplication and introductory computer architecture. No knowledge of Tusim is required. Later chapters will define the exact W/A/O layout, cycle models, dataflows, numerical formats, and APIs.

### Tusim as a decision instrument

Tusim should not be understood first as a directory of accelerator features. It is a **decision instrument**: a family of executable hypotheses about a tensor-unit subsystem. Each hypothesis has a system boundary, a workload and mapping, architecture parameters, environmental assumptions, observables, derived metrics, and uncertainty. A run is useful only when those elements are explicit enough to support or reject a concrete design decision.

The following ontology will be used throughout the book:

- a **workload property** describes the problem presented to the accelerator, such as shape, operator, dependency, datatype, or sparsity pattern;
- a **compiler policy** chooses lowering, layout, tiling, fusion, scheduling, and placement;
- an **architecture parameter** describes capacity or organization, such as PE dimensions or SRAM size;
- a **microarchitectural mechanism** defines behavior, such as a dataflow, DMA queue, pipeline, or arbitration policy;
- an **environmental assumption** describes context not owned by the modeled subsystem, such as external bandwidth or host overhead;
- a **model state** is internal state used to represent architectural behavior;
- an **observable** is a directly reported event or value, such as bytes transferred or commands completed;
- a **derived metric** combines observables under a declared equation and boundary;
- a **calibration parameter** is fitted or selected using a named external reference;
- a **decision criterion** states how alternatives will be compared under constraints.

This vocabulary prevents a compiler effect from being mistaken for a hardware effect, an assumption from being mistaken for a parameter, or a derived estimate from being described as a measurement.

---

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

\[
P_{peak}=2RCf,
\]

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

\[
P \le \min(P_{peak}, B I).
\]

If `BI < P_peak`, the chosen memory boundary imposes the lower roof. If `BI > P_peak`, arithmetic capacity imposes the lower roof. This classification is not a cycle simulation. It is a bound that tells us where to investigate next.

### The boundary is part of the definition

Operational intensity is meaningless without a memory boundary. Bytes transferred from DRAM differ from bytes read from a global buffer, scratchpad, register file, or PE-local storage. Reuse can increase intensity at one boundary while leaving another unchanged.

For a dense matrix multiplication

\[
O_{M\times N}=W_{M\times K}A_{K\times N},
\]

an ideal compulsory-traffic estimate with FP16 inputs and FP32 output is

\[
Q = 2MK + 2KN + 4MN \quad \text{bytes},
\]

and useful arithmetic under the two-operations-per-MAC convention is

\[
F=2MNK.
\]

The corresponding ideal operational intensity is

\[
I=\frac{2MNK}{2MK+2KN+4MN}.
\]

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

## 1.5 Dataflow is a physical and software decision

A dataflow specifies where values remain stationary, where they move, and when they are reused. Common labels include weight-stationary, output-stationary, and row-stationary, but a label alone is not a complete mapping. Tile sizes, loop order, spatial assignment, temporal schedule, and hierarchy placement determine actual traffic.

Consider three broad intentions:

- **weight-stationary:** keep weights close to PEs while activations and partial sums move;
- **output-stationary:** retain partial sums while weights and activations stream;
- **row-stationary:** arrange computation to exploit multiple forms of reuse across rows of convolution-like work. Eyeriss is the canonical silicon-backed reference for this family and emphasizes reuse of weights, activations, and partial sums through hierarchical storage [CHE16].

A dataflow changes:

- register and local-storage requirements;
- operand fanout and interconnect pressure;
- partial-sum movement;
- fill and drain behavior;
- achievable occupancy for different shapes;
- compiler mapping complexity.

No dataflow is universally optimal. Timeloop reports the importance of memory-hierarchy/dataflow co-design and explicitly observes flexibility–efficiency trade-offs across workloads [PAR19]. MAESTRO provides a data-centric language for describing spatial and temporal mapping and analyzing reuse and occupancy [KWO19].

Tusim preserves multiple dataflow modes because it is a pre-spec exploration model. The goal is not to switch to whichever mode wins one local benchmark and delete the rest. The goal is to understand the workload regimes and hardware costs under which each mode is plausible. Chapter 7 will inspect Tusim's plugin interface and test the current WS, OS, and RS paths.

---

## 1.6 Precision changes more than arithmetic density

Changing FP16 to INT8 or FP8 can reduce operand storage and traffic and may allow more multipliers per area. It also changes:

- accumulator width and overflow behavior;
- rounding and saturation;
- subnormal, NaN, and infinity handling;
- scale/zero-point metadata;
- conversion hardware;
- calibration or training requirements;
- reproducibility and verification complexity.

A throughput gain inferred only from smaller payload bytes is incomplete. If a decoder, dequantizer, metadata path, or accumulator becomes the bottleneck, the end-to-end gain can be smaller or negative. Likewise, sparsity and compression reduce useful payload only when the representation, decoder, scheduling, and memory system can exploit them.

Tusim includes several numerical formats, rounding modes, integer quantization, structured sparsity, and weight-compression models. Later chapters will treat these as architecture alternatives with accuracy and implementation costs, not as a list of checkboxes.

---

## 1.7 From isolated accelerator to full system

An isolated array model can answer important questions, but a deployed accelerator shares a system.

Gemmini was motivated by the observation that accelerators are often evaluated without full-stack effects such as SoC contention, operating-system overhead, and programming-stack inefficiency [GEN21]. The production TPU analysis likewise evaluates workloads and service constraints rather than only a matrix unit [JOU17]. These examples motivate a layered evaluation strategy:

1. **kernel semantics:** does the operator produce the intended result?
2. **microarchitecture:** how do geometry, dataflow, buffers, and pipelines behave?
3. **accelerator subsystem:** how do command queues, DMA, scratchpads, and engines interact?
4. **compiler/runtime:** can workloads be mapped, tiled, scheduled, and synchronized?
5. **SoC/system:** what contention, host overhead, coherence, and communication occur?
6. **application/service:** what latency distribution, throughput, accuracy, energy, and cost result?

A model should state which layers it represents. Claiming system performance from a kernel-only model is a category error.

### Tusim's system boundary

Tusim models the tensor-unit sub-architecture of a larger heterogeneous accelerator. The repository describes a context in which a compiler frontend partitions work among a host, an SU/GPU-like engine, and the TU. Tusim receives TU-oriented commands and models configurable tensor-unit components:

```text
Model / graph
    │
    ▼
Compiler and partitioning
    │        host/SU work is outside Tusim's main scope
    └── TU commands / TU ASM
             │
             ▼
      command queue and scheduler
             │
      ┌──────┴─────────┐
      ▼                ▼
 DMA / memory       compute engines
      │                │
      └──────┬─────────┘
             ▼
       counters / traces
```

The pinned repository contains a C library, configuration system, memory and compute modules, TU ISA/ASM, a demonstration ONNX compiler, tests, bindings, and exploration harnesses. It is broad enough to expose cross-layer questions, but it is not a complete model of every host and SoC effect. This boundary will be repeated throughout the book.

---

## 1.8 What a pre-spec CModel is for

Before the hardware specification is locked, exact implementation details do not yet exist. A useful CModel should therefore help eliminate bad assumptions and expose trade-offs without pretending to know nonexistent RTL timing.

### Questions it can answer

Subject to its implemented paths and fidelity labels, Tusim can support questions such as:

- At what workload shapes does a larger PE array lose occupancy?
- Which SRAM capacity avoids a particular tiling threshold?
- When does a wider DMA path cease to improve modeled latency?
- How do WS, OS, and RS differ under the same functional workload?
- When can double buffering hide modeled transfer time?
- How does a decoder width change the benefit of compressed weights?
- Under a stated traffic matrix and deterministic route-load heuristic, where do ring and mesh alternatives reverse ranking?
- Which numerical modes preserve required error properties?

### Questions it cannot answer alone

Without additional calibration or physical models, it cannot establish:

- final clock frequency or timing closure;
- sign-off area, power, thermal behavior, or SRAM compiler results;
- exact NoC behavior with finite queues and real arbitration when those are omitted;
- end-to-end application latency including unmodeled host/runtime work;
- model accuracy without the full workload, data, and numerical graph;
- cycle equivalence to RTL that has not been specified and compared.

The distinction is productive rather than limiting. A fast analytical or functional model can explore many alternatives, while RTL can validate a smaller number of selected candidates. The models answer different questions.

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

---

## 1.10 A reasoning loop that can improve the code

A technical textbook should not merely describe a codebase. Formal explanations, literature comparison, and exercises can reveal inconsistencies that ordinary development misses.

Consider the following loop:

1. **Define the quantity.** What exactly is a “cycle,” “stall,” “utilization,” or “energy” value?
2. **Derive the invariant.** What relationship must hold independent of implementation?
3. **Map it to code.** Which state and function implement the definition?
4. **Construct counterexamples.** Which shapes or modes stress the assumption?
5. **Run the model.** Does executable behavior match the definition?
6. **Compare externally.** Under identical mappings, how does another model, RTL, or measured system behave?
7. **Refine deliberately.** Change code only when the desired fidelity and verification strategy are clear.

The initial source audit already exposes research questions. Tusim has basic `g_tu` cycle counters and a separate performance-counter subsystem; not every engine returns the same kind of cycle value. Interconnect sweeps report deterministic route-load heuristic estimates rather than finite router queues or proved makespan bounds. The grouped-convolution estimate omits costs that become important for depthwise workloads. These are not details to hide. They are examples of how precise textbook definitions can guide future development.

---

## 1.11 Chapter summary

A tensor unit is not defined by its MAC count. It is a coupled compute, memory, communication, numerical, scheduling, compiler, and system design.

The main principles are:

1. Peak throughput is a roof, not achieved performance.
2. Operational intensity provides a first-order compute/bandwidth classification only after the memory boundary and traffic assumptions are defined.
3. Workload shape and mapping determine occupancy, reuse, and setup amortization.
4. Dataflow is both a hardware organization and a compiler mapping decision.
5. Precision, sparsity, and compression trade data volume and arithmetic density against accuracy, metadata, decoding, and verification cost.
6. Kernel, accelerator, SoC, and application models answer different questions.
7. A pre-spec CModel is most valuable when it compares plausible alternatives, states fidelity limits, and generates falsifiable architecture hypotheses.
8. Clear exposition and primary-source comparison can expose model inconsistencies and inspire disciplined code improvements.

The next chapter develops the fidelity framework required to know when a Tusim result is a functional fact, an analytical estimate, a deterministic lower bound, or a claim that still needs RTL or silicon calibration.

---

## Review questions

1. Why can increasing PE count reduce achieved efficiency for a fixed workload distribution?
2. Give three different definitions of utilization and an example where they disagree.
3. Why must operational intensity name a memory boundary?
4. Under what assumptions does `P ≤ min(P_peak, BI)` hold as a useful bound?
5. Why can batching improve throughput while violating a latency objective?
6. How can two dataflows produce the same numerical result but different traffic and cycle estimates?
7. Why does halving weight payload not imply halving layer latency?
8. Which system effects are lost when only an isolated matrix array is modeled?
9. Rewrite “Which interconnect is best?” as a falsifiable exploration question.
10. What evidence would be needed to promote an estimated cycle model to a calibrated model?

## Design exercises

### Exercise 1 — Boundary sensitivity

For one GEMM, compute operational intensity at the DRAM, global-buffer, and PE-local boundaries under explicitly chosen reuse assumptions. Explain why the three values differ.

### Exercise 2 — Workload distribution

Construct a five-shape suite that includes a square GEMM, a tall-skinny GEMM, a small reduction dimension, a non-aligned edge case, and a decode-like matrix-vector regime. Predict which shapes will underutilize a square array and state the assumptions behind your prediction.

### Exercise 3 — Multi-objective array choice

Compare 16×16, 32×8, and 8×32 arrays at equal PE count. Discuss occupancy, operand broadcast, routing regularity, buffer access, compiler mapping, and verification. Do not select a winner without a workload distribution.

### Exercise 4 — Model boundary

Draw a boundary around Tusim in a hypothetical SoC. List five effects inside the boundary and five outside it. For each outside effect, identify the weakest additional model that could represent it usefully.

### Exercise 5 — Evidence ladder

Choose one claim from an exploration report. Classify its current evidence as formula inspection, unit test, integration test, cross-model comparison, RTL/FPGA comparison, or silicon calibration. Design the next validation step.

---

## Primary references

- [KUN82] H. T. Kung, “Why Systolic Architectures?,” 1982. DOI: https://doi.org/10.1109/MC.1982.1653825
- [WAT09] S. Williams, A. Waterman, and D. Patterson, “Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures,” 2009. DOI: https://doi.org/10.1145/1498765.1498785
- [JOU17] N. P. Jouppi et al., “In-Datacenter Performance Analysis of a Tensor Processing Unit,” 2017. DOI: https://doi.org/10.1145/3079856.3080246
- [CHE16] Y.-H. Chen, J. Emer, and V. Sze, “Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,” 2016. DOI: https://doi.org/10.1109/ISCA.2016.40
- [SAM18] A. Samajdar et al., “SCALE-Sim: Systolic CNN Accelerator Simulator,” arXiv:1811.02883v2
- [PAR19] A. Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” 2019. DOI: https://doi.org/10.1109/ISPASS.2019.00042
- [KWO19] H. Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” 2019. DOI: https://doi.org/10.1145/3352460.3358252
- [GEN21] H. Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” 2021. DOI: https://doi.org/10.1109/DAC18074.2021.9586216
- [CHE18] T. Chen et al., “TVM: An Automated End-to-End Optimizing Compiler for Deep Learning,” OSDI 2018. https://www.usenix.org/conference/osdi18/presentation/chen

Detailed bibliographic notes and permitted claim scopes are maintained in `book/references/foundations.md`.
