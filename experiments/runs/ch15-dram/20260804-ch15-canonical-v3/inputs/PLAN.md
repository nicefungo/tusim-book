# Tusim Book — Global Plan (dynamic)

**This is the authoritative global plan for the Tusim book.** Every new session must read it before framing or drafting a chapter and must update it when evidence changes chapter boundaries or order. It supersedes the original approved proposal at `/home/zxy/.hermes/plans/2026-07-25_095253-tusim-book-plan.md`, which remains the historical 29-chapter artifact.

## 1. Dynamic replanning rule

1. **Follow this plan generally.** Chapter contents and ordering follow §4 unless research inside a chapter establishes a better organization.
2. **Replanning is governed work.** Record every merge, split, reorder, or boundary change here with date, rationale, and exact change; mention it in the session handoff.
3. **Select scope from fresh evidence.** Never choose a chapter only from the previous chapter's deferred list. Use whole-tree reconnaissance, the coverage map, executable evidence, and a coherent reader decision.
4. **Review the whole book at part boundaries or after material drift.** The first scheduled review was completed on 2026-08-04 after Chapter 14; its evidence record is `notes/whole-book-replanning-2026-08-04.md`.
5. **Preserve fidelity disciplines through every replan.** Keep declarations, configured state, reachable execution, byte effects, analytical estimates, and calibration separate. Never sum heterogeneous cycle domains.
6. **Protect evidence provenance.** Completed chapter numbers, sealed runs, handoffs, and cross-references are stable first-edition identifiers. Do not renumber or physically reorder them merely to make the table of contents more conventional.

## 2. Replanning decision after Chapter 14

The first edition now targets **22 chapters plus appendices**, not the historical 29. The chosen structure preserves completed Chapters 1–14 and compresses remaining territory by reader decision rather than source-file count.

### Why the 29-chapter structure was superseded

- Chapter 8 already performs one coherent sealed audit of floating-point formats and rounding. Separate BF16/FP8/TF32 and rounding chapters would duplicate the evidence and imply engine paths that do not exist.
- Chapter 14's metric census proves that the operator engines are best taught together as heterogeneous functional/analytical contracts, not as four chapters that invite cross-engine cycle summation.
- Chapters 9, 10, and 14 establish adjacent bank, DMA, and pipeline-controller boundaries, but they do **not** provide reader-decision coverage of `memory/double_buffer.[ch]`. A post-replan cross-chapter audit caught the distinction between mentioning/excluding that module and teaching its state machine. The standalone double-buffer surface therefore retains a dedicated chapter, with explicit non-integration boundaries rather than a fictional pipeline.
- The ONNX demonstration compiler does not provide an executable end-to-end path at the pin. Chapters 3 and 11 preserve the negative boundary; a dedicated chapter is deferred to a future source edition.
- DRAM, metric provenance, contexts/liveness, verification, and the exploration/extension arc remain distinct reader decisions with sufficient evidence.

### Structural policy

- Keep current chapter numbering and files stable.
- Do not move existing manuscripts during chapter production. Final part-directory moves, if wanted, occur once during publication preparation with link validation and no renumbering.
- Keep `PLAN.md` as a working governance file outside the curated publish tree. Decide later whether to create a separate stable reader-facing roadmap.

## 3. Status of completed chapters

| Actual chapter | Title | Historical-plan coverage | Status |
|---|---|---|---|
| 1 | The Architecture Questions Before RTL | Plan 1 | complete |
| 2 | How an Executable Model Earns Trust | Plan 2 | complete |
| 3 | Repository Tour and First Execution | Plan 3 + executable boundary of Plan 23 | complete |
| 4 | Configuration as the Architecture Contract | Plan 4 | complete |
| 5 | State, Lifecycle, and Public APIs | Plan 5 | complete |
| 6 | PE Arrays, MMA Semantics, and Tiling | Plan 6 | complete |
| 7 | Pluggable Dataflows | Plan 7 | complete |
| 8 | Floating-Point Foundations | Plans 8–10 | complete; old three-way split superseded |
| 9 | Memory Hierarchy and Banked Scratchpads | Plan 12 + part of 15 | complete |
| 10 | DMA Descriptor Contracts and Tick-Driven Execution | Plan 13 + part of 15 | complete |
| 11 | Instruction Surfaces and Command-Queue Ordering | Plans 16 and 21 + scheduler part of 22 | complete |
| 12 | Multi-Core Clusters and Interconnect Heuristic Estimates | multicore/interconnect part of Plan 24 | complete |
| 13 | Weight Streams: Quantization, Structured Sparsity, and Compression | Plan 11 | complete |
| 14 | Operator Compute Engines: Functional Semantics and Engine Metrics | Plans 17–20 + pipeline-controller part of 15 | complete; published at curated tip `c10537f` |

## 4. Revised 22-chapter architecture

### Part I — Why and How to Trust the Model

1. **The Architecture Questions Before RTL** — complete.
2. **How an Executable Model Earns Trust** — complete.
3. **Repository Tour and First Execution** — complete.

### Part II — Core Executable Contracts

4. **Configuration as the Architecture Contract** — complete.
5. **State, Lifecycle, and Public APIs** — complete.
6. **PE Arrays, MMA Semantics, and Tiling** — complete.
7. **Pluggable Dataflows** — complete.
8. **Floating-Point Foundations** — complete; includes the historical BF16/FP8/TF32 and rounding/reproducibility territories.

### Part III — Movement, Ordering, and Scale

9. **Memory Hierarchy and Banked Scratchpads** — complete.
10. **DMA Descriptor Contracts and Tick-Driven Execution** — complete.
11. **Instruction Surfaces and Command-Queue Ordering** — complete.
12. **Multi-Core Clusters and Interconnect Heuristic Estimates** — complete.

### Part IV — Working Sets, Operators, and Off-Chip Supply

13. **Weight Streams: Quantization, Structured Sparsity, and Compression** — complete.
14. **Operator Compute Engines: Functional Semantics and Engine Metrics** — complete.
15. **DRAM Service Models and Bandwidth Claims** — canonical v2 is retained, but drafting is blocked pending a narrow canonical-v3 audit-coverage amendment from the completed asynchronous skeptical review. Reader decision: distinguish the stateful access API, stateless transfer estimator, derived statistics, historical analytical sweeps, and absent DMA integration; determine which bandwidth/latency conclusions are safe.
16. **Double Buffering and Legal Overlap.** Reader decision: distinguish the standalone SRAM double-buffer state machine, active/shadow ownership and swaps, the descriptor-DMA engine, and the separate pipeline controller; identify when overlap is represented, merely estimated, or absent, and compare buffering capacity/area/energy/verification costs with latency-hiding opportunity.

### Part V — Observability and Resource Multiplexing

17. **Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy.** Reader decision: select a producer, interval, units, and fidelity rung for a metric without constructing one fictional timeline. Include linked `performance_counters`, `event_trace`, and `power_model`; treat `cycle_model` as source-present/non-`TU_OBJS` unless separately linked and tested.
18. **Resource Multiplexing: Contexts, Scheduling, and Scratchpad Liveness.** Treat runtime context retention/preemption, compile-time schedule ordering, and liveness-based allocation as three distinct, non-integrated resource-over-time models with separate clocks, consumers, and evidence. Chapter framing must split this into separate chapters if one reader decision cannot honestly contain all three. Do not revive an end-to-end ONNX story while generated TU work remains absent/broken.

### Part VI — Verification as Architecture

19. **Verification as an Architectural Feature.** Unify unit/invariant, golden, random differential, configuration propagation, mutation, integration, regression/CI, replay/debug/error, DPI, and binding evidence. Teach evidence selection and unsafe green-gate interpretations rather than repeating every prior chapter's audit log.

### Part VII — Exploration and Extension

20. **Designing a Trustworthy Sweep.** Falsifiable questions, realistic alternatives and controls, cmodel-linked versus analytical harnesses, pinning, metrics, counterexamples, sensitivity, and fidelity limits.
21. **Lessons from the Exploration Portfolio.** Synthesize recurring regimes across geometry, memory balance, data movement, numerics, operator composition, irregular efficiency, and system sharing; challenge stale reports where executable evidence disagrees.
22. **Extending Tusim Without Breaking Its Contract.** Carry a setting/module/plugin/opcode/sweep/binding through declaration, parser, runtime, consumer, observability, tests, docs, and ownership; preserve alternatives and avoid documented no-ops.

## 5. Historical 29-chapter coverage disposition

- **Historical 1–8:** covered by actual 1–8.
- **Historical 9–10:** fully folded into actual 8; no dedicated first-edition chapters.
- **Historical 11:** covered by actual 13.
- **Historical 12–13:** covered by actual 9–10.
- **Historical 14:** becomes actual 15.
- **Historical 15:** becomes actual 16. Actual 9, 10, and 14 provide prerequisites and negative integration boundaries, not reader-decision coverage of the double-buffer module itself.
- **Historical 16:** covered by actual 11.
- **Historical 17–20:** merged into actual 14; split superseded.
- **Historical 21:** covered by actual 11.
- **Historical 22:** scheduler foundation covered in actual 11; liveness/resource decision completes in actual 18.
- **Historical 23:** negative executable boundary covered in actual 3 and 11; no dedicated chapter until the toolchain has a working end-to-end path.
- **Historical 24:** multicore/interconnect covered in actual 12; contexts complete in actual 18.
- **Historical 25:** becomes actual 17.
- **Historical 26:** becomes actual 19.
- **Historical 27–29:** become actual 20–22.

## 6. Evidence-backed next sequence

### Chapter 15 — DRAM Service Models and Bandwidth Claims

Primary evidence: `tu_cmodel/memory/dram_model.[ch]`, aggregate `tests/test_dram.c`, `docs/dram-model.md`, `docs/exploration/dram-type-clock-sweep.md`, and adjacent crossover reports. `docs/bandwidth-modeling.md` is SRAM-owned contrast evidence, not primary DRAM evidence. Chapter 15 is next because it closes the last substantial linked off-chip accounting/model boundary; no non-test hierarchy-wrapper caller or descriptor-DMA feed is proven at this pin.

Canonical v2 and skeptical review establish the chapter's central challenge set:

- first-access bandwidth budget initialization and refill semantics;
- returned base latency versus separately returned stall;
- caller-advanced time and channel-availability bookkeeping without queued completion;
- flat read-only row-conflict penalty rather than row-buffer state;
- stateless estimator versus stateful access API;
- no-op core-clock setter and independent 1 GHz assumptions;
- derived bandwidth/utilization dependence on caller ticks;
- decorative preset geometry fields;
- config and descriptor-DMA reachability gaps;
- no non-test hierarchy-wrapper caller and a separate full-config power consumer;
- double-counted bandwidth admission and history-dependent reset;
- unsafe custom-parameter paths;
- historical sweep arithmetic contradictions versus executable model behavior.

### Chapter 16 — Double Buffering and Legal Overlap

Primary evidence: `tu_cmodel/memory/double_buffer.[ch]`, `tests/test_double_buffer.c`, its Makefile membership, double-buffer/software-pipeline docs and sweeps, plus the already audited descriptor-DMA and pipeline-controller surfaces. It was restored after an independent cross-chapter audit showed that prior chapters explicitly separated these modules but never taught the double-buffer state machine or its architecture trade-offs.

### Chapter 17 — Measurement Surfaces

Primary evidence: `tu_cmodel/perf/performance_counters.[ch]`, `event_trace.[ch]`, `power_model.[ch]`, source-present `cycle_model.[ch]`, focused tests and docs. It follows DRAM and double buffering so the book has named every major metric producer before teaching cross-producer provenance.

### Chapter 18 — Resource Multiplexing

Primary evidence: `infra/tu_context.[ch]`, `isa/tu_scheduler.[ch]`, `isa/tu_liveness.[ch]`, focused tests, context and scheduler sweeps, and docs. It closes the remaining context/liveness coverage without reviving the broken ONNX-to-runtime narrative.

## 7. Appendices and publication preparation

Retain the historical appendix program, generated or validated against the pin:

- A — build/test command reference and aggregate-membership map;
- B — configuration field/consumer/test reference;
- C — public C API ownership and lifetime rules;
- D — ISA/ASM quick reference;
- E — numerical formats and tolerance guide;
- F — glossary and symbol index;
- G — fidelity and limitations matrix;
- H — reproducibility manifest.

After Chapter 22: finalize preface, part introductions, manuscript directories, navigation, internal links, terminology index, generated appendices, and clean reproducibility runs. Do not expose the dynamic working plan directly unless it is converted into a stable reader-facing roadmap.

## 8. Session rule for Chapter 15

Canonical v2 remains immutable, but the completed asynchronous review identified two unclosed audit-coverage items: hashes/predicates and focused evidence for the separate cycle/power/config/document surfaces, plus a fragile one-byte hierarchy sentinel. Seal canonical v3 with those narrow amendments before drafting. Then draft only from canonical v3, run independent manuscript review and validators, close the chapter, and request approval before rebuild-tree publication.

## Revision log

- **2026-08-04 (asynchronous review completion / canonical-v3 requirement)** — The full skeptical review arrived after the v2 handoff. Most blockers had already been incorporated, but its complete findings exposed two residual gaps: v2 did not hash/gate the separate `cycle_model`, power test, config test, or SRAM bandwidth document, and its hierarchy probe passed a one-byte sentinel for a declared 64-byte request. Drafting was re-blocked pending a narrow v3 reseal. The same whole-book audit added a future revision backlog: supplement Chapter 8 with a compact rounding experiment/replay contract, Chapter 10 with address-generator status/safe subset, and Chapter 14 with concise fusion, convolution/pooling, and softmax/normalization architecture-decision material; keep deeper attention deferred until repaired.
- **2026-08-04 (Chapter 15 predraft closure)** — Sealed canonical v2 after skeptical review exposed double-counted bandwidth admission, stale-window reset, unsafe custom parameters, missing non-test hierarchy callers, distinct JSON/YAML/config-consumer paths, GDB inferior-status ambiguity, and arithmetic contradictions in the historical DRAM sweep. Chapter 15 drafting is allowed only from the amended ledger and retained v2 evidence.
- **2026-08-04 (cross-chapter audit amendment)** — Expanded the revised first edition from 21 to 22 chapters. An independent coverage audit found that Chapters 9/10/14 mention and bound the double-buffer surface but do not provide its reader-decision coverage; treating mention-level coverage as a completed chapter was an error. Restored **Double Buffering and Legal Overlap** as Chapter 16 and shifted measurement, resource multiplexing, verification, and the closing arc to Chapters 17–22. The next-three sequence is now DRAM → double buffering/legal overlap → measurement provenance.
- **2026-08-04 (whole-book replanning after Chapter 14; partially superseded by the amendment above)** — Replaced the remaining historical 29-chapter schedule with an initial 21-chapter first-edition structure. Declared Plans 9–10 fully folded into Chapter 8, initially treated Plan 15 as folded into Chapters 9/10/14, merged Plans 17–20 into Chapter 14, and deferred Plan 23 as a dedicated chapter because its end-to-end path is broken. The cross-chapter amendment above corrects the Plan 15 disposition and resulting future numbering; all other decisions remain active. Preserved completed numbering and deferred physical part-directory moves to publication preparation. Evidence record: `notes/whole-book-replanning-2026-08-04.md`.
- **2026-08-04 (initial)** — Created as the dynamic successor to the approved 29-chapter proposal; recorded the Chapter 1–14 mapping, evidence-adjusted coverage map, candidate territory, and mandatory whole-book review before any chapter after 14.
