# Chapter 18 framing and evidence plan — runtime context retention

- Date: 2026-08-05
- Edition pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Gate: mandatory Chapter 18 split/keep review
- Decision: **split the planned combined chapter**
- Selected Chapter 18 title: **Runtime Context Retention and Preemption Boundaries**
- New Chapter 19 title: **Static Scheduling and Scratchpad Allocation**
- Drafting status: **blocked** pending the source/claim ledger, executable audit, mutation proof, skeptical predraft review, and post-review seal
- Durable reproduction: [`../experiments/ch18_framing_reproduce.sh`](../experiments/ch18_framing_reproduce.sh) with retained [`chapter-18-framing-reproduction.log`](chapter-18-framing-reproduction.log)
- Review dispositions: [`chapter-18-framing-review-dispositions.md`](chapter-18-framing-review-dispositions.md)

## 1. Gate question and decision

The planned Chapter 18 grouped three resource-over-time surfaces:

1. runtime context retention and switching in `infra/tu_context.{h,c}`;
2. compile-time instruction ordering in `isa/tu_scheduler.{h,c}`; and
3. compile-time scratchpad liveness/allocation in `isa/tu_liveness.{h,c}`.

The gate asks whether one reader decision and one evidence ladder can teach all three without combining heterogeneous clocks, inventing an end-to-end compiler/runtime pipeline, or reducing the chapter to a catalogue.

**Decision: split.** Chapter 18 will answer one runtime architecture decision:

> At a legal preemption boundary, which state must be retained, who supplies the boundary and live-state contract, and which switch-cost and isolation claims follow from that choice?

Chapter 19 will answer one static compiler decision:

> Given an in-process `tu_instruction_t` sequence, which dependence, ordering, live-range, capacity, placement, and spill/fill claims are actually enforced before treating the rewritten sequence as legal?

The split is necessary because the context manager has runtime core state, caller-owned switch events, save/restore traffic, and isolation semantics, while scheduler/liveness operate on arrays of packed instruction structs with no non-test caller and no bridge to the context manager. The compiler pair is adjacent by intended pass order, but even that pair is not composed by pinned source. Keeping all three would require three independent caller inventories, three different notions of time, two distinct correctness contracts, and extensive Chapter 11 scheduler de-duplication. That is not one honest reader decision.

## 2. Lightweight global-plan consistency scan

### Triggered risks

- **Chapter 18 overload — triggered and resolved by split.** The live source confirms different owners, consumers, clocks, effects, tests, and integration status. The combined chapter would violate the plan's own split condition.
- **Broad synthesis becoming a catalogue — triggered and resolved by narrowing.** Chapter 18 now owns runtime retention/preemption only. Chapter 19 owns static ordering/allocation legality only.
- **Broken compiler path prematurely revived — triggered for the compiler half.** Chapter 19 must retain the negative boundary: no audited ONNX/compiler → scheduler → liveness → queue/runtime path exists at the pin.
- **Stable numbering versus provenance — partially triggered.** Completed Chapters 1–17 remain untouched. Only future chapters shift by one; the first edition becomes 23 chapters plus appendices.

### Risks not reopened

- Chapter 17/verification overlap remains closed: Chapter 17 owns measurement producers and denominators; the shifted verification chapter owns evidence selection and unsafe green-gate interpretation.
- The Chapter 8/10/14 supplement backlog remains deferred to the post-verification checkpoint.
- Source-edition drift is absent; `edition.yaml` remains pinned.
- No manuscript file or sealed evidence identifier is renumbered or moved.

## 3. Fresh comparable evidence inventory

All three implementation objects are members of `libtucmodel.a`, but linkage is not integration.

| Surface | Implementation | Focused executable evidence | Docs/sweeps | Aggregate `make test` | Non-test C caller outside own implementation |
|---|---:|---:|---:|---:|---:|
| runtime contexts | `tu_context.c/h`: 634/285 lines | `test_context.c`: 491 lines, 15/15; context sweep: 71 lines | `multi-context-execution.md`; `context-switch-state-scope.md` | context test omitted | none |
| static scheduler | `tu_scheduler.c/h`: 726/229 lines | `test_scheduler.c`: 534 lines, 14/14; policy sweep: 205 lines | `compiler-scheduling-pass.md`; `scheduler-policy-sweep.md` | included | none |
| liveness allocator | `tu_liveness.c/h`: 784/243 lines | `test_liveness.c`: 425 lines, 12/12 | `liveness-allocation.md`; no separate sweep | included | none |

A disposable `git archive` of the exact pin reproduced:

```text
context:  15/15 tests passed
scheduler: Results: 14/14 passed
liveness:  Results: 12/12 passed
```

The context sweep reproduced the exact retained-state model. For 256 KiB total W/A/O SRAM, fixed cost 100 cycles, and 32 B/cycle context-store bandwidth:

```text
full      state_B=262144  switch_cycles=16484
live25    state_B=65536   switch_cycles=4196
control   state_B=0       switch_cycles=100
```

The scheduler sweep reproduced identical results for ASAP, ALAP, and BALANCED on every shipped topology. The pipeline-tiles case is `28` estimated cycles, zero inserted barriers, zero reported hoists, and length `13` for all three policies. This is a static fixed-class sum, not runtime overlap.

The pinned source checkout remained detached, clean, and unchanged after the archive run.

### Independent reconnaissance disposition

Three read-only reconnaissance reviews independently inventoried contexts, scheduler, and liveness at the pin. The context and liveness reviews recommended the selected split. The scheduler review proposed keeping one chapter only if runtime retention remained the sole decision, scheduler was reduced to a Chapter 11 bridge, and liveness was treated as a candidate producer of retained-state knowledge. That alternative was rejected because the review itself found no scheduler→liveness call, no liveness→context live-prefix handoff, and no production caller: teaching liveness as part of the runtime decision would imply a source bridge that does not exist. The disagreement therefore strengthens rather than weakens the boundary: Chapter 18 may name the missing producer contract, but Chapter 19 must own the static implementation and its legality defects.

## 4. Ranked scope candidates

### Rank 1 — selected: split runtime retention from static scheduling/allocation

**Chapter 18 reader decision.** Choose FULL SRAM, declared live-prefix SRAM, or control-only retention at a named safe point; distinguish functional isolation from estimated switch traffic and omitted reload work.

**Chapter 19 reader decision.** Decide whether the scheduler/allocator's dependence and capacity contracts are strong enough to authorize a rewritten instruction sequence, and identify what must fail closed before execution.

**Benefits.** Each chapter has one owner, one principal correctness contract, and one coherent alternatives table. Chapter 18 can cover isolation, safe points, state scope, backing-store bandwidth, QoS, and lifecycle. Chapter 19 can cover DAG completeness, order selection, live ranges, physical placement, spill/fill legality, and the missing pass/runtime bridge. Chapter 11's scheduler findings become prerequisites rather than duplicated content.

**Costs.** The first-edition count grows from 22 to 23 and all future, unstarted chapters shift by one. The compiler chapter must still keep scheduler and liveness separate wherever the pin does not compose them.

### Rank 2 — rejected: keep all three under “where is resource time decided?”

**Reader decision.** Choose runtime time-slicing, compile-time reordering, or compile-time storage reuse as the control point for multiplexing.

**Benefit.** Preserves the 22-chapter count and offers a high-level comparison across runtime and compiler mechanisms.

**Why rejected.** These are not substitutable alternatives. Runtime contexts choose retained architectural state; scheduling chooses a topological order; liveness chooses physical offsets and synthetic spill/fill instructions. Their outputs, failure modes, and clocks cannot share a worked example or validation ladder. The source volume is 2,144 implementation lines plus 1,521 focused-test lines before docs, and the combined chapter would either duplicate Chapter 11 or under-audit the liveness allocator's severe legality defects.

### Rank 3 — rejected: Chapter 18 contexts plus liveness hints; defer scheduler

**Reader decision.** Connect `LIVE_SRAM` retention to compiler live-state metadata.

**Benefit.** The context manager's live-prefix mode explicitly motivates compiler-provided extents.

**Why rejected.** No call edge feeds allocator output into `live_w_bytes/live_a_bytes/live_o_bytes`; the allocator produces physical instruction offsets, while the context manager accepts one manually configured prefix per region. Presenting them as one path would manufacture the exact bridge the plan forbids. Scheduler semantics would also remain awkwardly divided between Chapters 11 and 19.

### Rank 4 — rejected: contexts only; fold liveness into verification or extension

**Benefit.** Gives Chapter 18 a narrow runtime contract without changing the chapter count if compiler allocation is omitted.

**Why rejected.** Chapter 11 explicitly deferred allocator semantics, and the allocator has substantial executable, test, and defect evidence. Verification and extension chapters have different reader decisions; hiding allocation there would create catalogue sections and leave a planned architecture decision uncovered.

## 5. Chapter 18 selected boundary

### Include

- manager/descriptor ownership and the `IDLE/ACTIVE/READY/BLOCKED/COMPLETED` vocabulary;
- allocation, save, restore, switch, block/unblock, round-robin, priority, and caller notifications;
- FULL, LIVE-prefix, and CONTROL-only retained SRAM semantics;
- exact cost equation:

```text
switch_cost = fixed_control_cost
            + ceil((outgoing_saved_bytes + incoming_saved_bytes)
                   / state_bytes_per_cycle)
```

- state that is actually copied, state merely named by comments, and state explicitly dropped;
- functional isolation versus unmodeled reload, backing-store, queue, contention, ECC, and dirty-map costs;
- public C configuration versus shipped JSON/YAML/runtime reachability;
- synchronization/drain claims versus the actual effect of `tu_core_sync()`;
- safe-point ownership, preemption granularity, QoS/fairness, lifecycle, and verification trade-offs;
- relation to Chapter 16's finding that context restore discards double-buffer ownership.

### Exclude

- scheduler algorithm details already owned by Chapter 11;
- static liveness/coloring/spill semantics, now Chapter 19;
- any compiler-produced live-prefix bridge;
- any ONNX/compiler/runtime end-to-end path;
- physical context-store area/energy/frequency claims;
- calibrated preemption latency, fairness, or transparent arbitrary-boundary preemption;
- Chapter 17 counter-domain synthesis.

## 6. Chapter 18 preliminary source map and bounded findings

### State and ownership

- `tu_ctx_manager_t` owns context descriptors and points at one caller-supplied `tu_core_t`.
- First allocation snapshots the current core and marks context 0 active; later allocations snapshot the same current core as ready contexts.
- Save calls `tu_core_sync()`, deep-copies retained SRAM bytes, copies selected region metadata, DMA struct state, dataflow pointer, runtime config, initialization state, and five legacy counters.
- Restore writes retained prefixes into already allocated core SRAM and restores selected metadata/state.
- Double-buffer pointers are set to `NULL`; command-queue contents are not preserved; the existing core queue pointer remains in place.

### Configuration and reachability

- Context policy is supplied through `tu_ctx_manager_config_t`, not shipped JSON/YAML or `tu_config_to_runtime()`.
- `save_dram_state` is declared but not consumed by the implementation.
- `has_config_override`, `config_override`, and `user_data` are descriptor fields with no switching effect in the implementation.
- Time-slice expiry is only a query over caller-fed counters. No non-test caller invokes notifications, expiry, or switching; there is no autonomous preemption engine.

### Preliminary defects and required discriminators

These are framing hypotheses to gate in the Chapter 18 ledger/audit, not yet manuscript authority:

1. **Priority zero starvation candidate.** Priority scheduling initializes `best_prio=0` and selects only `priority > best_prio`; a READY context at priority 0 may never be returned.
2. **Completion state reachability.** `TU_CTX_COMPLETED` is declared and printed, but no implementation path sets it.
3. **Command accounting.** `tu_ctx_notify_command()` increments only manager slice use; `tu_context_desc_t.total_commands` appears unproduced.
4. **Cycle accounting domains.** Caller-fed `slice_cycles_used`, core `estimated_cycles`, per-context `total_cycles`, and manager `total_cycles_stolen` are separate; no common-clock or automatic charging bridge is assumed.
5. **State-copy completeness.** Header prose names precision/rounding/performance state broadly; the implementation must be audited field by field against `tu_state_t` and process-global precision/rounding producers.
6. **Drain semantics.** The audit must prove what `tu_core_sync()` waits for and whether it drains every state copied or dropped; comments are not evidence.
7. **Error atomicity.** Failed partial deep copies, save failure, target restore failure, and freeing an active context require lifecycle probes and ownership review.
8. **Live-prefix contract.** Non-live tails deliberately remain from the incoming core image. Transparent isolation is valid only for FULL or after a proved software reload/live-prefix contract.
9. **Cost scope.** `total_cycles_stolen` records an analytical transfer equation but does not advance core time, queue time, DMA time, or Chapter 17 producers.
10. **Deferred-request contradiction.** The public header promises a switch at the next synchronization point, but `tu_ctx_request_switch()` immediately schedules and switches; no pending-request state is present.
11. **Shallow DMA snapshot.** `tu_dma_engine_t` contains descriptor `head`, `tail`, and `active` pointers even though context save copies the struct with `memcpy` and claims no heap pointers require deep copy. The audit must distinguish copied pointer identity from independent retained DMA work.
12. **Queue contract contradiction.** Header prose promises command-queue state save/restore, but save records only the queue pointer and restore intentionally keeps the live core queue and does not preserve its command/signal buffers or counters.
13. **Metadata versus bytes.** CONTROL_ONLY and LIVE modes leave some or all SRAM bytes from the intervening context while restore still overwrites bank metadata and total sizes. The audit must report these effects separately.
14. **Dead controls.** `save_dram_state` is not copied into the manager; per-context configuration overrides do not affect save/restore/scheduling. The chapter must not present either as an active design alternative at this pin.
15. **Embedded versus operative DMA state.** `tu_init_with_config()` zeroes `g_tu`, initializes the descriptor engine in process-global `g_tu_dma`, and never copies it into `g_tu.dma`; ordinary DMA functions consume `g_tu_dma`. Context save/restore copies only `tu_state_t.dma`, while `tu_core_sync()` drains only the command queue. The audit must not call that copied struct the operative DMA queue and must safely prove whether pending descriptor work is neither drained nor context-isolated.
16. **Global precision and plugin internals.** The process-global rounding mode and stochastic PRNG state are outside `tu_state_t`; context restore cannot restore them. The selected dataflow pointer is copied, but mutable plugin objects live in the process-global registry. Pointer restoration is not full plugin-state isolation.
17. **Single-active and failure atomicity.** Direct `tu_ctx_restore()` can activate a READY target without demoting the old ACTIVE descriptor. `tu_ctx_switch()` saves the outgoing context before validating/restoring the target, so invalid-target or restore failure can leave no ACTIVE descriptor and preserve a stale `active_ctx_id`. These transitions require explicit state-vector and accounting probes.
18. **Bank-arbitration state is only partly retained.** Save copies aggregate bank counters and bandwidth-policy scalars but deliberately nulls `bw_banks`; restore preserves the live core's existing `bw_banks` pointer and per-bank arbitration contents. The audit must separate restored aggregate metadata from non-restored per-bank bandwidth state.

## 7. New Chapter 19 boundary

Chapter 19 will jointly audit scheduler and liveness because both consume/produce `tu_instruction_t` arrays and together pose a coherent static legality question. It must nevertheless preserve their missing bridge.

Scheduler prerequisites imported from Chapter 11:

- named hoist and barrier passes count candidates but do not transform graph/output as advertised;
- full-run bookkeeping clears those counts;
- dense dependencies silently truncate at 16;
- `pipeline_tiles` and `max_window` are inert in `tu_scheduler.c`;
- the fixed `1`-per-DMA/`4`-per-other-node sum is uncalibrated and serial;
- no non-test compiler/runtime caller exists.

Liveness hypotheses requiring fail-closed probes:

- uses ignore byte ranges and attach to the most recent definition in the same region;
- FIRST/BEST/WORST strategy names may not correspond to three distinct placement algorithms;
- capacity minus safety margin may underflow;
- no-spill failure force-places at offset zero and still reports success;
- victim selection does not clearly evict already placed interfering values;
- spilled values can retain `UINT32_MAX` offsets that are truncated into 16-bit DMA fields;
- fill insertion occurs repeatedly across a live interval, while the spill store is emitted only after the last use;
- output capacity truncation can still end with `valid=true`;
- rewriting patches only selected opcode/operand forms and can bind a use to the wrong live value;
- tests largely check success/presence/bounds rather than semantic equivalence of the rewritten program.

## 8. Required Chapter 18 evidence before drafting

The framing decision does **not** authorize drafting yet. Chapter 18 requires:

1. a source-and-claim ledger with field-complete state-preservation census;
2. pin-locked hashes and structural predicates for context source/header, core/state/sync dependencies, config surfaces, tests, sweep, docs, Makefile, and Chapter 16/17 boundary evidence;
3. an exact whole-tree caller inventory;
4. focused 15/15 execution plus a real assertion mutation;
5. a custom bounded probe covering all three save scopes, intentionally stale tails, byte-versus-bank-metadata and per-bank-arbitration restoration, priority zero, completion reachability, immediate-versus-deferred request semantics, command/cycle counters, queue non-restoration, embedded-versus-operative DMA state, safely bounded pending-DMA behavior, global rounding/plugin state, dead `save_dram_state`/override controls, blocking, failed/invalid configs, and manager-local switch-cost accounting;
6. a field-complete state-transition matrix. Before and after every row it must record: all manager fields (`active_count`, `active_ctx_id`, slice command/cycle counters, pending save bytes, total switches, and stolen cycles); every descriptor's state, priority, live-byte controls, command/cycle/switch counters, last-switch cycle, override flag/value, and saved-state ownership; retained core SRAM bytes plus aggregate and per-bank metadata, command-queue contents/signals/counters and pointer identity, embedded DMA state, operative process-global `g_tu_dma`, runtime config, dataflow pointer plus mutable plugin counters, rounding mode plus a deterministic stochastic-PRNG discriminator, core legacy counters, and core clock; and operation return/status. The row set must cover manager creation/config rejection, allocation/exhaustion/get, save/restore, direct restore while another context is ACTIVE, active/READY/BLOCKED/IDLE free, self-target switch, out-of-range/`IDLE`/`BLOCKED`/already-`ACTIVE` targets, request-switch, all scheduler policies, repeated equal-priority ties, priority zero, exact/under/over command and cycle slice thresholds, block/unblock in every relevant state, notify/getter calls, repeated accepted/rejected trajectories, and safely injectable partial-copy/allocation failures. Every row must classify ownership (`active_ctx_id`, descriptor states, and `active_count` together), retention, accounting deltas, and whether a rejected or failed operation is atomic; unsupported safe failure injection remains an explicit blocked claim rather than an inferred pass;
7. independent recomputation of every sweep row used in prose;
8. explicit tests that cost accounting does not silently advance another clock;
9. a skeptical predraft review and post-review reseal if any input or predicate changes;
10. a predraft validator that passes under normal and optimized Python and rejects a real source assertion mutation.

## 9. Publication and repository constraints

- Book work lands on local `main`.
- Pinned Tusim remains detached, clean, and read-only.
- Build/probe work uses disposable archives.
- No push, curated rebuild, publication, source edit, force operation, or remote write is authorized by this framing gate.
