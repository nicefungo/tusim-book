# Tusim Book — Global Plan (dynamic)

**This is the authoritative global plan for the Tusim book.** Every new session must read it before framing or drafting a chapter and must update it when evidence changes chapter boundaries or order. It supersedes the original approved proposal at `/home/zxy/.hermes/plans/2026-07-25_095253-tusim-book-plan.md`, which remains the historical 29-chapter artifact.

## 1. Dynamic replanning rule

1. **Follow this plan generally.** Chapter contents and ordering follow §4 unless research inside a chapter establishes a better organization.
2. **Replanning is governed work.** Record every merge, split, reorder, or boundary change here with date, rationale, and exact change; mention it in the session handoff.
3. **Select scope from fresh evidence.** Never choose a chapter only from the previous chapter's deferred list. Use whole-tree reconnaissance, the coverage map, executable evidence, and a coherent reader decision.
4. **Review the whole book at part boundaries or after material drift.** The first scheduled review was completed on 2026-08-04 after Chapter 14; its evidence record is `notes/whole-book-replanning-2026-08-04.md`.
5. **Preserve fidelity disciplines through every replan.** Keep declarations, configured state, reachable execution, byte effects, analytical estimates, and calibration separate. Never sum heterogeneous cycle domains.
6. **Protect evidence provenance.** Completed chapter numbers, sealed runs, handoffs, and cross-references are stable first-edition identifiers. Do not renumber or physically reorder them merely to make the table of contents more conventional.
7. **Keep plan risks live.** Before framing each chapter, review §7, close or reclassify any triggered risk, and record the decision here and in the handoff. A chapter may not proceed merely because it is next numerically if its reader decision, evidence boundary, or relationship to adjacent chapters is still ambiguous.

## 2. Replanning decision after Chapter 14

The first edition now targets **23 chapters plus appendices**, not the historical 29. The chosen structure preserves completed Chapters 1–17 and compresses remaining territory by reader decision rather than source-file count. The mandatory Chapter 18 framing gate subsequently split runtime context retention from static scheduling/allocation; no completed chapter was renumbered.

### Why the 29-chapter structure was superseded

- Chapter 8 already performs one coherent sealed audit of floating-point formats and rounding. Separate BF16/FP8/TF32 and rounding chapters would duplicate the evidence and imply engine paths that do not exist.
- Chapter 14's metric census proves that the operator engines are best taught together as heterogeneous functional/analytical contracts, not as four chapters that invite cross-engine cycle summation.
- Chapters 9, 10, and 14 establish adjacent bank, DMA, and pipeline-controller boundaries, but they do **not** provide reader-decision coverage of `memory/double_buffer.[ch]`. A post-replan cross-chapter audit caught the distinction between mentioning/excluding that module and teaching its state machine. The standalone double-buffer surface therefore retains a dedicated chapter, with explicit non-integration boundaries rather than a fictional pipeline.
- The ONNX demonstration compiler does not provide an executable end-to-end path at the pin. Chapters 3 and 11 preserve the negative boundary; a dedicated chapter is deferred to a future source edition.
- DRAM, metric provenance, runtime context retention, static scheduling/allocation, verification, and the exploration/extension arc remain distinct reader decisions with sufficient evidence.

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
| 15 | DRAM Service Models and Bandwidth Claims | Plan 14 | complete; canonical-v3 evidence and independent manuscript reviews passed; local closure only, publication pending approval |
| 16 | Double Buffering and Legal Overlap | historical Plan 15 overlap territory | complete; canonical-v4 evidence and exact-commit review closed |
| 17 | Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy | Plans 22–23 measurement territory | complete; canonical-v4 evidence and technical/editorial/reproducibility reviews passed |

## 4. Revised 23-chapter architecture

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
15. **DRAM Service Models and Bandwidth Claims** — complete. Reader decision: distinguish the stateful access API, stateless transfer estimator, derived statistics, historical analytical sweeps, and absent DMA integration; determine which bandwidth/latency conclusions are safe.
16. **Double Buffering and Legal Overlap** — complete. Reader decision: distinguish the standalone SRAM double-buffer state machine, active/shadow ownership and swaps, the descriptor-DMA engine, and the separate pipeline controller; identify when overlap is represented, merely estimated, or absent, and compare buffering capacity/area/energy/verification costs with latency-hiding opportunity. **Boundary ownership:** Chapter 16 owns the standalone double-buffer state machine and the cross-surface legality/evidence matrix. It imports descriptor ownership from Chapter 10 and the pipeline-controller state/counter taxonomy from Chapter 14 rather than reteaching either module. No integrated legal-overlap path exists at this pin; any future story requires direct target-selection, completion, dependency, swap-authorization, compute-visibility, and common-clock evidence.

### Part V — Observability and Resource Multiplexing

17. **Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy.** — complete. Reader decision: select a producer, interval, units, and fidelity rung for a metric without constructing one fictional timeline. The chapter separates legacy `g_tu`, `tu_perf_counters_t`, event-trace and logging VCD producers, the source-present/non-`TU_OBJS` cycle model, embedded perf energy, standalone power, and benchmark-authored accounting. It qualifies caller-owned additive time, incomplete lifecycle operations, the TMAC/s field mislabeled TOPS, trace timestamp/capacity behavior, cycle-model direction/reset defects, and uncalibrated energy tables.
18. **Runtime Context Retention and Preemption Boundaries.** Reader decision: at a legal preemption boundary, choose which state is retained, who supplies the boundary/live-state contract, and which isolation and switch-cost claims follow. Separate FULL SRAM, declared live-prefix SRAM, and control-only modes; distinguish copied state, dropped state, caller-owned notifications, analytical transfer cost, and omitted reload/backing-store/queue effects. No compiler-produced liveness bridge or autonomous runtime preemption path is established at the pin.
19. **Static Scheduling and Scratchpad Allocation.** Reader decision: given an in-process `tu_instruction_t` sequence, decide whether dependence capture, order selection, live ranges, capacity, placement, and spill/fill rewriting are strong enough to authorize the transformed sequence. Import Chapter 11's scheduler findings without reteaching queue/ISA lifecycle; audit scheduler and liveness as adjacent but uncomposed static passes. Do not revive an end-to-end ONNX/compiler/runtime narrative.

### Part VI — Verification as Architecture

20. **Verification as an Architectural Feature.** Unify unit/invariant, golden, random differential, configuration propagation, mutation, integration, regression/CI, replay/debug/error, DPI, and binding evidence. Teach evidence selection and unsafe green-gate interpretations rather than repeating every prior chapter's audit log.

### Part VII — Exploration and Extension

21. **Designing a Trustworthy Sweep.** Falsifiable questions, realistic alternatives and controls, cmodel-linked versus analytical harnesses, pinning, metrics, counterexamples, sensitivity, and fidelity limits.
22. **Lessons from the Exploration Portfolio.** Synthesize recurring regimes across geometry, memory balance, data movement, numerics, operator composition, irregular efficiency, and system sharing; challenge stale reports where executable evidence disagrees.
23. **Extending Tusim Without Breaking Its Contract.** Carry a setting/module/plugin/opcode/sweep/binding through declaration, parser, runtime, consumer, observability, tests, docs, and ownership; preserve alternatives and avoid documented no-ops.

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
- **Historical 22:** scheduler foundation covered in actual 11; static scheduling/liveness legality completes in actual 19.
- **Historical 23:** negative executable boundary covered in actual 3 and 11; no dedicated chapter until the toolchain has a working end-to-end path.
- **Historical 24:** multicore/interconnect covered in actual 12; runtime contexts complete in actual 18.
- **Historical 25:** becomes actual 17.
- **Historical 26:** becomes actual 20.
- **Historical 27–29:** become actual 21–23.

## 6. Evidence-backed remaining sequence and completed baseline

### Chapter 15 — DRAM Service Models and Bandwidth Claims — complete

Primary evidence: `tu_cmodel/memory/dram_model.[ch]`, aggregate `tests/test_dram.c`, `docs/dram-model.md`, `docs/exploration/dram-type-clock-sweep.md`, and adjacent crossover reports. `docs/bandwidth-modeling.md` is SRAM-owned contrast evidence, not primary DRAM evidence. Chapter 15 closed the last substantial linked off-chip accounting/model boundary; no non-test hierarchy-wrapper caller or descriptor-DMA feed is proven at this pin.

Canonical v3 and the completed technical/editorial/reproducibility reviews establish the chapter's central challenge set:

- first-access bandwidth budget initialization and refill semantics;
- returned base latency versus separately returned stall;
- caller-advanced time and channel-availability bookkeeping without queued completion;
- flat non-ideal-read row-conflict penalty rather than row-buffer state;
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

Primary evidence: `tu_cmodel/memory/double_buffer.[ch]`, `tests/test_double_buffer.c`, its Makefile membership, double-buffer/software-pipeline docs and sweeps, plus the already audited descriptor-DMA and pipeline-controller surfaces. It was restored after an independent cross-chapter audit showed that prior chapters explicitly separated these modules but never taught the double-buffer state machine or its architecture trade-offs. Framing must preserve the standalone state-machine/DMA/pipeline-controller boundaries and must not assume they compose. Chapter 16 owns the cross-surface bridge checklist and legality matrix; Chapter 10 remains authoritative for descriptor ownership/queue semantics and Chapter 14 remains authoritative for the pipeline controller's state and counters.

### Chapter 17 — Measurement Surfaces

Primary evidence: `tu_cmodel/perf/performance_counters.[ch]`, `event_trace.[ch]`, `power_model.[ch]`, source-present `cycle_model.[ch]`, focused tests and docs. It follows DRAM and double buffering so the book has named every major metric producer before teaching cross-producer provenance.

### Chapter 18 — Runtime Context Retention and Preemption Boundaries

Primary evidence: `infra/tu_context.[ch]`, `tests/test_context.c`, the context-switch sweep, core state/synchronization dependencies, config/caller/build reachability, and context docs. The mandatory split/keep gate resolved **split** on 2026-08-05: runtime save/restore has a distinct owner, state contract, caller-fed time-slice surface, and switch-cost equation. Framing record: `notes/chapter-18-framing-and-evidence-plan.md`.

### Chapter 19 — Static Scheduling and Scratchpad Allocation

Primary evidence: `isa/tu_scheduler.[ch]`, `isa/tu_liveness.[ch]`, focused tests, scheduler sweep, compiler-pass docs, and Chapter 11's sealed scheduler boundary. It closes the remaining static ordering/liveness coverage without inventing scheduler→allocator composition or reviving the broken ONNX-to-runtime narrative. The chapter must gate the transformed sequence's dependence, capacity, placement, and spill/fill legality rather than treating `valid=true` or passing weak tests as semantic proof.

### Chapter 20 — Verification as an Architectural Feature

Primary evidence: the repository's unit, invariant, golden, differential, random, configuration, mutation, integration, regression/CI, replay/debug, DPI, and binding surfaces plus the sealed evidence practices demonstrated in Chapters 1–19. Keep this chapter about choosing evidence for a claim; do not repeat Chapter 17's metric-producer taxonomy or turn prior chapter audit logs into the chapter structure.

### Chapter 21 — Designing a Trustworthy Sweep

Primary evidence: executable C/Python sweeps, analytical harnesses, retained manifests, sensitivity studies, and counterexamples across the repository. Keep this chapter methodological: falsifiable question, alternatives, controls, producer identity, pinning, metrics, sensitivity, and claim limits.

### Chapter 22 — Lessons from the Exploration Portfolio

Primary evidence: the exploration report portfolio reconciled against executable source and the chapter audits. Keep this chapter empirical and synthetic: recurring regimes, useful alternatives, stale conclusions, and cross-domain lessons. Do not repeat Chapter 21's sweep-construction procedure.

### Chapter 23 — Extending Tusim Without Breaking Its Contract

Primary evidence: representative configuration, module, plugin, opcode, sweep, test, documentation, and binding extension paths. The chapter must trace additions end to end through declaration, parser, runtime conversion, consumer, observability, verification, ownership, and documentation; it must not present declared or generated no-ops as integrated support.

## 7. Plan risk register and mandatory review checkpoints

These risks are part of the plan, not optional editorial notes. Every new chapter framing plan must state which risks it triggers and how they are resolved, qualified, or deferred.

| Risk | Why it matters | Trigger | Required check or decision |
|---|---|---|---|
| **Stable numbering versus ideal pedagogy** | DRAM and double buffering follow operator engines rather than sitting immediately after DMA. Reordering would improve conventional topic locality but break stable identifiers, links, handoffs, and sealed-evidence narratives. | Any proposal to renumber, move, or merge completed chapters. | Preserve numbering for this edition unless a demonstrated reader-comprehension failure outweighs provenance cost; defer physical part-directory moves to publication preparation. |
| **Chapter 16 fictional integration** | Standalone double-buffer state, descriptor DMA, and the pipeline controller are adjacent but not thereby one executable pipeline. | Chapter 16 framing, diagrams, cycle equations, or overlap claims. | Trace callers and clocks separately; require explicit evidence for every bridge; present executable state, analytical overlap, and missing integration as distinct alternatives. |
| **Chapter 17/20 overlap** | Metric provenance and verification evidence can collapse into a repetitive “measurement and testing” discussion. | Chapter 17 or 20 framing includes the other's primary reader decision. | Keep Chapter 17 on producer/interval/units/fidelity; keep Chapter 20 on evidence selection, failure interpretation, and verification architecture. Re-scope before drafting if that distinction cannot be maintained. |
| **Chapter 18 overload** | Context save/restore, scheduler ordering, and liveness allocation have different timescales, consumers, and integration status. | Fresh reconnaissance cannot express one decision matrix without combining heterogeneous clocks or inventing a pipeline. | **Resolved 2026-08-05 by split:** Chapter 18 owns runtime context retention/preemption; Chapter 19 owns adjacent but uncomposed static scheduling/allocation. Reopen only if a future edition proves a real compiler/runtime bridge. |
| **Chapter 21/22 repetition** | Sweep methodology and portfolio synthesis draw on the same reports and can duplicate examples. | The same section could appear unchanged in both chapters. | Chapter 21 owns how to design and validate a sweep; Chapter 22 owns what the existing portfolio teaches after executable reconciliation. Use cross-references rather than duplicate tutorials. |
| **Broad synthesis chapters becoming catalogues** | Chapters 20–23 cover many modules and may regress to API/report enumeration. | A framing plan lacks a single reader decision, ranked alternatives, or explicit exclusions. | Split or narrow before evidence sealing; organize by decisions and failure modes, not directories or document lists. |
| **Completed-chapter supplement backlog is forgotten** | Chapters 8, 10, and 14 have bounded reader-decision gaps that do not justify new chapters but still matter to first-edition completeness. | End of Chapter 20 or start of publication preparation. | Schedule and verify: Chapter 8 rounding experiment/replay contract; Chapter 10 address-generation status/safe subset; Chapter 14 concise fusion, convolution/pooling, and softmax/normalization architecture-decision material. Keep deeper attention claims deferred until correctness is repaired. |
| **Source-edition drift** | A newer Tusim commit could change reachability, tests, or chapter boundaries while old seals remain valid only for the pinned edition. | Any proposed change to `edition.yaml` or source pin. | Treat as a separate governed edition decision; rerun whole-book coverage reconnaissance and reclassify affected claims rather than silently carrying conclusions forward. |
| **Working plan versus reader-facing structure** | `PLAN.md`, current manuscript directories, and final published navigation serve different purposes. | Publication preparation after Chapter 23. | Decide once whether to create a stable reader-facing roadmap; perform part-directory moves, link repair, terminology/index generation, and appendix validation as one controlled publication pass. Do not publish the dynamic plan by accident. |
| **Broken compiler path is prematurely revived** | Repository declarations and historical intent can look like an end-to-end ONNX/compiler story even though generated TU work is absent/broken at this pin. | Chapters 19, 23, or a future replan proposes compiler integration coverage. | Require a repository-contained nontrivial lowering that links, runs, and verifies output before granting an end-to-end compiler chapter; otherwise preserve the negative boundary. |

### Mandatory review checkpoints

1. **Before every chapter:** perform a lightweight global consistency scan against §4–§7, the coverage disposition, current source reachability, and the completed-chapter supplement backlog. Record triggered risks in the framing plan.
2. **After Chapter 16 / Part IV boundary — complete 2026-08-05:** the full whole-book coverage and sequence review confirmed that memory supply, movement, buffering, operators, and off-chip service are neither missing a reader decision nor double-covered. The 22-chapter sequence remains unchanged and Chapter 17 remains next. Evidence record: `notes/whole-book-coverage-review-2026-08-05-after-ch16.md`.
3. **During Chapter 18 framing — complete 2026-08-05:** the mandatory gate selected a split; Chapter 18 owns runtime context retention/preemption and Chapter 19 owns static scheduling/allocation. Evidence record: `notes/chapter-18-framing-and-evidence-plan.md`.
4. **After Chapter 19 / Part V boundary:** verify the Chapter 17/18/19 division, Chapter 20 prerequisites, and whether any producer or resource-over-time model remains unnamed.
5. **After Chapter 20:** review Chapter 21/22 overlap and turn the completed-chapter supplement backlog into an explicit revision schedule.
6. **Before publication preparation:** run a final coverage matrix, cross-reference/link audit, fidelity/terminology audit, appendix-generation check, stable-roadmap decision, and clean reproducibility pass.

If a checkpoint finds missing reader-decision coverage, a duplicated chapter purpose, or an unsupported integration story, drafting of the affected next chapter is blocked until `PLAN.md` records the corrective decision.

## 8. Appendices and publication preparation

Retain the historical appendix program, generated or validated against the pin:

- A — build/test command reference and aggregate-membership map;
- B — configuration field/consumer/test reference;
- C — public C API ownership and lifetime rules;
- D — ISA/ASM quick reference;
- E — numerical formats and tolerance guide;
- F — glossary and symbol index;
- G — fidelity and limitations matrix;
- H — reproducibility manifest.

After Chapter 23: finalize preface, part introductions, manuscript directories, navigation, internal links, terminology index, generated appendices, and clean reproducibility runs. Do not expose the dynamic working plan directly unless it is converted into a stable reader-facing roadmap.

## 9. Session rule after the Chapter 18 framing gate

Chapter 17 is complete and published. The mandatory Chapter 18 split/keep gate is closed by `notes/chapter-18-framing-and-evidence-plan.md`. Continue Chapter 18 only as **Runtime Context Retention and Preemption Boundaries**: build a field-complete ledger and fail-closed pinned audit before drafting. Keep static scheduler/liveness semantics for new Chapter 19, import Chapter 11 scheduler findings rather than duplicating them, and do not invent a compiler-produced live-prefix or ONNX-to-runtime bridge. Publication remains approval-gated: request explicit user authorization before any rebuild-tree update or push to `origin/main`.

## Revision log

- **2026-08-05 (mandatory Chapter 18 split/keep gate)** — Split the overloaded resource-multiplexing chapter after fresh pinned reconnaissance. Chapter 18 now owns runtime context retention/preemption; new Chapter 19 owns adjacent but uncomposed static scheduling and scratchpad allocation. Shifted the unstarted verification/exploration/extension arc to Chapters 20–23, increasing the first edition from 22 to 23 chapters without renumbering completed Chapters 1–17. The split is evidence-driven: all three objects are library-linked and focused-tested, but none has a non-test C caller; context switching has runtime core state/caller-fed boundaries/retention traffic, while scheduler/liveness rewrite in-process instruction arrays and have no source bridge to contexts or the broken ONNX path. Evidence record: `notes/chapter-18-framing-and-evidence-plan.md`.

- **2026-08-05 (Chapter 16 closure and Part IV checkpoint)** — Completed the 7,878-word Chapter 16 manuscript from fail-fast canonical v4, resolved all independent technical/skeptical/editorial findings, and closed exact-commit review at `66908874599854ea2d417d8f60a13398b448dc07`. The apparent residual triple emphasis marker was disproved by byte inspection; the validator now rejects a real regression. The mandatory whole-book coverage/sequence review retained 22 chapters, closed Part IV without a synthetic integrated-memory chapter, and kept Chapter 17 next. Evidence record: `notes/whole-book-coverage-review-2026-08-05-after-ch16.md`.
- **2026-08-04 (Chapter 16 boundary clarification)** — Kept Chapter 16 in place but narrowed its ownership after the mandatory global-plan risk scan: teach the standalone active/shadow state machine and a cross-surface legality/evidence matrix; import descriptor and pipeline-controller details from Chapters 10 and 14. An overlap bridge now requires target-selection, completion, dependency, swap-authorization, compute-visibility, and common-clock evidence rather than adjacency or a focused-test call chain.
- **2026-08-04 (plan risk register and review cadence)** — Added explicit global risks, trigger conditions, required decisions, and mandatory checkpoints before every chapter, at the Part IV and Part V boundaries, during Chapter 18 framing, after Chapter 19, and before publication preparation. Clarified Chapter 15 as complete/canonical-v3, expanded the evidence-backed remaining sequence through Chapter 22, and made fictional integration, chapter overlap/overload, supplement backlog, source-edition drift, compiler revival, and publication-structure risks durable plan gates.
- **2026-08-04 (Chapter 15 manuscript closure)** — Completed the 6,450-word manuscript and fail-closed validator from canonical v3; resolved technical/editorial/reproducibility findings including GHz→TOPS units, per-surface integration rungs, cycle-model counter provenance, enum portability, ideal row-mode exception, cross-artifact ledger convergence, optimization-safe validators, exact run-file closure, and v1/v2/v3 provenance. Independent final technical/editorial/reproducibility review passed. Chapter 16 is next; no push/publication occurred.
- **2026-08-04 (canonical-v3 closure)** — Sealed the final asynchronous-review amendments at input commit `242807f`: 23 hashes, 62 predicates/85 checks, DRAM 12/12, hierarchy 10/10, source-linked cycle model 21/21, power 20/20, mutation inferior code 01, expanded probe with 64-byte sentinel and availability-overwrite case, sweep recomputation, manifest, and 13-file predraft validation all passed. Drafting is allowed from v3.
- **2026-08-04 (asynchronous review completion / canonical-v3 requirement)** — The full skeptical review arrived after the v2 handoff. Most blockers had already been incorporated, but its complete findings exposed two residual gaps: v2 did not hash/gate the separate `cycle_model`, power test, config test, or SRAM bandwidth document, and its hierarchy probe passed a one-byte sentinel for a declared 64-byte request. Drafting was re-blocked pending a narrow v3 reseal. The same whole-book audit added a future revision backlog: supplement Chapter 8 with a compact rounding experiment/replay contract, Chapter 10 with address-generator status/safe subset, and Chapter 14 with concise fusion, convolution/pooling, and softmax/normalization architecture-decision material; keep deeper attention deferred until repaired.
- **2026-08-04 (Chapter 15 predraft closure)** — Sealed canonical v2 after skeptical review exposed double-counted bandwidth admission, stale-window reset, unsafe custom parameters, missing non-test hierarchy callers, distinct JSON/YAML/config-consumer paths, GDB inferior-status ambiguity, and arithmetic contradictions in the historical DRAM sweep. Chapter 15 drafting is allowed only from the amended ledger and retained v2 evidence.
- **2026-08-04 (cross-chapter audit amendment)** — Expanded the revised first edition from 21 to 22 chapters. An independent coverage audit found that Chapters 9/10/14 mention and bound the double-buffer surface but do not provide its reader-decision coverage; treating mention-level coverage as a completed chapter was an error. Restored **Double Buffering and Legal Overlap** as Chapter 16 and shifted measurement, resource multiplexing, verification, and the closing arc to Chapters 17–22. The next-three sequence is now DRAM → double buffering/legal overlap → measurement provenance.
- **2026-08-04 (whole-book replanning after Chapter 14; partially superseded by the amendment above)** — Replaced the remaining historical 29-chapter schedule with an initial 21-chapter first-edition structure. Declared Plans 9–10 fully folded into Chapter 8, initially treated Plan 15 as folded into Chapters 9/10/14, merged Plans 17–20 into Chapter 14, and deferred Plan 23 as a dedicated chapter because its end-to-end path is broken. The cross-chapter amendment above corrects the Plan 15 disposition and resulting future numbering; all other decisions remain active. Preserved completed numbering and deferred physical part-directory moves to publication preparation. Evidence record: `notes/whole-book-replanning-2026-08-04.md`.
- **2026-08-04 (initial)** — Created as the dynamic successor to the approved 29-chapter proposal; recorded the Chapter 1–14 mapping, evidence-adjusted coverage map, candidate territory, and mandatory whole-book review before any chapter after 14.
