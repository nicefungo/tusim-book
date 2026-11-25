# Tusim: Designing and Exploring Parametric Tensor Units

Second edition · Public simulator snapshot `7a094ff` · [Tested source and verification limits](progress.md)

A tensor unit can return the right matrix even when it runs a different dataflow from the one you requested. This book follows a request from its configuration file to the code that consumes it, then compares the output, the selected implementation and the cycles that implementation charges. Those are three different checks.

For a first run, start with [Chapter 3](manuscript/part-1-foundations/03-repository-tour-and-first-execution.md). Its small matrix has four answers you can check by hand. For a design comparison, read [Chapter 6](manuscript/part-2-core/06-pe-arrays-mma-semantics-and-tiling.md) on partial tiles and [Chapter 21](manuscript/part-2-core/21-designing-a-trustworthy-sweep.md) on testing whether a sweep exercised the intended path.

## Contents

### Part I · Foundations

- [Chapter 1 — Architecture Questions Before RTL](manuscript/part-1-foundations/01-architecture-questions-before-rtl.md)
- [Chapter 2 — How an Executable Model Earns Trust](manuscript/part-1-foundations/02-how-an-executable-model-earns-trust.md)
- [Chapter 3 — Repository Tour and First Execution](manuscript/part-1-foundations/03-repository-tour-and-first-execution.md)

### Part II · The model and its evidence

- [Chapter 4 — Configuration as the Architecture Contract](manuscript/part-2-core/04-configuration-as-the-architecture-contract.md)
- [Chapter 5 — State, Lifecycle, and Public APIs](manuscript/part-2-core/05-state-lifecycle-and-public-apis.md)
- [Chapter 6 — PE Arrays, MMA Semantics, and Tiling](manuscript/part-2-core/06-pe-arrays-mma-semantics-and-tiling.md)
- [Chapter 7 — Pluggable Dataflows](manuscript/part-2-core/07-pluggable-dataflows.md)
- [Chapter 8 — Floating-Point Foundations](manuscript/part-2-core/08-floating-point-foundations.md)
- [Chapter 9 — Memory Hierarchy and Banked Scratchpads](manuscript/part-2-core/09-memory-hierarchy-and-banked-scratchpads.md)
- [Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution](manuscript/part-2-core/10-dma-descriptor-contracts-and-tick-driven-execution.md)
- [Chapter 11 — Instruction Surfaces and Command-Queue Ordering](manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md)
- [Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates](manuscript/part-2-core/12-multi-core-clusters-and-interconnect-heuristics.md)
- [Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression](manuscript/part-2-core/13-weight-streams-quantization-sparsity-compression.md)
- [Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics](manuscript/part-2-core/14-operator-compute-engines-functional-semantics-and-engine-metrics.md)
- [Chapter 15 — DRAM Service Models and Bandwidth Claims](manuscript/part-2-core/15-dram-service-models-and-bandwidth-claims.md)
- [Chapter 16 — Double Buffering and Legal Overlap](manuscript/part-2-core/16-double-buffering-and-legal-overlap.md)
- [Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy](manuscript/part-2-core/17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md)
- [Chapter 18 — Runtime Context Retention and Preemption Boundaries](manuscript/part-2-core/18-runtime-context-retention-and-preemption-boundaries.md)
- [Chapter 19 — Static Scheduling and Scratchpad Allocation](manuscript/part-2-core/19-static-scheduling-and-scratchpad-allocation.md)
- [Chapter 20 — Verification as an Architectural Feature](manuscript/part-2-core/20-verification-as-an-architectural-feature.md)
- [Chapter 21 — Designing a Trustworthy Sweep](manuscript/part-2-core/21-designing-a-trustworthy-sweep.md)
- [Chapter 22 — Lessons from the Exploration Portfolio](manuscript/part-2-core/22-lessons-from-the-exploration-portfolio.md)

### Part III · Extending the model

- [Chapter 23 — Extending Tusim Without Breaking Its Contract](manuscript/part-3-practice/23-extending-tusim-without-breaking-its-contract.md)

## Reading the results

Use the [chapter evidence summaries](evidence-matrix.md) to distinguish a derivation from a run, and a historical result from a check at the second-edition pin. The [progress report through S16](progress.md) identifies what was independently reproduced. The [glossary](glossary.md) explains which component owns a counter or a state transition.

This reader edition preserves the chapter and section numbers of the sealed manuscript. Some sections are abridged: internal run records are described rather than redistributed. The ordinary matrix driver and its configuration remain available in Chapter 3. See the [edition note](progress.md#what-changed-for-public-readers) for the differences.
