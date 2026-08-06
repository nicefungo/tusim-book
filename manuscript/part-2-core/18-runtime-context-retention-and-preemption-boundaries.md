# Chapter 18 — Runtime Context Retention and Preemption Boundaries

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

> **Chapter contract.** At this edition, Tusim's context manager is standalone executable C machinery for copying selected state and immediately changing descriptors. It has no external non-test caller, no shipped JSON/YAML construction path, and no compiler or runtime producer for legal safe points or live prefixes. It therefore does **not** establish autonomous or arbitrary-boundary preemption, transparent tenant isolation, fair scheduling, or calibrated handoff latency. FULL, LIVE-prefix, and CONTROL-only are different retention contracts. Each becomes correct only at a caller-established legal boundary and with an explicit contract for omitted state. Corrected canonical v7 is the sole drafting authority; v5 and v6 are retained superseded history.

## Learning objectives

After this chapter, you should be able to:

1. distinguish a legal preemption boundary from an API call boundary;
2. name the safe-point, retained-set, ownership, and shared-state contracts needed for continuation;
3. classify FULL, LIVE-prefix, and CONTROL-only retention without ranking them as fidelity levels;
4. reason about ownership from `(active_ctx_id, all descriptor states, active_count)` rather than one field;
5. explain why allocation clones the current shared core image rather than creating a blank context;
6. trace manager creation, allocation, save, restore, switch, block, unblock, and free;
7. recognize direct restore and rejected-switch failures that violate the intended single-owner invariant;
8. derive retained bytes and the exact manager-local switch-cost equation;
9. distinguish normal save-plus-restore traffic from direct-restore and failed-switch call histories;
10. separate retained primary SRAM bytes and aggregate metadata from live per-bank `bw_banks` state;
11. identify queue, operative DMA, plugin, precision, outer-core, ICC, DRAM, and double-buffer boundaries;
12. explain priority ties, priority zero, inclusive slice thresholds, notification wrap, and absent fairness;
13. evaluate FULL, LIVE-prefix, and CONTROL-only by correctness regime, traffic, implementation cost, and verification burden; and
14. state exactly what canonical v7 proves and which conclusions remain unsafe.

## Prerequisite graph

```text
Chapter 5: lifecycle, ownership, global swap, and failure atomicity
                              │
Chapter 9: W/A/O SRAM capacity, aggregate metadata, bank service state
                              │
Chapter 10: descriptor DMA progress and completion ownership
                              │
Chapter 15: caller-owned DRAM models and independent clocks
                              │
Chapter 16: double-buffer role and allocation ownership
                              │
Chapter 17: producer, interval, clock, equation, and fidelity discipline
                              ▼
 safe point + retained set + ownership transition + shared-state handling
                              │
                              ▼
             defensible context-continuation claim
                              │
Chapter 18 names the missing live-state producer contract
                              ▼
Chapter 19 audits compile-time scheduling and liveness separately
```

The graph matters because context switching crosses boundaries established earlier. A copied pointer is not ownership. A counter name is not a clock. A queue synchronization call is not necessarily a DMA drain. A primary SRAM image is not every piece of accelerator state. Chapter 18 uses those distinctions rather than inventing one integrated preemption subsystem.

## Opening architecture question: what must survive a legal preemption?

Imagine context A executing while weights, activations, and partial outputs occupy the W/A/O SRAM regions. Context B is READY. A runtime wants to stop A, run B, and later resume A. Before discussing a context descriptor or API, answer five architecture questions.

1. **Is the boundary legal?** Are all effects that must precede suspension complete, or is a producer still able to mutate state after the snapshot begins?
2. **What belongs to A?** Which bytes, counters, modes, dependencies, and ownership records are private state rather than shared machine state?
3. **What is still in flight?** Have command-queue work, global descriptor DMA, pipelines, and external-memory operations drained or been transferred to a new owner?
4. **What remains shared?** Do plugins, precision controls, outer-core resources, ICC buffers, and caller-owned DRAM continue globally?
5. **What does cost mean?** Is a reported number copied bytes, an analytical ledger, elapsed model time, host memcpy duration, or measured hardware latency?

These questions are independent. A complete byte copy at an illegal boundary is wrong. A legal boundary with an incomplete retained set is also wrong. Both can coexist with a successful return code. The central decision is therefore:

> At a named caller-established legal boundary, should the system retain all primary W/A/O bytes, caller-declared W/A/O prefixes, or no SRAM bytes—and which external contracts make that choice correct?

A useful hardware-neutral expression is

\[
\text{legal continuation} =
\text{safe boundary}
+ \text{sufficient retained state}
+ \text{valid ownership transition}
+ \text{handling of shared and in-flight state}.
\]

The Tusim manager implements only selected pieces of this expression. It copies selected state and changes lifecycle labels. `tu_ctx_request_switch()` invokes selection and switching immediately; it does not record a request for a future safe point. Slice expiry is a query. Notifications are caller-fed. There is no automatic safe-point discovery, compiler-produced liveness bridge, or autonomous scheduling loop. Those absences define the chapter boundary.

## 18.1 Theory and terminology: four correctness obligations plus cost

### Safe point and quiescence

A **safe point** is an execution boundary at which suspension preserves all effects required for later continuation. It may be an instruction boundary, a drained command boundary, an explicitly synchronized checkpoint, or a software-declared quiescent point. These are not synonyms. An arbitrary-boundary mechanism must capture more transient state than a drained checkpoint. A command boundary may still have DMA in flight. A synchronous queue may return from its sync path without saying anything about another global engine.

The owner of the safe-point contract must be named. It could be a compiler, command processor, runtime, host protocol, or hardware interrupt mechanism. Tusim's context manager names none of them as an integrated producer. Its API call boundary is merely where the C function runs. Therefore the chapter uses **caller-established legal boundary** whenever it reasons about correct use.

The header's broad “thread-safe context switching” language is not supported as a concurrency guarantee. The manager has no lock or synchronization primitive, and the core's global-state swap window was already bounded in [Chapter 5](05-state-lifecycle-and-public-apis.md). A caller can serialize access externally, but that external serialization is not supplied by this manager.

### Retained set and reconstruction contract

Let the required continuation state be

\[
R = R_{control} \cup R_{local\ memory} \cup R_{metadata}
    \cup R_{inflight} \cup R_{global\ modes}.
\]

A transparent mechanism must retain all required members of \(R\). A partial mechanism can omit members only if a reconstruction, reload, drain, or shared-object contract gives those members correct values before use. “Not copied” is not automatically a defect: CONTROL-only deliberately copies no SRAM. The defect appears when prose promises transparent isolation while the omitted-state contract is absent.

Tusim exposes three local-memory policies:

- **FULL** deep-copies each W/A/O region's complete primary byte capacity.
- **LIVE-prefix** deep-copies one caller-configured prefix in each region.
- **CONTROL-only** copies zero W/A/O bytes.

They are architecture alternatives, not low/medium/high quality. FULL increases copied bytes and context-store capacity. LIVE-prefix reduces traffic but requires trustworthy extents and a dead-tail or reload proof. CONTROL-only shifts all SRAM reconstruction to software. None captures every queue, DMA, plugin, precision, outer-core, DRAM, or double-buffer property.

### Ownership invariant

Tusim stores an `active_ctx_id`, lifecycle state in each descriptor, and `active_count`. The last name is misleading if read as “number of ACTIVE descriptors”: it is intended and used as the number of allocated non-IDLE slots. Even that interpretation can be corrupted by freeing an already-IDLE slot.

Define

```text
owner_tuple = (
    active_ctx_id,
    state of every descriptor,
    active_count
)
```

For a healthy executing manager, the intended invariant is:

```text
exactly one descriptor is ACTIVE;
active_ctx_id names that descriptor; and
active_count equals the number of allocated non-IDLE descriptors.
```

No single scalar proves this invariant. `active_ctx_id` can be stale while no descriptor is ACTIVE. One descriptor can remain ACTIVE while `active_ctx_id` names another. Two descriptors can be ACTIVE. `active_count` can be zero while one allocated descriptor remains ACTIVE. Verification must inspect the tuple after every successful and rejected operation.

### Shared and in-flight state contract

State outside the descriptor still needs an owner and a continuation rule. Queue work, operative DMA, plugin internals, precision controls, outer-core/ICC resources, DRAM, and double-buffer ownership may need to be drained, transferred, reconstructed, serialized, or explicitly shared. A legal boundary and correct W/A/O bytes do not make those obligations disappear. This is the fourth correctness obligation in the legal-continuation expression.

### Cost characterization

A complete architectural handoff cost might include fixed control work, pipeline and queue drainage, outgoing movement, incoming movement, software reload, backing-store traffic, arbitration, context-store queueing, ECC, and contention. Tusim records only a manager-local analytical subset.

Let

- \(F\) be `fixed_switch_cycles`;
- \(P\) be `pending_save_bytes`, which is call-history state rather than necessarily one matching atomic handoff;
- \(B_{in}\) be the target descriptor's saved W/A/O bytes;
- \(W\) be `state_bytes_per_cycle`.

The restore-time ledger increment is exactly

\[
\Delta C =
\begin{cases}
F + \left\lceil\dfrac{P+B_{in}}{W}\right\rceil, & W>0,\\[6pt]
F, & W=0.
\end{cases}
\]

For an ordinary successful switch between equal-size descriptors, and only then, \(P=B_{in}=B\), so

\[
B=B_W+B_A+B_O,
\qquad
\Delta C=F+\left\lceil\dfrac{2B}{W}\right\rceil.
\]

Zero bandwidth suppresses the transfer term. It is neither rejected configuration nor infinite latency. Direct restore can charge incoming bytes without an outgoing save. A failed switch can leave outgoing pending bytes for a later restore. `total_cycles_stolen` is therefore a **call-history analytical ledger**, not elapsed switch time and not a Chapter 17 common clock.

## 18.2 Source map and reachability boundary

The public header yields exactly 19 `tu_ctx_*` operations. The source audit derives this list rather than trusting a handwritten count.

| Role | Public operations |
|---|---|
| Manager lifecycle | `tu_ctx_manager_config_validate`, `tu_ctx_manager_create`, `tu_ctx_manager_destroy` |
| Descriptor lifecycle | `tu_ctx_alloc`, `tu_ctx_free`, `tu_ctx_get` |
| Retention and handoff | `tu_ctx_save`, `tu_ctx_restore`, `tu_ctx_switch`, `tu_ctx_request_switch` |
| Selection and state | `tu_ctx_schedule_next`, `tu_ctx_slice_expired`, `tu_ctx_block_current`, `tu_ctx_unblock` |
| Caller notifications | `tu_ctx_notify_command`, `tu_ctx_notify_cycles` |
| Reporting | `tu_ctx_print_status`, `tu_ctx_get_switch_count`, `tu_ctx_get_switch_overhead` |

`tu_context.o` is archived in `libtucmodel.a`. Focused context and sweep Makefile rules exist. The context target is not an aggregate `make test` prerequisite. More importantly, the audit finds `CH18_CALLERS external_nontest=none`: outside implementation, header, tests, and documentation, no production caller reaches the API. Shipped JSON, YAML, parsing, and runtime conversion contain no context-manager block. Linkage proves resolvability; focused tests prove bounded standalone behavior; neither establishes runtime integration.

The object relationship is:

```text
tu_ctx_manager_t
 ├── core ─────────────────────────► one shared tu_core_t
 ├── contexts[] ───────────────────► descriptor snapshots
 ├── active_ctx_id
 ├── active_count
 ├── caller-fed slice counters
 ├── pending_save_bytes
 └── total_cycles_stolen ──────────► manager-local analytical ledger

tu_context_desc_t
 ├── lifecycle state and priority
 ├── selected tu_state_t image
 ├── separately allocated saved W/A/O bytes
 ├── accounting fields
 └── override/user metadata with no switching effect at this pin
```

Context policy is C-API-only. Operational controls include policy, save scope, live W/A/O extents, fixed cost, state bandwidth, and slice thresholds. `save_dram_state` is declared but never copied into the manager or consumed. `has_config_override`, `config_override`, and `user_data` remain descriptor metadata without scheduling or switching effects. Validation rejects null core/configuration inputs, zero slots, invalid policy/scope, and LIVE extents above region capacities. It does not semantically bound maximum contexts, fixed cost, bandwidth, time slices, or priority beyond their C types.

The source map must also distinguish selected state from the full machine:

| Surface | Retained behavior | Shared, dropped, or external behavior | Safe claim |
|---|---|---|---|
| W/A/O primary bytes | FULL capacities or LIVE prefixes; none for CONTROL | LIVE/CONTROL tails remain from intervening image | isolation only for retained bytes under an external contract |
| SRAM region metadata | `total_size`, bank capacity/geometry, aggregate counters, policy scalars, region cycle, name | saved `bw_banks` is not retained | aggregate metadata can differ from live per-bank service state |
| Command queue | selected pointer appears in saved state | restore keeps live pointer and queue internals | queue is not a per-context snapshot |
| Embedded DMA | `tu_state_t.dma` struct copied | ordinary descriptor APIs use process-global `g_tu_dma` | embedded copy is not operative DMA isolation |
| Dataflow plugin | selected pointer copied | registry, counters, `impl_data`, mutable object state shared | pointer selection, not plugin isolation |
| Precision state | none for global rounding, PRNG, subnormal, error modes | all continue process-globally | no per-context precision-mode isolation |
| Legacy ledgers | five selected fields copied | most Chapter 17 producers remain separate | selected counter retention only |
| Outer `tu_core_t` | no per-descriptor outer identity/init/ICC image | shared outer object and ownership | descriptor is not a complete core snapshot |
| DRAM | no model in `tu_state_t` | independently created, caller-owned object | `save_dram_state` is dead |
| Double buffer | no role/ownership serialization | live `db` pointer is nulled on restore | ownership and active role can be lost |

## 18.3 Implementation walk-through

### Manager creation and destruction

Creation validates the supplied core and configuration, allocates the manager, allocates the descriptor array, initializes slots, and gives each descriptor default priority `128`. The manager points at one existing `tu_core_t`; it does not create a scheduler loop or attach itself to ordinary core execution. A real manager-construction `calloc` failure is structurally handled, but canonical v7 does not globally wrap `calloc` because that would perturb core, plugin, and queue setup. That path remains a structural claim, not an executable failure-injection result.

Destruction releases retained allocations and manager storage. Destruction does not transform an unintegrated manager into a runtime owner, nor can it retroactively drain shared queue or global DMA work. Lifecycle correctness still depends on the caller's sequencing.

### Allocation is cloning

Allocation searches for the first IDLE descriptor, clears it, marks it READY, snapshots the current shared core image, marks it ACTIVE only when `active_count==0`, and increments `active_count`. This is cloning, not independent blank construction.

The canonical discriminator allocates contexts around changes to the shared image:

```text
ROW allocation_clone RESULT ids=0/1 bytes=31/42 dma=31/42 estimated=100/105 last=0/0
```

The values `31` and `42` are fixture sentinels, not architecture constants. Their importance is inheritance: each allocation captures the then-current bytes and legacy DMA ledger. The contexts also inherit `estimated_cycles` values `100` and `105`, while both saved `last_switch_cycle` values remain zero. A READY context can therefore begin with the ACTIVE context's bytes, counters, runtime configuration, and shared pointers as they existed at allocation time. Isolation begins only after the inherited image and later bounded transitions are understood.

The zero baseline causes another defect. Save computes

\[
\text{ctx.total_cycles} \mathrel{+}=
\text{core.estimated_cycles}-\text{ctx.last_switch_cycle}
\]

with unsigned arithmetic. The first descriptor's initial baseline is zero, so its first save attributes all pre-allocation core history to that context. If the core counter regresses from 10 to 5 relative to the saved baseline, `5-10` wraps to `18446744073709551611`.

### Save

`tu_ctx_save()` first calls `tu_core_sync()`. That helper swaps the selected core state into process-global `g_tu`, invokes only `tu_cmdq_sync_all()`, then swaps back. A synchronous queue returns immediately. An asynchronous queue loops until `count==0` with no timeout or deadlock escape. The helper does not flush the operative process-global descriptor DMA engine.

Save then frees the descriptor's prior retained W/A/O allocations before allocating replacements. Exactly three retained-copy calls exist. Under the 64-byte fixture, injected failures at ordinal one, two, or three request exact sizes `64/0/0`, `64/64/0`, and `64/64/64`. Initial allocation failure returns `-1`, leaves the slot IDLE with `active_count=0`, and frees partial allocations.

Replacement is not transactional. Re-saving an existing context destroys the old retained arrays before all replacement allocations succeed. The canonical destructive re-save failure reaches two 64-byte calls and can leave the descriptor ACTIVE while its previous complete restorable snapshot is gone. There is no rollback. This is a distinct property from the clean initial-allocation failure path.

After a successful copy, selected core fields are recorded, the descriptor becomes READY, `pending_save_bytes` is set, and unchecked cycle subtraction updates descriptor accounting. Save alone can therefore leave no ACTIVE descriptor; it is a lower-level operation, not an ownership-safe complete handoff.

### Restore

Restore accepts only a READY target. It copies retained bytes and selected metadata, marks the target ACTIVE, changes `active_ctx_id`, increments switch count, charges the manager ledger, clears pending traffic, and resets slice counters. It does **not** demote some other ACTIVE descriptor. Therefore it is unsafe as an independent switching primitive while another owner is ACTIVE.

Two canonical direct-restore histories illustrate both ownership and cost:

```text
incoming-only direct restore:
  mgr=2/1/2/4, switches=1/13
  two ACTIVE descriptors, analytical charge 13

restore after a prior 192-byte save:
  mgr=2/1/1/4, switches=1/19
  analytical charge 19
```

For three 64-byte regions, \(B=192\), \(F=7\), and \(W=32\). Incoming-only restore gives `7+ceil(192/32)=13`. An outgoing-plus-incoming call history gives `7+ceil(384/32)=19`. Target identity alone does not determine the ledger.

Restore has no supported normal allocation failure point after READY validation. Corrupting retained pointers or lengths to force a copy failure would invoke undefined behavior. Restore failure atomicity beyond state validation therefore remains blocked rather than “tested.”

### Switch and request-switch

The implementation sequence is conceptually:

```text
tu_ctx_switch(target):
    locate and save the current ACTIVE descriptor
    restore target
```

Target validation occurs during restore, after outgoing mutation. Invalid, IDLE, BLOCKED, or already-ACTIVE targets can therefore fail after the outgoing owner has been saved and demoted. Rejected switching is not failure-atomic.

A self-target switch is accepted. The current descriptor is saved to READY and immediately restored. It increments switch count and charges fixed plus traffic cost even though the architectural request names the same context. The API does not reject this no-op request.

`tu_ctx_request_switch()` calls selection and switching immediately. There is no pending-request bit, synchronization-point queue, interrupt delivery, or later callback. Calling it a “request” does not make it deferred.

### Block, unblock, and free

`tu_ctx_block_current()` saves the active descriptor and then marks it BLOCKED. That leaves no ACTIVE descriptor and a stale manager owner until caller code selects and restores another context. `tu_ctx_unblock()` returns success for every in-range descriptor state, but mutates only BLOCKED to READY. `TU_CTX_COMPLETED` is printable lifecycle vocabulary, but it is not scheduler-eligible and no pinned implementation path produces it.

Free accepts READY, BLOCKED, COMPLETED, and IDLE descriptors despite narrower header prose. Freeing ACTIVE first saves and then frees it, leaving no owner and stale `active_ctx_id`. Freeing an already-IDLE slot decrements `active_count` whenever another context exists. Slot reuse after active free can then produce two READY descriptors, zero ACTIVE descriptors, and stale ownership.

## 18.4 Ownership failures as state vectors

Compact vectors reveal defects that return-code-only tests miss.

| Operation | Before | Return | After | Architectural result |
|---|---|---:|---|---|
| direct restore target 1 | ctx0 ACTIVE, ctx1 READY, owner 0 | `0` | ctx0 ACTIVE, ctx1 ACTIVE, owner 1 | two owners |
| switch invalid/IDLE/BLOCKED | ctx0 ACTIVE | `-1` | no ACTIVE, owner stale, pending `192` | failure mutates outgoing owner |
| switch already ACTIVE | two ACTIVE due to prior misuse | `-1` | one ACTIVE but owner names another, pending `192` | tuple inconsistent |
| self switch | ctx0 ACTIVE | `0` | ctx0 ACTIVE, one switch, overhead `19` | accepted and fully charged |
| free ACTIVE | ctx0 ACTIVE, ctx1 READY | `0` | ctx0 IDLE, ctx1 READY, no ACTIVE | no replacement ownership |
| free IDLE | ctx0 ACTIVE, another slot IDLE | `0` | ctx0 ACTIVE, `active_count=0` | allocated count corrupted |
| reuse after active free | ctx1 READY, owner stale, count 1 | slot 0 | ctx0 READY, ctx1 READY | zero owners persist |
| block current | ctx0 ACTIVE | `0` | ctx0 BLOCKED, no ACTIVE | caller must schedule/restore |

The retained probe vectors include:

```text
free ACTIVE:             mgr=1/0/0/4 pending=192
free IDLE:               mgr=0/0/1/4
reuse after ACTIVE free: mgr=2/0/0/4 pending=192
direct restore:          mgr=2/1/2/4 switches=1/13
already-ACTIVE reject:   mgr=2/1/1/4 pending=192
```

The tuple notation in these compact records is `active_count/active_ctx_id/number_of_ACTIVE/max_contexts`. Their lesson is not that callers should memorize vectors; it is that lifecycle APIs must be checked against global invariants on both success and failure.

A robust implementation would validate the target before touching the outgoing owner, stage a replacement snapshot before freeing the old one, commit ownership atomically, and either choose a successor when freeing/blocking ACTIVE or reject the operation. Direct save/restore could be private helpers beneath one transactional switch operation. At minimum, runtime invariant checks should recompute allocated and ACTIVE counts from descriptor states.

## 18.5 Scheduling and notification accounting

### Round-robin

Round-robin scans from the slot after `active_ctx_id`, wraps by index, and returns the first READY descriptor. This is deterministic traversal. It is not a fairness, bounded-wait, throughput, or service guarantee. Blocking patterns, repeated readiness, caller switch timing, and absent runtime integration remain outside the selector.

### Priority

Priority selection initializes `best_prio=0` and updates the winner only for a strictly greater READY priority. Consequently:

- a READY priority-zero descriptor is unschedulable;
- equal positive priorities retain the first encountered, the lowest matching slot;
- repeated selection can return the same low slot (`first=1 second=1`);
- there is no aging, weighted service, or starvation prevention.

Priority is a selection key, not a QoS contract. The manager records no calibrated service, deadline, or fairness metric.

### Slice thresholds

Cycle and command expiry are independent inclusive predicates:

\[
\text{expired} =
(L_c\ne0 \land U_c\ge L_c)
\lor
(L_m\ne0 \land U_m\ge L_m).
\]

For cycle limit 10, canonical values are `9/10/11 -> false/true/true`. For command limit 3, they are `2/3/4 -> false/true/true`. Zero disables the corresponding threshold. Querying expiry does not switch anything automatically.

### Caller-fed counters and wrap

`tu_ctx_notify_command()` and `tu_ctx_notify_cycles()` update manager slice counters, including when no descriptor is ACTIVE. They do not create per-context execution accounting. Descriptor `total_commands` has no producer. `total_cycles` changes only on save using the unsigned legacy-core difference discussed earlier.

Neither notification increment checks overflow. Adding one to maximum values wraps both counters to zero:

```text
ROW notify_wrap RESULT cmds=0 cycles=0 expired=0
```

Thus an expired slice can appear fresh. Notifications with no owner can still move the manager counters to `5/5`. These are caller-authored control inputs, not evidence of elapsed accelerator execution or calibrated scheduling.

## 18.6 Retained SRAM alternatives and the metadata split

### Primary-byte policies

| Policy | Saved bytes | Restore effect | Required external correctness contract |
|---|---:|---|---|
| FULL | complete W+A+O capacities | all primary W/A/O bytes restored | legal safe point plus handling of all non-SRAM shared/in-flight state |
| LIVE-prefix | one caller-configured prefix per region | prefixes restored; tails remain from intervening image | trustworthy extents, legal safe point, dead-tail or reload proof |
| CONTROL-only | `0 B` | all physical SRAM bytes remain from intervening image | complete software reload/reconstruction before use |

LIVE extents are prefixes, not arbitrary intervals, dirty blocks, compiler-produced liveness, or a verified minimal state set. Validation only compares each extent with its region size. Chapter 19 may investigate compile-time scheduling and liveness, but no bridge from those analyses to `live_w_bytes`, `live_a_bytes`, or `live_o_bytes` exists at this pin.

### Reproducible stale-tail example

The focused LIVE fixture uses four-byte W/A/O prefixes, \(F=7\), and \(W=8\) B/cycle. Consider two floats in W:

```text
ctx0 before save: [1.0, 2.0]
ctx1 intervening: [10.0, 20.0]
restore ctx0:      [1.0, 20.0]
```

Only the first four-byte prefix returns from context 0. The tail is whatever the intervening core left behind. Calling this transparent tenant isolation would be false. It is prefix restoration conditional on a caller-established legal boundary, explicit handling of shared and in-flight state, and proof that the tail is dead or reloaded.

The retained bytes are

\[
B=4+4+4=12\ \text{B}.
\]

Each ordinary equal-size switch costs

\[
7+\left\lceil\frac{12+12}{8}\right\rceil
=7+3=10\ \text{analytical cycles},
\]

and two accepted switches yield cumulative `switches=2/20`. CONTROL retains zero bytes, leaves W as `22/22` in the discriminator, and records `switches=2/14`: fixed seven twice. With `fixed_switch_cycles=7` and `state_bytes_per_cycle=0`, it likewise records a seven-cycle fixed-only ledger increment rather than infinite cost.

### Metadata census: `total_size` retained, `bw_banks` not retained

This qualification is hostile-review critical. Save and restore explicitly carry each W/A/O region's:

- `total_size`;
- bank capacity and geometry;
- aggregate reads, writes, bank conflicts, and stall cycles;
- bandwidth-policy scalars;
- region current cycle; and
- name.

The saved image does **not** retain `bw_banks`, the per-bank arbitration/service records. Restore therefore combines aggregate metadata from one context with live per-bank state left by another. This is not whole-object restoration.

Canonical v5 falsely claimed that `total_size` was omitted because an under-scoped predicate inspected only a helper and missed assignments in the enclosing save path. Pinned `tu_context.c:122–125` saves W/A/O `total_size`; lines `187`, `204`, and `221` restore them. Corrected canonical v7 includes that predicate repair plus the later COMPLETED lifecycle-wording correction. The correct sentence is exact: **W/A/O `total_size` is saved and restored, while saved `bw_banks` contents are not retained.** Never invert either half.

### Double-buffer ownership

Restore sets each live region's `db` pointer to `NULL` without serializing active/shadow role and without freeing the displaced live object. Ownership and role identity can be lost, and an allocation can leak. The bounded Chapter 18 probe avoids executing that leaking trajectory. [Chapter 16](16-double-buffering-and-legal-overlap.md) remains authoritative for its sealed executable evidence. The Chapter 18 sanitizer result must not be promoted into safety evidence for an intentionally unexecuted leak path.

## 18.7 Queue, DMA, plugin, precision, and outer-state boundaries

### Queue is live, not restored

Header and documentation claims about queue snapshot/recreation do not match implementation. Save records a pointer as part of selected state, while restore deliberately preserves the live core queue pointer. Commands, dependencies, signals, indices, counts, and queue clock are not reconstructed per descriptor.

The canonical probe uses a fabricated but memory-safe discriminating queue image. Its sentinels remain live across a switch. This proves copying and pointer behavior; it is not a legal asynchronous-drain experiment. An unresolved asynchronous queue can make `tu_core_sync()` loop indefinitely. The synchronous case returns immediately. Neither behavior drains the separate process-global descriptor DMA.

OpenCL's primary command-queue specification provides useful vocabulary for commands, events, and synchronization, but Tusim's pinned semantics are established by executable source rather than inferred from that standard ([OCL311](../../references/foundations.md#ocl311-opencl-command-queue-contract)).

### Embedded and operative DMA are different objects

`tu_state_t.dma` is an embedded struct and is copied. `tu_init_with_config()` separately initializes process-global `g_tu_dma`, and ordinary descriptor APIs consume that global engine. If shallow descriptor pointers were placed in the embedded struct, copying them would not establish ownership. More decisively, a safely bounded pending global descriptor survives `tu_ctx_switch()` with queue depth and pointer identity unchanged while the target's embedded DMA snapshot is restored independently.

Therefore “DMA is retained” is too broad. The selected embedded struct is copied; operative global descriptor work remains shared and undrained. [Chapter 10](10-dma-descriptor-contracts-and-tick-driven-execution.md) supplies the earlier distinction among descriptor completion, progress, and queue ownership.

### Plugin pointer versus plugin object

The selected dataflow plugin pointer is copied with core state. The registry and plugin objects are process-global and mutable. Public counters such as `total_flops`, `total_tiles`, and `total_cycles`, plus opaque `impl_data`, remain shared. Pointer restoration chooses a shared object; it does not clone or isolate plugin internals.

### Precision modes continue globally

Rounding mode, xorshift PRNG state, subnormal mode, and error mode are process-global and absent from both `tu_state_t` and the manager. The probe distinguishes deterministic stochastic continuation with `0.60181281637875705` and `0.77984955054230642`, and separately discriminates subnormal mode. Error mode is hash-locked and structurally classified. Context switching does not reset or restore these controls.

This matters for reproducibility: two contexts that assume independent stochastic streams or rounding modes can influence each other even when their primary SRAM prefixes are correct. A future design must choose between per-context capture, explicit global serialization, or a documented shared-mode contract.

### Selected legacy ledgers are not every measurement producer

The implementation copies five legacy fields: `total_dma_bytes`, MMA calls, MMA tiles, MMA FLOPs, and `estimated_cycles`. It also copies runtime configuration, selected dataflow pointer, embedded DMA struct, and `initialized`. It does not retain every counter, trace, cycle model, or power producer classified in [Chapter 17](17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md). `total_cycles_stolen` does not advance legacy core time, queue time, global DMA time, bank clocks, or those independent producers.

### Outer core, ICC, and DRAM

Descriptors snapshot selected `tu_state_t`, not outer `tu_core_t` identity, initialization ownership, or ICC buffers. The manager shares one outer core. No DRAM model is a `tu_state_t` member; standalone DRAM objects are created and owned by callers. `save_dram_state` has no consumer. FULL therefore means full primary W/A/O byte retention within this model, not full machine-state retention.

## 18.8 Worked reproducible derivation: exact sweep arithmetic

The retained sweep uses the pinned revision, a 16×16 core configuration, binary KiB capacities, fixed cost \(F=100\) cycles, and default state bandwidth \(W=32\) B/cycle. It partitions total SRAM as

\[
B_W=\frac{T}{2},\qquad B_A=\frac{T}{4},\qquad
B_O=\frac{T}{4},\qquad B_W+B_A+B_O=T.
\]

LIVE25 retains one quarter of each region, hence \(B=T/4\). All cycle values are deterministic outputs of the manager's estimated analytical ledger. They are not host memcpy measurements, RTL cycles, calibrated preemption latency, a lower bound, or end-to-end resume time.

| Total SRAM | Policy | Retained `B` | Exact derivation | Switch ledger |
|---:|---|---:|---|---:|
| 128 KiB | FULL | `131072 B` | `100 + ceil(262144/32)` | `8292 cycles` |
| 128 KiB | LIVE25 | `32768 B` | `100 + ceil(65536/32)` | `2148 cycles` |
| 128 KiB | CONTROL | `0 B` | `100 + 0` | `100 cycles` |
| 256 KiB | FULL | `262144 B` | `100 + ceil(524288/32)` | `16484 cycles` |
| 256 KiB | LIVE25 | `65536 B` | `100 + ceil(131072/32)` | `4196 cycles` |
| 256 KiB | CONTROL | `0 B` | `100 + 0` | `100 cycles` |
| 512 KiB | FULL | `524288 B` | `100 + ceil(1048576/32)` | `32868 cycles` |
| 512 KiB | LIVE25 | `131072 B` | `100 + ceil(262144/32)` | `8292 cycles` |
| 512 KiB | CONTROL | `0 B` | `100 + 0` | `100 cycles` |

For FULL 256 KiB, two-way traffic is `524288 B`. Bandwidth sensitivity is:

| State bandwidth | Exact derivation | Ledger |
|---:|---|---:|
| `16 B/cycle` | `100 + ceil(524288/16)` | `32868 cycles` |
| `32 B/cycle` | `100 + ceil(524288/32)` | `16484 cycles` |
| `64 B/cycle` | `100 + ceil(524288/64)` | `8292 cycles` |

The apparent inverse scaling is equation behavior. A physical design with wider context-store bandwidth may require more ports, wires, buffering, arbitration, area, energy, or reduced frequency. None of those effects is modeled. The sweep also omits software reload, context-store allocation and queueing, backing-store traffic, setup, dirty scans, synchronization latency, contention, ECC, and capacity pressure.

The exact retained output can be reproduced by inspecting canonical v7's `test-context-sweep.log`, whose twelve rows are gated by the release validator. The canonical run itself is immutable and has both an inner 45-entry retained manifest and a four-entry outer bundle manifest.

## 18.9 Architecture alternatives and trade-offs

| Alternative | Correctness regime | Traffic/storage | Latency interpretation | Control/compiler burden | Main risk | Verification burden |
|---|---|---|---|---|---|---|
| FULL | all primary W/A/O bytes plus explicit handling of omitted state suffice at a legal boundary | highest modeled copied bytes and backing-store capacity | largest Tusim transfer term, but drain/contention omitted | lower live-set burden | shared queue/DMA/global state still defeats transparent isolation | prove every non-SRAM boundary separately |
| LIVE-prefix | exact per-region prefixes at a legal boundary; tails dead or reloaded | reduced copied bytes | smaller transfer term only | trustworthy extent producer and reload plan required | stale tails or wrong prefix corrupt continuation | liveness-to-prefix proof, tail poisoning, reload tests |
| CONTROL-only | software reconstructs every SRAM value before use | zero retained SRAM in this ledger | fixed-only model row; actual reload omitted | highest runtime/software burden | smallest row mistaken for fastest or lowest-energy resume | reload traffic, dependencies, contention, and resume testing |
| Round-robin | deterministic slot traversal is sufficient | no retention change | no service-time model | simple selector | fairness inferred from traversal | repeated readiness/block trajectories |
| Priority | strict positive-priority selection desired | no retention change | no calibrated QoS | priority and aging policy needed | priority zero excluded; low-slot ties repeat | starvation, tie, and wrap trajectories |
| Wider state bandwidth | a physical context store can sustain it | same bytes, fewer analytical transfer cycles | lowers only the equation's transfer term | more implementation complexity | area/power/frequency/contention omitted | implementation evidence and calibration |

FULL gives the strongest modeled primary-SRAM byte retention, not complete tenant isolation. LIVE-prefix can be attractive when an authoritative producer proves that one prefix per region is sufficient; no such bridge exists here. CONTROL-only can be correct when software reload is mandatory and verified, but zero saved bytes does not mean zero traffic, latency, or energy. Priority versus round-robin changes selection only, not state completeness.

A recommendation must name the regime. For a tiny control workload whose SRAM is cheaply reconstructed, CONTROL may avoid context-store capacity. For a large resident tensor with expensive reload, FULL may reduce software complexity despite high retained traffic. LIVE can dominate modeled bytes when liveness is naturally prefix-shaped, but an interval or dirty-block representation may be better when live state is sparse. Choosing among them needs compiler/runtime effects, verification cost, physical context-store capacity, area, power, energy, and contention—not one cycle column.

## 18.10 Verification evidence

Corrected canonical v7 is `experiments/runs/ch18-context/20260806-ch18-canonical-v7`. Its `input_commit` binds the final predraft input set against source pin `e918c80b6fce833cd1fcae97730fa841c2176f25`.

The evidence ladder is:

1. exact detached, clean Tusim pin and unchanged ignored-file inventory;
2. 39 implementation/header/test/config/document hashes;
3. 171 structural predicates and 210 source checks;
4. exactly 19 public APIs and zero external non-test callers;
5. static linkage for focused, mutation, sweep, O0/O2, and sanitizer binaries;
6. focused suite `15/15`;
7. real assertion mutation `14/15` with nonzero status;
8. all 12 sweep rows;
9. 45 lifecycle/ownership/accounting transition labels plus field-complete companion surfaces;
10. exact first/second/third 64-byte allocation-failure ordinals;
11. probe summary `CH18_PROBE SUMMARY failures=0`;
12. byte-identical output when only the probe translation unit is changed from O0 to O2—the library is built once;
13. bounded, leak-clean ASan/UBSan probe execution;
14. predraft validator mutation with a real `assert(False)` rejected under normal Python and `python -O`;
15. a unique 45-entry retained manifest and exact 51-file run inventory; and
16. a unique four-entry outer manifest binding `sha256-retained.txt`, `manifest-check.log`, `finalization.log`, and `predraft-validation.log`.

The 45 transition labels cover null APIs; invalid creation; cloning and exhaustion; free in ACTIVE/READY/BLOCKED/COMPLETED/IDLE states; reuse; save and direct restore; restore while another owner is active; self, invalid, IDLE, BLOCKED, and already-ACTIVE switch targets; immediate request-switch; round-robin; repeated priority ties; priority zero; inclusive thresholds and wrap; notifications without owner; block/unblock states; first/second/third copy failures; destructive re-save; all scopes; zero bandwidth; core/runtime retention; cycle underflow; queue, DMA, plugin, precision, and global boundaries; and dead controls.

Companion records cover every W/A/O byte, aggregate metadata, instantiated per-bank bandwidth member, runtime-config field, queue scalar/command/dependency/signal state, embedded and global DMA summary, override digest, pointer relationships, five legacy ledgers, core clock, selected plugin public counters, rounding/subnormal modes, and outer-core identity/ICC ownership. Opaque plugin `impl_data`, PRNG internals, error mode, caller-owned DRAM, and raw addresses are structurally classified rather than unsafely dereferenced.

Counts are not semantic truth by themselves. Canonical v5 passed its encoded gates while an under-scoped predicate produced the false `total_size` narrative; canonical v6 later carried an overbroad “schedulable” adjective for COMPLETED. Hostile review corrected both interpretations, and canonical v7 repeated the audit with the final predraft claims. Manifests establish integrity and reproducibility; meaningful predicates and adversarial interpretation establish claim quality.

The evidence does **not** prove production integration, safe-point legality, arbitrary preemption, legal asynchronous queue drainage, complete machine isolation, fairness, calibrated QoS, physical context-store implementation, RTL equivalence, silicon agreement, area, energy, or end-to-end resume latency.

## Fidelity box

> **Executable:** context-object linkage, focused 15/15 behavior, bounded transitions, copy scopes, exact retained bytes, and manager-ledger arithmetic at pin `e918c80b6fce833cd1fcae97730fa841c2176f25`.
>
> **Functional model:** selected descriptor lifecycle and selected state-copy behavior. It is not a concurrency-safe or complete-machine snapshot.
>
> **Analytical model / estimated and uncalibrated:** `total_cycles_stolen` and all sweep cycle rows. They are deterministic model ledger values, not measured latency.
>
> **Not integrated:** zero external non-test callers and no shipped JSON/YAML/parser/runtime construction path. No automatic safe-point or compiler-live-prefix producer exists.
>
> **Qualified execution:** the queue sentinel is fabricated but memory-safe copying evidence, not legal asynchronous drainage. O0/O2 equality applies only to the probe translation unit; the archive was built once with one compiler. Manager `calloc` failure and unsupported restore-corruption paths remain blocked.
>
> **State boundary:** W/A/O `total_size` is saved and restored; saved per-bank `bw_banks` state is not retained. Queue contents, operative `g_tu_dma`, plugin internals, precision globals, outer core/ICC, and caller-owned DRAM remain shared or external. Double-buffer ownership loss is imported from Chapter 16 rather than executed in the bounded Chapter 18 sanitizer path.
>
> **Unsafe conclusions:** autonomous or arbitrary-boundary preemption, deferred safe-point switching, complete tenant isolation, queue/global-DMA drainage, per-context plugin or precision isolation, fair scheduling, calibrated switch latency, `total_cycles_stolen` as elapsed time, FULL as full machine state, or CONTROL as universally fastest or lowest-energy.

## Common failure modes

1. **Boundary and integration errors.** A C call is not a safe point; archive linkage is not runtime integration; broad “thread-safe” prose is not a lock or concurrency proof.
2. **Scalar-only ownership checks.** `active_ctx_id` and `active_count` can each look plausible while descriptor states show two owners, no owner, or corrupted allocation count.
3. **Unsafe primitive composition.** Direct restore can create two ACTIVE descriptors; rejected switches mutate outgoing state; self-switch is accepted and fully charged.
4. **Missing successor logic.** Freeing or blocking ACTIVE can leave no owner, while freeing IDLE can corrupt allocated count and slot reuse need not repair ownership.
5. **Blank-context assumptions.** Allocation clones current shared bytes, selected counters, configuration, and pointers; it does not construct an independent empty image.
6. **Unchecked accounting.** A zero first baseline charges old history; caller-fed notification counters can update without an owner and wrap.
7. **Fairness inference.** Round-robin traversal is not a service guarantee; strict priority repeats low-slot ties, excludes priority zero, and has no aging.
8. **Calling LIVE compiler liveness or tenant isolation.** LIVE is one caller-supplied prefix per region; stale tails require a legal boundary plus dead-tail/reload and shared-state contracts.
9. **Reading CONTROL's zero bytes as zero resume work.** Software reload, backing-store traffic, dependencies, and contention are omitted.
10. **Misstating SRAM retention.** `total_size` and aggregate metadata are retained; saved `bw_banks` is not. Canonical v7 is authoritative after correcting the v5 defect and v6 lifecycle wording.
11. **Treating queue synchronization as machine drainage.** The live queue is not reconstructed; asynchronous synchronization may loop; operative global DMA is separate.
12. **Treating copied pointers or structs as isolated objects.** Embedded DMA differs from `g_tu_dma`; plugin registry objects and `impl_data` remain shared.
13. **Assuming precision modes are descriptor state.** Rounding, PRNG, subnormal, and error controls continue globally.
14. **Calling FULL a full machine snapshot.** Outer core/ICC, DRAM, queue, global DMA, plugins, modes, and double-buffer ownership remain outside it.
15. **Mixing clock domains.** `total_cycles_stolen` advances no Chapter 17 producer; zero bandwidth suppresses its transfer term rather than modeling infinity.
16. **Assuming re-save is transactional.** Old retained arrays are freed before replacement succeeds, so allocation failure can destroy a valid checkpoint.
17. **Overreading sanitizer scope.** Leak-clean bounded execution does not cover the deliberately unexecuted double-buffer ownership-loss trajectory.
18. **Treating manifests as semantic proof.** They prove exact bytes and closure, not that every predicate or interpretation is correct.

## Summary

A defensible context switch starts with a legal boundary, not a function call. It then requires a sufficient retained set, an invariant-preserving ownership transition, and explicit treatment of shared and in-flight state. Tusim's context manager supplies selected standalone executable mechanisms but not the whole contract.

FULL, LIVE-prefix, and CONTROL-only differ in retained primary W/A/O bytes. FULL copies complete capacities. LIVE copies caller-supplied prefixes and leaves stale tails. CONTROL copies no SRAM and relies on reconstruction. Their exact retained bytes feed a manager-local estimated equation, not calibrated latency. For a normal equal-size switch, the specialization is `F + ceil(2B/W)`; the general restore equation uses pending outgoing plus incoming bytes, and zero bandwidth suppresses transfer cost.

Ownership is the tuple of active ID, every descriptor state, and allocated count. Direct restore, rejected switches, free, block, IDLE free, and reuse expose states with two owners, no owner, stale identity, or corrupted count. Allocation clones shared state. Notifications and cycle accounting are caller-fed or unchecked call-history ledgers. Scheduling is deterministic but not fair.

The retained-state boundary is intentionally uneven. Crucially, region `total_size` is saved and restored while saved per-bank `bw_banks` state is not retained. Queue contents, operative global DMA, plugin internals, precision controls, outer-core/ICC, and caller-owned DRAM remain shared or external. Double-buffer role and allocation ownership can be lost.

Canonical v7 establishes these pin-specific claims with 39 hashes, 171 predicates, 210 checks, 19 APIs, focused 15/15, mutation 14/15, 12 sweep rows, 45 transition labels, `failures=0`, bounded sanitizer execution, optimizer-safe validation, and two manifest layers. It does not establish arbitrary preemption, integration, complete isolation, fairness, calibration, or physical context-store cost.

## Review questions

1. Why are a legal preemption boundary and a successful switch call not equivalent?
2. What four contracts are required for defensible continuation?
3. Why must ownership use `(active_ctx_id, all descriptor states, active_count)`?
4. How can direct restore create two ACTIVE descriptors?
5. Why is a rejected `tu_ctx_switch()` not failure-atomic?
6. Why is allocation described as cloning rather than construction?
7. What distinguishes FULL, LIVE-prefix, and CONTROL-only?
8. Why does the LIVE stale-tail example restore W as `[1.0, 20.0]`?
9. Derive `12 B`, `10 cycles/switch`, and `20` cumulative cycles in the LIVE fixture.
10. Derive the 256-KiB FULL, LIVE25, and CONTROL rows.
11. Why can restoring the same 192-byte target cost `13` or `19` ledger cycles?
12. What does `state_bytes_per_cycle==0` do at this pin?
13. What does `tu_core_sync()` actually synchronize?
14. Distinguish embedded `tu_state_t.dma` from operative `g_tu_dma`.
15. Which precision states remain process-global?
16. Why is READY priority zero unschedulable?
17. Why do equal positive priorities repeatedly choose the lowest slot?
18. How can notification wrap make an expired slice appear fresh?
19. Why does first save charge pre-allocation `estimated_cycles`?
20. Which SRAM fields are restored, and which per-bank state is not?
21. Why was v5's `total_size` omission claim false despite passing gates?
22. What does canonical v7 establish, and which conclusions remain unsafe?

## Review-question answer key

1. The call runs immediately but has no producer proving dependencies, queue work, DMA, or transient effects are at a safe boundary.
2. A legal boundary, sufficient retained or reconstructable state, a valid ownership transition, and explicit handling of shared and in-flight state. Cost characterization is separate from these correctness obligations.
3. Any one field can be stale or corrupted independently; only the tuple exposes two owners, no owner, wrong identity, or wrong allocated count.
4. Restore marks a READY target ACTIVE and changes the ID without demoting an existing ACTIVE descriptor.
5. Switch saves and demotes the outgoing context before restore validates the target, so every listed rejection mutates outgoing state and leaves pending bytes. Invalid, IDLE, and BLOCKED targets leave no ACTIVE owner; an already-ACTIVE target leaves one ACTIVE descriptor whose identity conflicts with `active_ctx_id`.
6. Every allocation snapshots the current shared core image, including bytes, selected ledgers, configuration, and pointers.
7. FULL copies all primary W/A/O bytes, LIVE copies declared prefixes, and CONTROL copies none; each requires different external correctness work.
8. The first four-byte float comes from context 0's prefix; the second float remains from context 1's intervening tail.
9. `B=4+4+4=12 B`; `7+ceil(24/8)=10`; two accepted switches total `20`.
10. With `F=100`, `W=32`, and `B=262144/65536/0`, use `100+ceil(2B/32)` to obtain `16484`, `4196`, and `100`.
11. Incoming-only history moves `192 B`, giving `7+ceil(192/32)=13`; a matching outgoing-plus-incoming history moves `384 B`, giving `19`.
12. It suppresses transfer cycles and charges fixed cost only; it is not rejected or modeled as infinity.
13. It swaps selected state into `g_tu` and calls command-queue synchronization only; it does not flush operative global DMA.
14. One is copied inside selected state; ordinary descriptor APIs use a separate process-global engine whose pending work survives switching.
15. Rounding mode, stochastic PRNG state, subnormal mode, and error mode.
16. Selection starts with `best_prio=0` and requires strict `priority>best_prio`.
17. A strict greater-than comparison never replaces the first equal maximum encountered.
18. Unsigned maximum plus one becomes zero, so inclusive threshold queries can return false again.
19. Initial `last_switch_cycle` is zero and no allocation-time baseline excludes older core history.
20. `total_size`, geometry/capacity, aggregate counters, policy scalars, region cycle, and name are restored; saved per-bank `bw_banks` entries are not.
21. The predicate inspected only a helper and missed explicit `total_size` assignments in the enclosing save function and their restore sites.
22. v7 establishes bounded pin-specific standalone transitions, copy behavior, and analytical arithmetic—not integration, safe-point legality, fairness, complete isolation, or calibrated latency.

## Design exercises

1. **Transactional switch.** Redesign `tu_ctx_switch()` so invalid, IDLE, BLOCKED, and already-ACTIVE targets cannot mutate the outgoing owner. Specify prevalidation, staged state, commit order, rollback, and mutation tests.
2. **Ownership checker.** Define a runtime invariant checker over ACTIVE count, `active_ctx_id`, allocated count, and pending bytes. Decide whether zero ACTIVE is legal during an explicit suspended state.
3. **LIVE-set interface.** Compare prefixes, interval lists, dirty bitmaps, compiler-generated reload plans, and copy-on-write pages by storage, traffic, runtime complexity, and proof burden.
4. **Structured cost result.** Replace one cumulative scalar with fixed, outgoing, incoming, reload, drain, queueing, contention, and ECC components. Give every component a clock and fidelity label.
5. **Global-state isolation.** Design ownership for queue, global DMA, plugin objects, rounding, PRNG, subnormal, and error modes. Compare deep-copy, reference counting, drain-before-switch, and explicitly shared contracts.
6. **Failure-atomic checkpointing.** Preserve an old snapshot if the second of three W/A/O allocations fails. Specify temporary ownership and cleanup under every ordinal.
7. **Fair scheduler.** Add aging, weighted service, or deadlines while retaining deterministic tests for equal ties, blocking, priority zero, and notification wrap. Define the fairness metric.
8. **Calibration plan.** Specify matched RTL or hardware experiments for context-store traffic and resume latency, including workload, safe point, clock, raw counters, error metrics, and omitted effects.
9. **Audit the audit.** Mutate source so W/A/O `total_size` save truly disappears. Design structural and executable probes that reject the mutation without relying on helper-local text.
10. **Chapter 19 bridge.** Define what compile-time liveness must prove before it can populate the three LIVE-prefix controls. Include layout, dynamic-shape, aliasing, and reload obligations.

## Exercise answer sketches

1. Validate target and current-owner invariants first, stage outgoing data without destroying the old snapshot, stage incoming restoration, and commit descriptor states plus `active_ctx_id` as one transition. Mutations should force every validation and allocation failure.
2. Recompute allocated and ACTIVE counts from descriptors, require the ID to name the unique ACTIVE descriptor when executing, and separately model an explicit suspended state if zero ACTIVE is allowed. Pending traffic must correspond to a staged handoff.
3. Prefixes minimize metadata but over-copy non-prefix live sets. Intervals improve precision with metadata cost. Dirty maps capture writes rather than semantic liveness. Compiler reload plans can omit storage but carry the largest cross-layer proof obligation.
4. Return a record rather than one scalar. Fixed and transfer terms may share a model clock only by explicit contract; reload and contention need their own producers until integrated. Never sum incompatible domains.
5. Queue and DMA can be drained or serialized; plugin objects need per-context instances or protected shared ownership; global modes need capture/restore or caller serialization. Shallow pointer copying is insufficient.
6. Allocate and fill temporary W/A/O images first. On any failure, free temporaries and retain the old descriptor unchanged. Swap ownership only after all three copies succeed.
7. Define bounded wait or weighted service over eligible intervals, add monotonic counters with overflow policy, and test long repeated trajectories rather than one selection. State how BLOCKED time affects the denominator.
8. Match the same boundary, bytes, context-store organization, clock, and workload in model and reference. Retain raw save/drain/restore events and report absolute and relative error rather than calibrating one aggregate number.
9. Gate explicit save and restore assignments for all three regions, then perturb live `total_size`, switch away and back, and require exact restoration. Run the source mutation and validator in normal and optimized modes.
10. The compiler must map live values to concrete W/A/O prefixes, prove every omitted tail dead or reloaded, preserve alias/layout assumptions, handle dynamic extents, and emit a runtime-visible safe-point plus reload contract.

## Primary references

- **Pinned Tusim implementation and public interface:** canonical v7 retains hash-locked copies and audit evidence for `tu_cmodel/infra/tu_context.[ch]` at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`; see the [canonical transcript](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/transcript.log), [source audit](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/source-audit.log), and [inner manifest](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/sha256-retained.txt).
- **Executable transition evidence:** [canonical probe](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/probe.log), [focused context suite](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/test-context.log), [focused mutation](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/test-context-mutation.log), and [context sweep](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/test-context-sweep.log).
- **Closure evidence:** [outer bundle manifest](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/bundle-sha256.txt), [finalization binding](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/finalization.log), and [predraft validation](../../experiments/runs/ch18-context/20260806-ch18-canonical-v7/predraft-validation.log).
- [BAN02] Scratchpad memory: primary scratchpad organization context and conservative claim scope in the verified [foundations ledger](../../references/foundations.md#ban02-scratchpad-memory).
- [TOM67] Dependency-driven scheduling: primary scheduling vocabulary and conservative claim scope in the verified [foundations ledger](../../references/foundations.md#tom67-dependency-driven-scheduling).
- [OCL311] OpenCL command-queue contract: official primary command/event/synchronization vocabulary in the verified [foundations ledger](../../references/foundations.md#ocl311-opencl-command-queue-contract).
