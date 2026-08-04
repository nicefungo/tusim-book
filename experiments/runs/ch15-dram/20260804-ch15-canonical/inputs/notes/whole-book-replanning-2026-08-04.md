# Whole-Book Replanning Review — 2026-08-04

## Decision

The first edition is replanned from 29 proposed chapters to **21 governed chapters plus appendices**. Chapters 1–14 keep their numbers, filenames, evidence seals, and current order. The remaining sequence is:

15. DRAM Service Models and Bandwidth Claims
16. Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy
17. Resource Multiplexing: Contexts, Scheduling, and Scratchpad Liveness
18. Verification as an Architectural Feature
19. Designing a Trustworthy Sweep
20. Lessons from the Exploration Portfolio
21. Extending Tusim Without Breaking Its Contract

This review is the evidence record for the corresponding revision in `PLAN.md`.

## Review method

The review compared:

- the historical 29-chapter proposal at `/home/zxy/.hermes/plans/2026-07-25_095253-tusim-book-plan.md`;
- all 14 manuscripts and the available Chapter 9–14 framing plans;
- `fidelity-matrix.md` and all 39 findings in `source-audit.md`;
- live library membership and test provenance in the pinned Makefile;
- source, focused tests, documentation, exploration reports, and non-test callers at Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`.

Coverage was judged by whether a chapter teaches the original **reader decision and fidelity boundary**, not by keyword presence.

## Coverage review of the historical plan

| Historical plan | Evidence in the written book | Replanning disposition |
|---|---|---|
| 1–7: purpose, trust, repository, config, lifecycle, PE/MMA, dataflow | Actual Chapters 1–7 provide the intended reader decisions and executable boundaries. | Keep as Chapters 1–7. |
| 8–10: floating-point foundations; BF16/FP8/TF32; rounding/reproducibility | Chapter 8 has dedicated source maps and sections for BF16, FP8, TF32, RNE/RTZ/stochastic rounding, subnormals, special values, executable boundary matrices, and format-specific defects. | Treat all three historical chapters as fully folded into Chapter 8. A split would duplicate one sealed conversion audit and imply engine precision paths that do not exist. |
| 11: integer quantization, sparsity, compression | Chapter 13 covers the full weight-representation decision and proves the three surfaces are adjacent, not one integrated feed. | Keep as Chapter 13; do not move or renumber. |
| 12: banked SRAM and hierarchy | Chapter 9 covers three incompatible memory surfaces and the raw-pointer/integration boundaries. | Keep as Chapter 9. |
| 13: DMA/descriptors/address generation | Chapter 10 covers descriptor geometry, lifecycle, ownership, clocks, ordinary-operation reachability, and the retained 12/13 address-generator failure. | Keep as Chapter 10. |
| 14: DRAM and bandwidth | DRAM is mentioned in Chapters 2, 4, 9, and 10, but no chapter audits the standalone access clock, estimator, presets, statistics, config path, or the historical DRAM sweep. | Remaining; becomes Chapter 15. |
| 15: double buffering/software pipelines | Chapter 10 reproduces standalone double-buffer evidence and rejects the bounded DMA-to-shadow overlap sequence; Chapter 14 audits the pipeline controller and byte-proportional overlap credit. | Folded into Chapters 10 and 14. No dedicated chapter unless a future edition supplies an integrated corrected path. |
| 16: command queue/synchronization | Chapter 11 covers ordering, dependency, completion, signaling, barrier, reset, and reclamation contracts. | Fully covered in Chapter 11. |
| 17–20: operator engines | Chapter 14 deliberately unifies seven engines through a return-value/metric census and records the attention FP16 staging defect. | Fully folded into Chapter 14; the old four-way split is superseded. |
| 21: ISA/ASM | Chapter 11 separates packed metadata, text ASM, and queue dispatch rather than inventing one stack. | Fully covered in Chapter 11. |
| 22: scheduling/liveness | Chapter 11 audits the scheduler's fixed-cost DAG model but explicitly defers liveness allocation and spill/fill semantics. | Scheduler foundation covered; remaining liveness/resource-allocation decision moves to Chapter 17. |
| 23: ONNX compiler | Chapter 3 audits emission and proves all inspected generated programs have zero TU ops and fail to link on undefined `host_gemm`; Chapter 11 proves no compiler→scheduler→queue bridge. | No dedicated first-edition chapter at this pin. Preserve the negative boundary in Chapters 3/11 and revisit in a future edition if an end-to-end path exists. |
| 24: multicore/interconnect/contexts | Chapter 12 covers multicore and interconnect surfaces but not context save/restore. | Contexts move to Chapter 17. |
| 25: counters/cycle/trace/energy | Only local warnings and producer-specific references exist in current chapters. `performance_counters`, `event_trace`, and `power_model` are linked and focused-tested; `cycle_model` is source-present but absent from `TU_OBJS`. | Remaining; becomes Chapter 16, organized around metric provenance rather than summation. |
| 26: verification | Verification practice is pervasive, but no chapter teaches the complete architecture-level verification decision across golden, differential, config, mutation, CI, replay, error, DPI, and binding surfaces. | Remaining; becomes Chapter 18. |
| 27–29: sweeps, portfolio synthesis, extension | Individual chapters challenge historical sweeps, but the closing methodological and synthesis arc has not been written. | Retain as Chapters 19–21. |

## Why Chapter 15 is next

The DRAM surface has a coherent, still-unclaimed reader decision: **which output is a local service estimate, which is stateful access accounting, and when may either support a bandwidth claim?** It has sufficient primary evidence for a full chapter:

- linked implementation: `tu_cmodel/memory/dram_model.[ch]`;
- aggregate focused suite: `tests/test_dram.c` (`test-dram` is in `make test`);
- focused documentation: `docs/dram-model.md` and `docs/bandwidth-modeling.md`;
- historical exploration: `docs/exploration/dram-type-clock-sweep.md` plus the adjacent K-crossover report;
- explicit integration boundary: Chapter 10 already proves descriptor DMA never calls the DRAM model.

Fresh inspection also reveals discriminating chapter-grade findings that the historical documentation overstates:

1. the first non-ideal access begins with a zero bandwidth budget and is charged a window stall because initialization establishes the window but does not fill it;
2. access calls return base latency separately from stall and do not advance `current_cycle`;
3. channel availability is recorded but no access is actually queued or delayed;
4. row-conflict mode adds a flat ten-cycle penalty to every read and counts every read as a conflict, with no row state, and does not apply the same logic to writes;
5. `tu_dram_estimate_transfer()` uses a separate stateless `ceil(bytes / GB/s-at-assumed-1-GHz) + latency` equation;
6. `tu_dram_set_core_clock()` is a no-op, while other helpers independently accept or assume a core clock;
7. derived bandwidth divides cumulative bytes by caller-advanced `current_cycle`, so it can exceed peak and utilization can exceed one;
8. preset geometry fields such as bus width, bank count, and row size are mostly descriptive in the executable path;
9. the shipped config declares DRAM settings, but the standalone model is constructed by enum/custom APIs rather than the global runtime path.

These boundaries make Chapter 15 more than a technology table and prevent the historical analytical sweep from being presented as an execution of the standalone model.

## Structural alternatives considered

### Alternative A — Renumber and physically reorder by topic

Move Chapter 13 next to Chapter 8, insert DRAM after Chapter 10, then place operator engines after all memory chapters.

**Benefit:** a conventional numerics→memory→engines sequence.  
**Cost:** invalidates stable chapter numbers, internal links, handoffs, review references, and sealed-evidence narratives across 14 chapters; creates large editorial churn without changing technical truth.  
**Disposition:** rejected for this snapshot edition.

### Alternative B — Preserve 29 chapters

Write dedicated BF16/FP8/TF32, rounding, double-buffer, four operator, and ONNX chapters as originally proposed.

**Benefit:** regular topic granularity and close fidelity to the historical proposal.  
**Cost:** duplicates sealed Chapters 8 and 14, promotes disconnected modules into fictional pipelines, and gives the broken ONNX demonstration more weight than its executable evidence supports.  
**Disposition:** rejected.

### Alternative C — Preserve completed numbering and compress by reader decision

Keep Chapters 1–14 immutable; complete the missing model boundaries, then close with measurement, resource multiplexing, verification, exploration, and extension.

**Benefit:** preserves evidence provenance, eliminates duplicate chapters, and gives every remaining chapter a distinct architecture decision.  
**Cost:** DRAM follows operator engines rather than sitting immediately after DMA; Part IV therefore uses off-chip supply as a system-level hinge rather than a strict source-tree order.  
**Disposition:** selected.

## Revised part logic

1. **Why and how to trust the model** — Chapters 1–3.
2. **Core executable contracts** — Chapters 4–8.
3. **Movement, ordering, and scale** — Chapters 9–12.
4. **Working sets, operators, and off-chip supply** — Chapters 13–15.
5. **Observability and resource multiplexing** — Chapters 16–17.
6. **Verification as architecture** — Chapter 18.
7. **Exploration and extension** — Chapters 19–21.

The current filesystem's `part-1-foundations` / `part-2-core` layout is left untouched in this replanning change. Physical manuscript moves are publication-preparation work: they should happen once, with link validation and no chapter renumbering, after the remaining manuscripts exist.

## Decisions deferred to publication preparation

- Whether to publish a stable reader-facing roadmap distinct from the working `PLAN.md`.
- When to move manuscripts into final part directories and regenerate links/navigation.
- Whether a later source edition has enough compiler integration to restore a dedicated ONNX chapter.
- Whether corrected integrated double buffering warrants a second-edition chapter.
