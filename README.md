# Tusim Book

**Working title:** *Tusim: Designing and Exploring Parametric Tensor Units*
**Edition:** stable-main snapshot `e918c80`
**Canonical language:** English

This directory contains the source-backed technical/academic reference book for Tusim.

## Current manuscript

- [Chapter 1 — Architecture Questions Before RTL](manuscript/part-1-foundations/01-architecture-questions-before-rtl.md) — revised first complete draft
- [Chapter 2 — How an Executable Model Earns Trust](manuscript/part-1-foundations/02-how-an-executable-model-earns-trust.md) — complete first draft; executable audit reproduced; independently reviewed and validated
- [Chapter 3 — Repository Tour and First Execution](manuscript/part-1-foundations/03-repository-tour-and-first-execution.md) — complete first draft; clean build, smoke/config tests, direct C execution, compiler/docs/CI audit reproduced
- [Chapter 4 — Configuration as the Architecture Contract](manuscript/part-2-core/04-configuration-as-the-architecture-contract.md) — complete first draft; enforced surface audit and propagation/effect probes reproduced; 9 skeptical-review findings resolved
- [Chapter 5 — State, Lifecycle, and Public APIs](manuscript/part-2-core/05-state-lifecycle-and-public-apis.md) — complete first draft; live ownership/lifecycle audit, discriminating probe, leak-sanitizer reproduction, and skeptical review resolved
- [Chapter 6 — PE Arrays, MMA Semantics, and Tiling](manuscript/part-2-core/06-pe-arrays-mma-semantics-and-tiling.md) — complete first draft; enforced geometry/capacity audit, focused/golden/random execution, subnormal-defect reproduction, and three independent reviews resolved
- [Chapter 7 — Pluggable Dataflows](manuscript/part-2-core/07-pluggable-dataflows.md) — complete first draft; fail-closed WS/OS/RS equivalence/timing audit and three independent skeptical reviews resolved
- [Chapter 8 — Floating-Point Foundations](manuscript/part-2-core/08-floating-point-foundations.md) — complete first draft; independent conformance checks and pinned known-defect snapshot reproduced
- [Chapter 9 — Memory Hierarchy and Banked Scratchpads](manuscript/part-2-core/09-memory-hierarchy-and-banked-scratchpads.md) — complete first draft; expanded isolated audit reproduced and three independent skeptical reviews resolved
- [Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution](manuscript/part-2-core/10-dma-descriptor-contracts-and-tick-driven-execution.md) — complete first draft; hash-guarded descriptor audit reproduced and independent architecture, evidence, and editorial reviews resolved
- [Chapter 11 — Instruction Surfaces and Command-Queue Ordering](manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md) — complete first draft; exact-pin instruction/queue audit and adversarial lifecycle probe reproduced; technical, editorial, and reproducibility findings resolved and independently re-reviewed
- [Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates](manuscript/part-2-core/12-multi-core-clusters-and-interconnect-heuristics.md) — complete first draft; canonical-v5 evidence reseal passed; clean technical, editorial, and reproducibility re-review passed
- [Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression](manuscript/part-2-core/13-weight-streams-quantization-sparsity-compression.md) — complete first draft; canonical-v8 evidence seal passed; skeptical pre-draft and independent technical/editorial/reproducibility review findings resolved
- [Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics](manuscript/part-2-core/14-operator-compute-engines-functional-semantics-and-engine-metrics.md) — complete first draft; canonical-v3 evidence seal passed; skeptical pre-draft and independent technical/editorial/reproducibility review findings resolved
- [Chapter 15 — DRAM Service Models and Bandwidth Claims](manuscript/part-2-core/15-dram-service-models-and-bandwidth-claims.md) — complete first draft; canonical-v3 evidence seal passed; independent technical/editorial/reproducibility review findings resolved and clean re-review passed
- [Chapter 16 — Double Buffering and Legal Overlap](manuscript/part-2-core/16-double-buffering-and-legal-overlap.md) — complete first draft; fail-fast canonical-v4 evidence seal passed; independent technical, skeptical-continuity, and editorial findings resolved; exact-commit review closed
- [Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy](manuscript/part-2-core/17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md) — complete first draft; canonical-v4 evidence seal passed; independent technical, editorial, and reproducibility findings resolved; exact-commit re-review closed
- [Chapter 18 — Runtime Context Retention and Preemption Boundaries](manuscript/part-2-core/18-runtime-context-retention-and-preemption-boundaries.md) — complete first draft; canonical-v7 evidence seal passed; independent technical, editorial, and reproducibility findings resolved; exact-commit review and governance re-review closed
- [Chapter 19 — Static Scheduling and Scratchpad Allocation](manuscript/part-2-core/19-static-scheduling-and-scratchpad-allocation.md) — complete first draft; postreview-v3 evidence seal passed; independent technical, editorial, and reproducibility findings resolved; exact-commit re-review and reviewed-snapshot closure passed
- [Chapter 20 — Verification as an Architectural Feature](manuscript/part-2-core/20-verification-as-an-architectural-feature.md) — complete manuscript; postreview-v2 evidence seal passed; independent technical, editorial, and reproducibility findings resolved; reviewed-snapshot release closure passed
- [Chapter 21 — Designing a Trustworthy Sweep](manuscript/part-2-core/21-designing-a-trustworthy-sweep.md) — complete manuscript; corrected postreview-v8 evidence seal passed; independent technical, editorial, and reproducibility findings resolved; final exact-commit re-review passed

## Editorial foundations

- [Edition manifest](edition.yaml)
- [Style, evidence, and cross-session writing principles](style-guide.md) — authoritative editorial contract
- [Stable-snapshot source audit](source-audit.md)
- [Fidelity matrix](fidelity-matrix.md)
- [Verified foundation references](references/foundations.md)

## Writing status

| Item | Status |
|---|---|
| Edition freeze | complete |
| Initial clean build and smoke verification | complete |
| Initial source/fidelity audit | complete; deeper per-module audit continues with relevant chapters |
| Foundational literature map | expanded and independently verified |
| Chapter 1 | revised first complete draft |
| Chapter 2 | complete 6,128-word first draft; mechanical validation and independent skeptical review passed |
| Chapter 3 | complete 5,397-word first draft; executable audit reproduced; 11 skeptical-review findings resolved and revalidated |
| Chapter 4 | complete 7,296-word first draft; clean build and 20/20 config tests pass; enforced pinned audit and runtime propagation/effect probe pass; 9 skeptical-review findings resolved |
| Chapter 5 | complete 3,118-word first draft; clean build and focused direct/queue/ASM/multicore/status tests pass; ownership probe passes; LeakSanitizer result reproduced; skeptical review resolved |
| Chapter 6 | complete 5,512-word first draft; clean isolated build, 19/19 cmodel, 9/9 dataflow, 11/11 golden, quick random, enforced tiling audit, and revised geometry/subnormal probe pass; three independent reviews resolved |
| Chapter 7 | complete 6,236-word first draft; verified full source archive, 15/15 claim-source audit, clean static build, 9/9 dataflow, 20/20 config, 16/16 multicore, 13/13 DPI, fail-closed WS/OS/RS probe, static-link gates, and three independent reviews resolved; existing sweep challenged rather than accepted |
| Chapter 8 | complete 5,849-word first draft; verified full source archive, 17/17 claim-source audit, 19/19 cmodel, 20/20 config, 12/12 BF16, 14/14 rounding, 21/21 FP8, 25/25 TF32, 9/9 dataflow, 11/11 golden, exhaustive FP16/FP8 decode checks, three digest-closed engine-local snapshots, and nine static-link gates pass; three independent skeptical reviews resolved |
| Chapter 9 | complete 4,335-word first draft; verified full source archive, 24/24 claim-source audit, 10/10 hierarchy functions, 19/19 cmodel cases, observed 20/20 config run (harness not fail-closed), expanded banking/refill/reset/config/integration probe, and four static-link gates pass; three independent skeptical reviews resolved |
| Chapter 10 | complete 5,566-word first draft; canonical hash-guarded run reproduces 65/65 source checks, focused descriptor/scatter-gather/multicast evidence, the known 12/13 address-generator result, intentional unsafe-pipeline skip, and zero-failure custom probes; architecture, repository, evidence, and editorial blockers resolved |
| Chapter 11 | complete 6,085-word first draft; canonical run reproduces 26 source hashes, 96 structural/reachability predicates, five static-link gates, queue 9/9, ISA 9/9, ASM PASS, scheduler 14/14, and a zero-failure adversarial probe; pre-draft and manuscript architecture/editorial/reproducibility findings resolved |
| Chapter 12 | complete 6,893-word first draft; canonical-v5 reproduces 28 source hashes, 155 structural/reachability predicates, 183 total source checks, 16/16 focused multicore tests, forced 15/16 mutation failure, the exact heuristic counterexample, retained pre-draft validation, and outer bundle closure; clean technical, editorial, and reproducibility re-review passed |
| Chapter 13 | complete 5,624-word first draft; canonical-v8 reproduces 25 source hashes, 138 structural/reachability predicates, 163 total source checks, 14/14 int-quant, 27/27 sparsity, 24/24 compress, forced 26/27 mutation failure, exact byte/estimate probe findings, retained pre-draft validation, and outer bundle closure; skeptical pre-draft review and independent technical/editorial/reproducibility review findings resolved |
| Chapter 14 | complete 6,100-word first draft; canonical-v3 reproduces 28 source hashes, 46 structural/reachability predicates, 74 total source checks, 16/16 elementwise, 11/11 norm, 12/12 conv, 14/14 pool, 11/11 pipeline, 15/15 standalone softmax, qualified attention (6–8/9 rc=1, UB-dependent failing subset, never 9/9), forced 14/15 softmax mutation, the metric census (96/80/40) and exact engine probe findings, retained pre-draft validation, and outer bundle closure; skeptical pre-draft review and independent technical/editorial/reproducibility review findings resolved |
| Chapter 15 | complete 6,450-word first draft; canonical-v3 reproduces 23 source hashes, 62 structural/reachability predicates, 85 total checks, DRAM 12/12, hierarchy 10/10, source-linked cycle model 21/21, power 20/20, forced 11/12 mutation with inferior code 01, expanded state-machine/64-byte-sentinel probe, four historical-sweep contradictions, immutable manifest, and 13-file predraft validation; independent technical/editorial/reproducibility review findings resolved and clean re-review passed |
| Chapter 16 | complete 7,878-word first draft; fail-fast canonical-v4 reproduces 31 source hashes, 60 structural/reachability predicates, 91 checks, standalone DB 10/10, forced 9/10 mutation, exact stale-bridge/controller/lifecycle probes, ten historical rows, discrete threshold and shared-resource discriminators, AddressSanitizer lifecycle control, immutable manifests, and fail-closed predraft/manuscript validation; independent findings resolved and exact-commit review closed |
| Chapter 17 | complete 6,089-word first draft; canonical-v4 reproduces 31 source hashes, 96 structural/reachability predicates, 127 checks, focused perf/trace/cycle/power suites, exact additive/reset/diff/merge/direction/unit probes, immutable 43-entry retained and four-entry outer manifests, and fail-closed predraft/manuscript validation with real assertion mutation under normal and optimized Python; independent findings resolved and exact-commit re-review closed |
| Chapter 18 | complete 8,093-word first draft; canonical-v7 reproduces 39 source hashes, 171 structural predicates, 210 checks, exactly 19 public APIs and zero external non-test callers, context 15/15, real mutation 14/15, 12 exact sweep rows, 45 transition labels, byte-identical O0/O2/sanitizer probe output, immutable 45-entry retained and four-entry outer manifests, and fail-closed manuscript validation with 25 reader-claim mutations; independent technical/editorial/reproducibility findings resolved and reviewed-snapshot closure passed |
| Chapter 19 | complete 6,754-word first draft; postreview-v3 reproduces 15 sealed inputs, 182 source checks, 128 opcode rows, exact scheduler/liveness boundary probes, immutable 46-entry body and five-entry outer manifests, complete-probe digest binding, and fail-closed manuscript validation with 23 reader-claim mutations under normal and optimized Python; independent technical/editorial/reproducibility findings resolved, exact-commit re-review passed, and reviewed-snapshot release closure passed |
| Chapter 20 | complete 8,559-word manuscript; postreview-v2 seals 22 hashes, 52 predicates, 75 source checks, a 63-file exact evidence bundle, normal/O2 byte-identical claim probe, 23 verbatim limitations, and fail-closed manuscript validation with 64 reader-visible plus 23 limitation mutations under normal and optimized Python; independent technical/editorial/reproducibility findings resolved and final exact-commit review passed |
| Chapter 21 | complete 8,084-word manuscript; corrected postreview-v8 seals 21 source hashes, 26 predicates, 48 source checks, 61 retained payload members and a 71-file exact evidence tree, byte-identical O0/O2 route/plugin probes, source-derived linked-plugin totals, 12 verbatim limitations, and fail-closed manuscript validation with 63 reader-visible plus 12 limitation mutations under normal and optimized Python; final technical/editorial/reproducibility re-review passed at `c71a3d6` |

## Evidence policy

The book gives precedence to executable behavior and tests at the pinned commit. Historical documents are used for rationale only when they agree with current behavior or are explicitly labeled historical. Quantitative claims identify assumptions, cycle domain, modeled omissions, and calibration status.
