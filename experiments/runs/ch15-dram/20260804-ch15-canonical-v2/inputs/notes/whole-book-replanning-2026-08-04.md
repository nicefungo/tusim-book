# Whole-Book Replanning Review — 2026-08-04

## Decision

The first edition is replanned from 29 proposed chapters to **22 governed chapters plus appendices**. Chapters 1–14 keep their numbers, filenames, evidence seals, and current order. The remaining sequence is:

15. DRAM Service Models and Bandwidth Claims
16. Double Buffering and Legal Overlap
17. Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy
18. Resource Multiplexing: Contexts, Scheduling, and Scratchpad Liveness
19. Verification as an Architectural Feature
20. Designing a Trustworthy Sweep
21. Lessons from the Exploration Portfolio
22. Extending Tusim Without Breaking Its Contract

This review is the evidence record for the corresponding revisions in `PLAN.md`.

## Review method

The review compared:

- the historical 29-chapter proposal at `/home/zxy/.hermes/plans/2026-07-25_095253-tusim-book-plan.md`;
- all 14 manuscripts and the available Chapter 9–14 framing plans;
- `fidelity-matrix.md` and all 39 findings in `source-audit.md`;
- live library membership and test provenance in the pinned Makefile;
- source, focused tests, documentation, exploration reports, and non-test callers at Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`;
- three independent read-only reviews: historical-plan coverage, remaining-source reconnaissance, and alternative whole-book structures.

Coverage is judged by whether a chapter teaches the original **reader decision and fidelity boundary**, not by keyword presence. This rule caused one correction after the first draft of the review: Chapters 9/10/14 mention, exclude, or bound the double-buffer surface, but they do not teach `double_buffer.[ch]`. Historical Plan 15 therefore remains as a dedicated Chapter 16.

## Coverage review of the historical plan

| Historical plan | Evidence in the written book | Replanning disposition |
|---|---|---|
| 1–7: purpose, trust, repository, config, lifecycle, PE/MMA, dataflow | Actual Chapters 1–7 provide the intended reader decisions and executable boundaries. | Keep as Chapters 1–7. |
| 8–10: floating-point foundations; BF16/FP8/TF32; rounding/reproducibility | Chapter 8 has dedicated source maps and sections for BF16, FP8, TF32, RNE/RTZ/stochastic rounding, subnormals, special values, executable boundary matrices, and format-specific defects. | Treat all three historical chapters as folded into Chapter 8. Preserve any additional rounding sweeps for the portfolio chapter; reconsider a split only if integrated precision dispatch or model-level accuracy evidence appears. |
| 11: integer quantization, sparsity, compression | Chapter 13 covers the full weight-representation decision and proves the three surfaces are adjacent, not one integrated feed. | Keep as Chapter 13; do not move or renumber. |
| 12: banked SRAM and hierarchy | Chapter 9 covers three incompatible memory surfaces and raw-pointer/integration boundaries. | Keep as Chapter 9. |
| 13: DMA/descriptors/address generation | Chapter 10 covers descriptor geometry, lifecycle, ownership, clocks, ordinary-operation reachability, and the retained 12/13 address-generator failure. | Keep as Chapter 10. |
| 14: DRAM and bandwidth | DRAM is mentioned in Chapters 2, 4, 9, and 10, but no chapter audits the standalone access clock, estimator, presets, statistics, config path, or historical DRAM sweep. | Remaining; becomes Chapter 15. |
| 15: double buffering/software pipelines | Chapters 9 and 10 establish bank/DMA prerequisites and explicit non-integration boundaries; Chapter 14 audits a separate pipeline controller. None teaches the standalone active/shadow state machine, swaps, stats, tests, or its own sweeps. | Remaining; becomes Chapter 16. It must teach adjacent alternatives and missing bridges without inventing an integrated pipeline. |
| 16: command queue/synchronization | Chapter 11 covers ordering, dependency, completion, signaling, barrier, reset, and reclamation contracts. | Fully covered in Chapter 11. |
| 17–20: operator engines | Chapter 14 deliberately unifies seven engines through a return-value/metric census and records the attention FP16 staging defect. | Folded into Chapter 14; retain operator-specific architecture regimes for the portfolio chapter rather than duplicate source audits. |
| 21: ISA/ASM | Chapter 11 separates packed metadata, text ASM, and queue dispatch rather than inventing one stack. | Fully covered in Chapter 11. |
| 22: scheduling/liveness | Chapter 11 audits the scheduler's fixed-cost DAG model but explicitly defers liveness allocation and spill/fill semantics. | Scheduler foundation covered; remaining liveness/resource-allocation decision moves to Chapter 18. |
| 23: ONNX compiler | Chapter 3 proves inspected generated programs have zero TU ops and fail to link on undefined `host_gemm`; Chapter 11 proves no compiler→scheduler→queue bridge. | No dedicated first-edition chapter at this pin. Preserve the negative boundary in Chapters 3/11; revisit if an end-to-end path exists. |
| 24: multicore/interconnect/contexts | Chapter 12 covers multicore and interconnect surfaces but not context save/restore. | Contexts move to Chapter 18, adjacent to but explicitly distinct from scheduler/liveness. |
| 25: counters/cycle/trace/energy | Current chapters contain local producer warnings. `performance_counters`, `event_trace`, and `power_model` are linked and tested; `cycle_model` is source-present but absent from `TU_OBJS`. | Remaining; becomes Chapter 17, organized around metric provenance rather than summation. |
| 26: verification | Verification practice is pervasive, but no chapter teaches the complete architecture-level decision across golden, differential, config, mutation, CI, replay, error, DPI, and binding surfaces. | Remaining; becomes Chapter 19. |
| 27–29: sweeps, portfolio synthesis, extension | Individual chapters challenge reports, but the closing methodology and synthesis arc has not been written. | Retain as Chapters 20–22. |

## Why Chapter 15 is next

The DRAM surface has a coherent, still-unclaimed reader decision: **which output is a local service estimate, which is stateful access accounting, and when may either support a bandwidth claim?** It has sufficient primary evidence for a full chapter:

- linked `tu_cmodel/memory/dram_model.[ch]`;
- aggregate `tests/test_dram.c`;
- `docs/dram-model.md` and `docs/bandwidth-modeling.md`;
- `docs/exploration/dram-type-clock-sweep.md` and adjacent crossover reports;
- an explicit integration boundary because descriptor DMA never calls the model.

Fresh inspection establishes chapter-grade challenges:

1. the first non-ideal access starts with a zero bandwidth budget and receives a window stall;
2. access calls return base latency separately from stall and do not advance `current_cycle`;
3. channel availability is recorded without queued completion;
4. row mode adds a flat ten-cycle read penalty and counts every read as a conflict, without row state or corresponding write logic;
5. the stateless estimator uses `ceil(bytes / GB/s-at-assumed-1-GHz) + latency`;
6. `tu_dram_set_core_clock()` is a no-op while other helpers independently accept or assume a clock;
7. derived bandwidth divides cumulative bytes by caller-advanced time and can exceed declared peak;
8. several preset geometry fields are descriptive in the executable path;
9. config declarations do not establish runtime or descriptor-DMA propagation.

These boundaries make Chapter 15 more than a technology table and prevent the historical sweep from being presented as standalone-model execution.

## Structural alternatives considered

### Alternative A — Renumber and physically reorder by topic

Move Chapter 13 beside Chapter 8, insert DRAM and double buffering after Chapter 10, and move operator engines later.

**Benefit:** conventional numerics→memory→engines sequence.
**Cost:** invalidates stable chapter identifiers, links, handoffs, review references, and sealed-evidence narratives without changing technical truth.
**Disposition:** rejected for this snapshot edition.

### Alternative B — Preserve all 29 chapters

Write separate BF16/FP8/TF32, rounding, four operator, and ONNX chapters in addition to the remaining subsystem chapters.

**Benefit:** regular topic granularity and historical-plan fidelity.
**Cost:** duplicates sealed Chapters 8 and 14 and overweights a broken compiler path.
**Disposition:** rejected.

### Alternative C — Over-compress to 21 chapters

Treat double buffering as folded into Chapters 9/10/14.

**Benefit:** shortest remaining sequence.
**Cost:** confuses mention-level and boundary coverage with reader-decision coverage; omits a linked, focused-tested, documented, sweep-backed state machine and its materially distinct architecture trade-offs.
**Disposition:** rejected after independent coverage audit.

### Alternative D — Preserve completed numbering and compress only true duplicates

Keep Chapters 1–14 immutable; write DRAM, double buffering, measurement, resource multiplexing, verification, and the exploration/extension close.

**Benefit:** preserves evidence provenance while retaining materially distinct model variants and giving every remaining chapter a coherent decision.
**Cost:** DRAM/double buffering follow operator engines rather than sitting immediately after DMA.
**Disposition:** selected.

## Revised part logic

1. **Why and how to trust the model** — Chapters 1–3.
2. **Core executable contracts** — Chapters 4–8.
3. **Movement, ordering, and scale** — Chapters 9–12.
4. **Working sets, operators, and off-chip supply** — Chapters 13–16.
5. **Observability and resource multiplexing** — Chapters 17–18.
6. **Verification as architecture** — Chapter 19.
7. **Exploration and extension** — Chapters 20–22.

The current `part-1-foundations` / `part-2-core` filesystem layout remains untouched. Physical manuscript moves are publication-preparation work to perform once, with link validation and no renumbering, after the remaining manuscripts exist.

## Decisions deferred to publication preparation

- Whether to publish a stable reader-facing roadmap distinct from working `PLAN.md`.
- When to move manuscripts into final part directories and regenerate links/navigation.
- Whether a later source edition has enough compiler integration for a dedicated ONNX chapter.
- Whether integrated precision dispatch or model-level accuracy evidence warrants a future numerics sequel.
