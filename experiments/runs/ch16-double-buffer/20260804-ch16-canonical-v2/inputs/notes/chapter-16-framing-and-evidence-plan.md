# Chapter 16 — Framing and Evidence Plan

**Working title:** Double Buffering and Legal Overlap  
**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (read-only)  
**Plan authority:** `PLAN.md` revision dated 2026-08-04  
**Status:** predraft evidence collection; drafting blocked until a post-review canonical seal and skeptical dispositions pass.

## 1. Mandatory global-plan and risk scan

The scan covers `PLAN.md` §§4–7, the historical coverage disposition, `notes/whole-book-replanning-2026-08-04.md`, Chapters 9/10/14 boundaries, `source-audit.md`, `fidelity-matrix.md`, and the Chapter 15 closure handoff.

- **Sequence/coverage:** Chapter 16 remains the last Part IV reader decision. Chapters 9 and 10 establish SRAM/DMA prerequisites and Chapter 14 audits the separate pipeline-controller metric, but none teaches the standalone `memory/double_buffer.[ch]` ownership state machine. Mention-level coverage is not chapter coverage.
- **Triggered risk — Chapter 16 fictional integration:** active and chapter-defining. Standalone SRAM double-buffering, descriptor DMA, and the pipeline controller must retain separate caller inventories and clocks. The pipeline controller is the only source-level bridge candidate and must be tested for actual byte visibility, not accepted from includes/comments.
- **Stable numbering:** no trigger to renumber or move completed chapters. Chapter 16's delayed placement preserves evidence provenance and is pedagogically supported by Chapters 9/10/14 prerequisites.
- **Chapter 17/19, Chapter 18 overload, Chapter 20/21 repetition, broad synthesis:** not triggered by this chapter if metric-producer taxonomy, contexts/scheduling, verification methodology, and sweep methodology remain exclusions.
- **Supplement backlog:** Chapters 8/10/14 supplements remain deferred; Chapter 10's bounded DMA-to-shadow negative evidence is a prerequisite, not a reason to reopen it.
- **Source-edition drift:** absent; `edition.yaml` remains pinned to `e918c80`.
- **Broken compiler path:** historical compiler recommendations are not executable integration evidence and are excluded.

**Global decision:** the chapter order remains valid, but the continuity scan required a narrow boundary clarification before drafting. Chapter 16 owns the standalone double-buffer state machine and cross-surface legality/evidence matrix; descriptor ownership remains Chapter 10 territory and pipeline-controller state/counter teaching remains Chapter 14 territory. `PLAN.md` now records six requirements for any claimed bridge: target selection, completion, dependency, swap authorization, compute visibility, and common-clock evidence.

## 2. Fresh evidence reconnaissance

The live source exposes three adjacent but unequal surfaces:

1. `memory/double_buffer.[ch]` owns active/shadow allocation, pointer selection, swaps, dirty state, manually supplied byte/cycle counters, and destruction through `tu_sram`.
2. `dma_descriptor.[ch]` owns functional byte movement and an independent tick/cycle state. Ordinary descriptors resolve SRAM through `tu_sram_raw_ptr()`; they do not intrinsically select a shadow buffer.
3. `compute/pipeline_controller.[ch]` owns slots, a caller-advanced `current_cycle`, descriptor submission/ticking, stage transitions, pointer swaps, and an analytical overlap ledger. It has no non-test caller at the pin and does not dispatch compute through `cmd_id`.

The bridge candidate in `pipeline_controller.c` sets both `dst_region` and `dst_host` for host-to-TU loads. Descriptor execution prioritizes `dst_region` and therefore resolves `tu_sram_raw_ptr()` to the current active buffer; the shadow pointer is ignored. The controller then swaps on descriptor `completed`, making the stale shadow active. This is a negative integration boundary until independently reproduced.

## 3. Ranked scope organizations

| Rank | Candidate | Reader decision | Evidence and continuity | Principal risk | Disposition |
|---|---|---|---|---|---|
| 1 | **Ownership first, then prove or reject each overlap bridge** | decide when a swap is legal, which bytes become active, which producer owns each clock/counter, and what extra capacity/control buys under named regimes | strongest standalone source/test evidence; naturally uses Chapters 9/10/14 as boundaries while preserving the pipeline bridge as an adversarial case | could become an API catalogue unless organized around legal state transitions and alternatives | **selected** |
| 2 | Pipeline-timeline tutorial | compare sequential, depth-2, and depth-3 tile timelines and derive speedup | abundant comments/docs and a pipeline suite | highest fictional-integration risk; diagrams can imply compute dispatch, valid shadow loading, and shared elapsed time that source does not establish | rejected |
| 3 | SRAM-capacity and tiling trade-off chapter | choose single buffering, double buffering, banking, or larger effective working sets from analytical sweeps | rich O/W/A sizing reports and textbook-friendly equations | historical ideal-overlap equations can eclipse executable state and contain unsupported area/compiler recommendations | rejected as primary organization; retained as a qualified alternatives section |
| 4 | Unified DMA/buffer/controller API inventory | enumerate descriptors, buffers, stages, and stats | easiest source map | no coherent reader decision; duplicates Chapters 10/14 and invites linked-object integration claims | rejected |

## 4. Reader decision and opening question

**Reader decision:** Given a tile working set, available SRAM, descriptor transfer, compute window, and controller choice, decide whether to use single buffering, standalone ping-pong ownership, or a separately scheduled overlap model; determine the legal swap preconditions, byte visibility, capacity/area/energy/control cost, attainable latency hiding, clock/counter provenance, and evidence needed before claiming speedup.

**Opening architecture question:** **What must be true before swapping a shadow buffer can hide latency without making stale data active—and which Tusim surface, if any, proves each condition?**

## 5. Scope

### In scope

- standalone equal-capacity primary/shadow allocation and active/shadow pointer ownership;
- enable/idempotence, disable/data preservation, destroy, reset-equivalent behavior, and context save/restore boundary;
- dirty/valid distinction, unguarded legal/illegal swaps, repeated swaps, and notification/accounting semantics;
- active-buffer-aware generic SRAM accesses and shared bank-meter state;
- descriptor DMA's byte destination resolution, completion flag, and independent clock;
- the separate pipeline controller as an explicit bridge candidate and analytical overlap ledger;
- real non-test caller inventories, archive membership, focused-test provenance, and configuration reachability;
- historical double-buffer and buffer-sizing reports only after equation/conclusion recomputation;
- alternatives across single, ping-pong, partitioned/banked, triple/ring, and queue/event-backed buffering, with regime-specific performance, capacity/area/energy, control, and verification costs.

### Explicitly out of scope

- re-teaching descriptor ownership, queue/chaining, DRAM, or command-queue semantics (Chapters 10, 11, 15);
- treating `cmd_id` storage as compute execution;
- adding pipeline-controller, DMA, SRAM, or operator counters into one elapsed timeline;
- full metric-producer taxonomy (Chapter 17), contexts/scheduling/liveness (Chapter 18), or verification methodology (Chapter 19);
- reviving ONNX/compiler recommendations as executable evidence;
- modifying the pinned source or proposing one universally fastest architecture.

## 6. Source map and evidence ladders

| Surface | Primary evidence | Gate question |
|---|---|---|
| standalone state | `tu_cmodel/memory/double_buffer.[ch]`, `tu_sram.[ch]` | which pointer owns visible bytes; what validates a swap; which state/counters change? |
| focused test | `tests/test_double_buffer.c`, Makefile | what transitions pass; is there a real rule and aggregate membership? |
| descriptor DMA | `dma_descriptor.[ch]`, Chapter 10 seal | does a descriptor write shadow bytes; when is completion asserted; which clock advances? |
| pipeline controller | `compute/pipeline_controller.[ch]`, bounded Chapter 10 probe, Chapter 14 evidence | does it bridge bytes and stages correctly; what is functional versus ledger-only? |
| contexts/lifecycle | `infra/tu_context.c`, SRAM destroy/disable | does state survive save/restore; where can ownership be lost or leaked? |
| configuration | JSON/YAML, `infra/config.[ch]`, runtime conversion, hierarchy config | is double buffering declared, parsed, converted, retained, and consumed, or API-only/decorative? |
| documents/reports | `TU_DOUBLE_BUFFER.md`, `software-pipelining.md`, exploration reports | which equations are historical ideal models and which claims contradict execution? |

Evidence ladders remain separate:

- `allocated -> enabled -> shadow written -> write accounted -> valid/dirty checked -> swap permitted -> active bytes observed -> safely disabled/destroyed`;
- `descriptor created -> destination resolved -> bytes copied -> completed flag -> DMA tick/cycle -> controller transition`;
- `controller configured -> tile submitted -> slot/stage transition -> compute actually dispatched -> load/store overlap proved -> elapsed schedule -> calibrated speedup`;
- `declared -> parsed -> validated -> converted -> retained -> consumed -> discriminating effect`.

## 7. Predraft executable evidence plan

The fail-closed audit must:

1. hash the exact source, tests, Makefile, config/context, docs, reports, and prior bounded-probe evidence;
2. prove both modules are archive members and reject shared-library linkage;
3. compile/run `test_double_buffer.c` directly because `test-double` is `.PHONY`/clean-only with no recipe and is absent from aggregate `test`;
4. mutation-test one focused state assertion;
5. avoid the unmodified `test_pipeline.c`: it requests four DMA channels while fixed channel storage is three; preserve it as source evidence and use a one-channel bounded probe;
6. print exact standalone transitions: initial pointers/data; notify without write; swap while clean; write+notify+swap; even/odd swaps; disable with each active index; counter persistence;
7. discriminate shared state: active and shadow bytes are separate, but both roles share one `banks` bandwidth-meter/cycle state;
8. reproduce the controller bridge: requested shadow pointer, actual descriptor destination resolution, descriptor completion versus `cycles_completed/current_cycle`, post-swap active/shadow bytes, dirty flag, and ledger totals;
9. show `cmd_id` is stored but never dispatched and reset destroys rather than reinitializes the controller;
10. gate context save/restore dropping `db`, config absence/decorative hierarchy field, and exact non-test caller inventories;
11. recompute representative analytical rows and reject unsupported generalizations;
12. preserve mutation controls, immutable retained logs, exact manifests, and pre/post source cleanliness.

## 8. Skeptical pre-draft gates

- Hand-recompute every probe value and state transition from source; never trust test names, comments, or the probe's CHECKs.
- Treat `shadow_dirty` as notification state, not proof of bytes, capacity, descriptor completion, or validity.
- Require a legal-swap precondition; an API that permits clean swaps does not itself enforce legality.
- Trace actual descriptor destination precedence (`dst_region` versus `dst_host`) and active index at execution time.
- Distinguish DMA executor completion, descriptor cycle estimate, DMA engine cycle, controller cycle, SRAM bank cycle, manually recorded overlap, and pipeline ledger totals.
- Check every lifecycle path, including active-shadow disable, direct destroy, re-init, reset, and context restore.
- Check actual Makefile recipes and aggregate membership rather than `.PHONY` names.
- Recompute report rows from formulas and label assumptions: ideal independent ports, traffic residency, startup/drain, channel serialization, and no calibration.
- Audit the audit: every blanket integration/config/lifecycle claim must have a hashed file and explicit predicate.

## 9. Claims the chapter must not make

- that a dirty bit proves fresh/complete data or that swaps are legality-checked;
- that descriptor DMA intrinsically targets the shadow buffer;
- that pipeline `cmd_id` dispatches compute or command-queue work;
- that `completed` means elapsed descriptor service time;
- that controller, DMA, SRAM, and operator cycles share one clock;
- that the unmodified pipeline suite is a safe green integration certificate;
- that docs' depth-2/depth-3 timelines execute as drawn;
- that historical ideal-overlap TOPS are measured, calibrated, or generally attainable;
- that double buffering creates free capacity: equal shadow allocation doubles physical bytes for unchanged per-role usable capacity;
- that double buffering, banking, triple buffering, or a larger single buffer is universally optimal.
