# Chapter 16 — Double Buffering and Legal Overlap

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

> **Chapter contract.** This chapter separates five adjacent surfaces: the standalone SRAM double-buffer state machine, descriptor DMA, the standalone pipeline controller, the scheduler's unrelated “double-buffered” ordering test, and historical analytical overlap reports. It does not combine their clocks or counters into an end-to-end accelerator timeline. A swap is legal only when a named producer has completed the intended bytes into the physical buffer that will become active, every consumer dependency authorizes visibility, and lifecycle state will preserve ownership. The pinned implementation does not enforce that complete protocol.

## Learning objectives

After this chapter, you should be able to:

1. explain why double buffering is an ownership protocol, not merely two allocations;
2. distinguish active and shadow **roles** from the fixed primary and `shadow_data` **physical allocations**;
3. state the preconditions for a legal swap and explain why `shadow_dirty` is insufficient;
4. derive steady-state overlap, startup, and drain costs without double-counting a compute window;
5. trace generic SRAM accesses and descriptor DMA to the physical allocation they actually modify;
6. reproduce the pinned controller's stale-data bridge and explain its post-swap dirty attribution;
7. keep descriptor completion, descriptor service estimate, DMA time, controller time, SRAM time, and manually recorded cycles separate;
8. explain why the controller's reported speedup can be positive or infinite when no overlap was credited;
9. account for the physical-capacity, port, control, context, and verification costs of ping-pong storage;
10. choose among single, equal ping-pong, bank-partitioned, ring/triple, and event-backed alternatives by regime rather than slogan; and
11. identify which claims are executable, analytical, historical, estimated, or rejected at the pinned edition.

## Prerequisite graph

```text
Chapter 9: SRAM storage, active raw pointers, shared bank meters
                              │
Chapter 10: descriptor bytes, completion, ticks, ownership
                              │
Chapter 14: standalone pipeline controller and heterogeneous metrics
                              │
Chapter 15: producer-first cycle and integration discipline
                              ▼
       two allocations -> ownership -> producer completion -> legal swap
               │               │                 │               │
               └───────────────┴─────────────────┴───────────────┘
                                      │
                                      ▼
                    defensible overlap and capacity claim
```

Chapter 9 established that storage capacity, byte effects, bank service, and operation reachability are separate contracts. Chapter 10 showed that descriptor selection can copy bytes long before channel retirement, and that a completion field is not a general dependency event. Chapter 14 introduced the pipeline controller but did not teach its double-buffer ownership behavior. Chapter 15 reinforced the rule that nearby models and cycle fields do not become one timeline merely because their names sound compatible.

This chapter owns the missing reader decision: **when is a buffer-role exchange legal, what does it cost, and which Tusim surface proves each precondition?** It does not reteach descriptor geometry, operator metrics, DRAM service, or general scheduling.

## Opening architecture question: when is a swap safe?

Assume compute is consuming tile *n* from an active SRAM buffer while DMA is intended to preload tile *n+1* into a shadow buffer. The DMA descriptor becomes `completed`, and the controller swaps the roles. Has latency been hidden correctly?

Only if all of the following are true:

1. **Target selection:** the producer wrote the physical allocation currently playing the shadow role.
2. **Extent and contents:** every byte needed by tile *n+1* was produced, not merely some byte or a counter increment.
3. **Completion semantics:** the completion observation means those writes are finished for the relevant consumer.
4. **Dependency:** compute on tile *n* no longer needs the allocation that will become shadow.
5. **Swap authorization:** exactly one owner performs the role transition, in the intended order.
6. **Visibility:** subsequent compute resolves its addresses through the newly active allocation.
7. **Clock relationship:** any latency-hiding claim uses a defined schedule connecting producer and consumer events.
8. **Lifecycle:** reset, disable, destroy, or context switching cannot silently discard or misidentify live state.

The pinned standalone API enforces none of these as a complete protocol. It can allocate, return pointers, toggle an index, and maintain caller-supplied ledgers. That is useful machinery, but machinery is not legality.

The central distinction is:

```text
ability to swap != permission to swap
notification != validity
descriptor completed != common-clock readiness
two arrays != two independent physical ports
reported speedup != demonstrated overlap
```

## 16.1 Theory: latency hiding is a scheduled dependency problem

Let `D` be the producer time for the next tile and `C` the consumer compute time for the current tile, measured in one explicitly defined clock. Sequential execution of one repeated tile costs `D + C`. In an ideal steady state with independent resources and correct ping-pong ownership, the repeated interval can approach:

```text
T_steady = max(D, C)
ideal hidden time per steady tile = min(D, C).
```

This equation does not erase startup and drain. For two identical tiles with load overlap only, a correct ideal timeline is:

```text
initial load tile 0                 D
compute tile 0 / load tile 1       max(C, D)
final compute tile 1               C
------------------------------------
T_two_tiles = D + max(C, D) + C.
```

Writing `2 × max(D,C)` would incorrectly hide the first fill or last drain. For `T` tiles under the same simplified assumptions:

```text
T_total = D + (T − 1)·max(D, C) + C.
```

If stores are also overlapped, the resource graph matters. A preload and store sharing one DMA channel cannot each claim the full compute window. With one sequential channel and compute window `C`, a conservative allocation is:

```text
preload_hidden = min(C, P)
store_hidden   = min(C − preload_hidden, S)
```

where `P` and `S` are preload and store service. The expression `min(C,P) + min(C,S)` can exceed `C` and double-count time. Simultaneous full preload and store overlap requires explicit independent channels, ports, arbitration, and a verified schedule.

These formulas are **Analytical model** statements. They become architecture claims only after the model names resource independence, startup/drain, queues, completion events, and the mapping from model time to execution. Decoupled access/execute work motivates latency tolerance through separately progressing streams, but also makes queue capacity and synchronization first-class obligations ([SMI84](../../references/foundations.md#smi84-decoupled-accessexecute)). Timeloop and MAESTRO similarly demonstrate why workload, mapping, storage, and resource assumptions must be explicit; neither validates Tusim's controller ([PAR19](../../references/foundations.md#par19-timeloop), [KWO19](../../references/foundations.md#kwo19-maestro)).

### Roles, allocations, and epochs

“Ping” and “pong” are roles that alternate. Tusim has two physical allocations:

- the primary allocation, `r->banks.data`;
- the added allocation, `r->db->shadow_data`.

It also has two logical roles:

- **active:** the allocation generic SRAM APIs currently expose to consumers;
- **shadow:** the opposite allocation, intended for the next producer.

At `active_idx=0`, the primary allocation is active and the `shadow_data` allocation holds the shadow role. At `active_idx=1`, those roles reverse. Therefore “shadow buffer” is ambiguous unless the text says **shadow role** or **`shadow_data` allocation**. Explicitly managed scratchpads make this placement and ownership obligation architectural rather than incidental ([BAN02](../../references/foundations.md#ban02-scratchpad-memory)).

A robust design usually adds an epoch or generation to each role. A Boolean dirty bit can say “someone reported a write since a transition.” It cannot distinguish tile 41 from tile 42, partial from complete data, duplicate notification from first notification, or a completion event for one allocation from an event for the other. Legal ownership needs identity, not just activity.

## 16.2 Source map: five surfaces that must remain separate

| Surface | Pinned source/evidence | What it establishes | What it does not establish |
|---|---|---|---|
| standalone double buffer | `tu_cmodel/memory/double_buffer.{h,c}`, `tu_sram.{h,c}` | allocation, role pointers, swap, notification ledgers, disable/destroy behavior | integrated producer/consumer protocol or independent ports |
| descriptor DMA | `tu_cmodel/dma_descriptor.{h,c}` | functional byte destination, executor completion, independent tick state | intrinsic shadow targeting or common controller clock |
| pipeline controller | `tu_cmodel/compute/pipeline_controller.{h,c}` | slots, stages, descriptor calls, swaps, analytical ledgers | ordinary-operation reachability, command execution, valid byte bridge |
| scheduler test | scheduler source and its “double-buffered tile pipeline” test | constructs disjoint-address tile sequences and checks valid scheduling plus instruction presence | relative cross-tile ordering, physical overlap, or calls to either standalone API family |
| historical reports | `docs/TU_DOUBLE_BUFFER.md`, `docs/software-pipelining.md`, exploration reports | design intent and ideal equations | pinned integration, calibration, or generally attainable speedup |

Both `double_buffer.o` and `pipeline_controller.o` are members of the static archive. The pipeline controller is the only non-test `tu_cmodel` source caller that combines double-buffer mutation and descriptor APIs. No non-test library caller invokes the pipeline controller itself. Thus it is a **library-present standalone bridge candidate**, not an ordinary workload path.

This chapter supersedes Chapter 14's **evidentiary interpretation**, not its raw observations. Chapter 14 correctly reported the controller's source-defined ledger values and the apparent 11/11 output of its standalone suite. Chapter 16's legality audit establishes that the unmodified suite's four-channel request exceeds three-entry DMA storage, so that result is not memory-safe integration evidence; it also establishes that `cycles_saved` and `speedup` can be positive or infinite without legal byte overlap. Sections 16.6–16.8 audit the legality of that earlier ledger rather than reteaching it.

Test provenance is equally specific. `tests/test_double_buffer.c` passes 10/10 when the chapter runner compiles it directly, but `test-double` has no Makefile recipe and is absent from aggregate `make test`; its name appears only in `.PHONY`/clean bookkeeping. The source assertion mutation passes only 9/10 and exits nonzero, proving the focused gate is live. `test-pipeline` has a Makefile rule and aggregate membership, but its setup requests four DMA channels while fixed descriptor-engine storage has three. The canonical Chapter 16 audit therefore does not execute that unsafe suite as a green integration certificate; it uses a bounded one-channel probe for the chapter's exact claims. A bounded probe does not replace the omitted suite.

## 16.3 Standalone implementation: two byte arrays, one ownership index

`tu_sram_enable_double_buffer()` checks that the region exists and has nonzero `total_size`, allocates zeroed state plus one zeroed equal-size data array, sets `active_idx=0`, and attaches the state through `r->db`. Calling it again while `r->db && enabled` returns success without reallocating. The source comment requires enabling after `tu_sram_init()`, but the implementation does not verify that the primary allocation was initialized. Idempotence is therefore qualified by a caller-enforced construction order.

The capacity equation is simple:

```text
logical usable capacity per role = S bytes
total physical data capacity     = 2S bytes
```

A 16 KiB active role plus equal shadow consumes 32 KiB of data allocation. It does not provide a 32 KiB tile, and it does not create capacity for free. If W, A, and O all require ping-pong storage, their duplicate allocations must all be counted.

Pointer selection is index-driven:

```text
active_idx = 0: active = primary, shadow role = shadow_data
active_idx = 1: active = shadow_data, shadow role = primary.
```

Generic `tu_sram_read`, `tu_sram_write`, bulk access, and `tu_sram_raw_ptr()` select the current active pointer. This is the byte-visibility mechanism: after a legal swap, ordinary active-aware accesses see the other allocation without copying data.

### Worked example 1: clean swap and notification without bytes

`tu_sram_swap_buffers()` performs only three state updates:

```text
active_idx = 1 - active_idx
swap_count++
shadow_dirty = false
```

It does not check dirty state, byte count, tile identity, descriptor outcome, compute dependency, or ownership. An initial clean swap is accepted and exposes the zeroed added allocation. In the canonical probe, primary begins as `0x11`, shadow as `0x00`, and the first clean swap produces:

```text
DB_CLEAN_SWAP count=1 active_idx=1 active=00 shadow=11 dirty=0
```

This is **Executable** negative evidence: the API permits an illegal protocol transition. It does not mean every use of double buffering is illegal; it means legality belongs to the caller.

### Dirty is a notification bit, not a validity protocol

`tu_sram_get_shadow_ptr()` merely returns a pointer. Contrary to the header's “writing ... sets” wording, neither pointer retrieval nor a raw write changes `shadow_dirty`. Only `tu_sram_notify_shadow_write(r, bytes, cycles)` marks dirty and additively increments `dma_to_shadow_bytes` and `dma_to_shadow_cycles`.

The notification function does not inspect memory. It accepts a byte count larger than capacity and any caller-supplied cycle value. The probe reports:

```text
DB_NOTIFY_ONLY shadow_before=00 shadow_after=00 dirty=1 bytes=1016 dma_cycles=82
```

No byte changed, yet dirty became true and the ledgers advanced. Therefore the safe label is **manual notification/accounting state**. It is not a valid bit, freshness proof, extent check, descriptor binding, or completion token. `tu_sram_record_overlapped_cycles()` is another additive caller ledger; the standalone module derives no overlap from clocks or bytes.

A legal replacement would minimally associate `(buffer identity, tile generation, expected extent, produced extent, producer status)` and permit swap only after the generation is complete and the prior active generation has no remaining readers.

### Byte independence does not imply port independence

The two allocations hold distinct bytes, but bank meters and counters live once in `r->banks`. Reads/writes, available words, refill cycle, stalls, and aggregate counters follow whichever allocation is active. The canonical probe consumes bank 0 in one role, swaps, and sees the same exhausted meter in the other:

```text
DB_SHARED_METER first=0 second=2 active_value=00000000 bank0_words=0
```

The first write receives no penalty, and the corresponding access after the swap receives the two-cycle exhausted-bank penalty. Double allocation therefore does not model two independently serviced bank arrays or simultaneous DMA/compute ports. An ideal overlap equation that assumes independent access resources is a separate architecture alternative, not a conclusion from this data structure.

## 16.4 Lifecycle: disable can preserve bytes; context restore cannot preserve ownership

Disabling has deliberate role-aware behavior. If primary is active, the added allocation is discarded. If `shadow_data` is active (`active_idx=1`), disable copies it back into primary before freeing double-buffer state. The probe makes `0x44` active and confirms:

```text
DB_DISABLE enabled=0 primary=44 db_null=1
```

Direct SRAM destruction frees both data allocations and double-buffer state. These paths establish a usable standalone lifecycle for owned regions.

Live reinitialization is not a reset path. `tu_sram_init_bw()` begins by zeroing the region object, then allocates replacement primary and bank-meter storage. It does not first release an existing primary allocation, bank meter, shadow allocation, or DB state. The v4 lifecycle probe captures the displaced pointers, confirms that ownership was lost, and salvages them explicitly:

```text
SRAM_REINIT primary_replaced=1 meter_replaced=1 db_lost=1 new_size=32
```

The contractual rule is therefore **destroy before init**. Calling init on a live region leaks ownership; it does not preserve, drain, or invalidate generations safely.

Reset and context behavior are different. `tu_pipeline_reset()` calls destroy, saves depth/config, and does not reinitialize or reallocate slots. The result is uninitialized controller state with a null slot pointer. A later submission auto-initializes depth one, not the saved depth. The probe records:

```text
PIPE_RESET initialized=0 depth=2 slots_null=1 free_slots=1
PIPE_AFTER_RESET_SUBMIT tid=0 depth=1 initialized=1 stored_cmd=123
```

The first line's `free_slots=1` is a query fallback, not an allocated free slot. “Reset” is destruction followed by deferred depth-one auto-initialization.

Context save/restore is worse for a live double-buffer owner. Save retains scoped primary bytes but not the added allocation, active index, dirty state, swaps, or manual ledgers. Restore overwrites a live region's `db` pointer with `NULL` without first freeing it. That leaks the old state and exposes restored primary bytes regardless of which role had been active. Context switching is therefore **rejected** as an integration bridge at this pin. A correct context contract would either prohibit switching with live ownership, serialize both allocations and generations, or transfer explicit ownership while reclaiming displaced state.

```text
CTX_RESTORE ids=0,1 save_rc=0 restore_rc=0 db_lost=1 primary_live=1
```

## 16.5 Descriptor DMA targets the active region by default

For an ordinary host-to-TU descriptor, execution resolves the destination in this order:

```text
if dst_region != NULL:
    destination = tu_sram_raw_ptr(dst_region) + dst_base
else:
    destination = dst_host
```

Because `tu_sram_raw_ptr()` follows the current active role, a descriptor carrying a non-null region writes active bytes. `dst_host` is consulted only when `dst_region` is null. Descriptor DMA therefore has no intrinsic “write this region's shadow role” semantic.

The timing fields also remain Chapter 10's separate contract. On a successful selected descriptor, the C executor copies bytes, sets `completed=true`, and calculates a future `cycles_completed` estimate. `tu_dma_tick()` advances `g_tu_dma.current_cycle`; channel retirement can occur later. A controller that observes `completed` observes executor outcome, not necessarily elapsed service in the controller's clock. The descriptor's service estimate, DMA engine cycle, and controller cycle cannot be substituted for one another.

The general range checks need stronger qualification. SRAM `bounds_check()` reports an error but returns `void`; generic SRAM read/write continues into bank lookup and `memcpy` even for an ordinary non-wrapping out-of-range access. Descriptor execution returns on detected linear host↔TU failures, but TU-to-TU copies have no equivalent bounds gate, scatter indices are not individually bounded, and `base + total_bytes` does not prove the final stride-derived address fits. Those sums, like SRAM's `addr + size`, are also 32-bit additions performed before comparison and can suffer wraparound. The bounded Chapter 16 probe covers only small linear host-to-TU transfers. It establishes no arbitrary-input safety. A production contract should use path-specific, subtraction-form checks such as `size <= limit && addr <= limit - size`, validate every stride/scatter-derived address with widened types, and make failure prevent the copy.

This distinction matters because a correct bridge needs either:

- a descriptor destination that explicitly names the shadow physical allocation and keeps it stable through execution; or
- a region API whose destination role is encoded and resolved at a controlled event, with generation checks.

Setting two conflicting descriptor fields and hoping one redirects the other is not a protocol.

## 16.6 Worked example 2: the controller makes stale data active

The standalone pipeline controller attempts a bridge during tile submission. For a host-to-TU load on a double-buffered region, it obtains `shadow = tu_sram_get_shadow_ptr(buffer_region)`, then sets both:

```text
load_desc->dst_region = buffer_region
load_desc->dst_host   = shadow
```

The descriptor executor gives `dst_region` precedence. It writes through `tu_sram_raw_ptr(buffer_region)`, which is the **active** allocation. When `completed` becomes true, the controller swaps, then calls `tu_sram_notify_shadow_write()`.

The canonical bounded probe makes every allocation visible:

- active primary byte = `0x11`;
- current shadow-role byte = `0x22`;
- host source byte = `0x7a`;
- one asynchronous DMA channel;
- one 64-byte transfer, whose descriptor service timestamp becomes 53.

Before advancement:

```text
PIPE_BEFORE tid=0 stage=1 active=11 shadow=22
            dst_region=1 dst_host_shadow=1 pipe_cycle=0 dma_cycle=0
```

One `tu_pipeline_advance()` calls `tu_dma_tick()`. The DMA engine advances to cycle 1 and executes the copy. The controller's own `current_cycle` remains 0 because this API does not increment it. Descriptor execution resolves the non-null region to active primary and writes `0x7a` there. The controller then swaps. The result is:

```text
PIPE_AFTER stage=2 completed=1 desc_cycles=53
           pipe_cycle=0 dma_cycle=1
           active=22 shadow=7a swapped=1 dirty=1
```

Trace the physical allocations:

```text
before DMA:     primary(active)=11    shadow_data(shadow role)=22
DMA writes:     primary(active)=7a    shadow_data=22
controller swap: primary(shadow role)=7a    shadow_data(active)=22
notify:         marks current shadow role dirty, which is primary=7a
```

Fresh bytes landed in the old active allocation and became the new shadow. Stale `0x22` became active. The post-swap notification marks the new shadow—the allocation that happens to contain fresh bytes—but cannot repair active visibility. This is **Executable / negative integration evidence**. It directly rejects the documents' intended DMA-to-shadow story at this edition.

The defect also appears without any descriptor. At depth one, a tile with no load still begins in PRELOAD. `load_done` defaults true, so the first advance swaps an enabled region. The probe starts with active `0x55` and clean zero shadow, then reports:

```text
PIPE_DEPTH1_NOLOAD tid=0 active=00 shadow=55 swaps=1 dirty=0 stage=2
```

The controller exposed unwritten zero bytes and entered COMPUTE. Thus “first tile may skip preload” is implemented only when depth is greater than one **and** `enable_load_overlap=true`; depth one performs a no-load swap.

## 16.7 The controller models a deadline, not compute execution

Tiles carry `cmd_id`, but no controller call submits that ID to the command queue or queries command completion. COMPUTE is represented by:

```text
cycle_expected = current_cycle + compute_cycles
compute_done = current_cycle >= cycle_expected.
```

The controller's synchronization loop increments its own `current_cycle` and calls `tu_pipeline_advance()`, which independently ticks DMA. That is a caller-driven state machine with an analytical compute deadline. It does not dispatch an operator, prove the intended active bytes were consumed, or connect command dependencies to a swap.

Configuration is also only partly behavioral:

- `enable_load_overlap` and `enable_store_overlap` gate manual credits;
- `model_stalls` is read in an empty, comment-only branch and has no observable behavioral effect;
- `enable_triple_overlap` is not consumed;
- `tile_timeout_cycles` is not consumed;
- depth is clamped to 1..8;
- the configured PE `pipeline_depth` elsewhere in Tusim is a different field and concept.

Standalone double buffering itself is API-only. Shipped JSON/YAML/runtime conversion does not select regions or enable it. `tu_mem_level_config_t.double_buffered` is declared and defaults LocalSPAD true, but hierarchy construction does not consume it to call `tu_sram_enable_double_buffer()`. That field is decorative for this state machine.

The scheduler's “double-buffered tile pipeline” test is yet another surface: it constructs disjoint-address tile sequences and checks successful, valid scheduling plus instruction presence, but it does not assert the advertised relative cross-tile ordering. It invokes neither the standalone double-buffer API nor this controller. Shared terminology is not integration.

## 16.8 Worked example 3: why reported controller speedup is not overlap evidence

The controller maintains an analytical ledger, not elapsed makespan. At submission it defines descriptor load/store cycles as floor division by 32 bytes; an absent descriptor is charged one cycle in `sequential_total`. It later computes:

```text
pipelined_total = total_compute_cycles
                + (total_load_cycles - overlapped_load_cycles)
                + (total_store_cycles - overlapped_store_cycles)

speedup = sequential_total / pipelined_total.
```

Several paths make the numerator and denominator inconsistent.

### One-load case: positive speedup with zero saved cycles

The bounded bridge tile has a 64-byte load and five compute cycles:

```text
load ledger       = 64 / 32 = 2
compute           = 5
absent store      = 1 in sequential baseline
sequential_total  = 2 + 5 + 1 = 8
pipelined_total   = 5 + 2 = 7
saved/overlap     = 0
reported speedup  = 8/7 = 1.142857x
```

The apparent gain comes entirely from charging the absent store only in the sequential baseline.

### Depth-one compute-only case

A three-cycle tile with no load or store reports:

```text
sequential_total = 1 + 3 + 1 = 5
pipelined_total  = 3
saved            = 0
speedup          = 1.666667x
```

Again, no overlap exists. The baseline's two invented one-cycle operations create the ratio.

### Depth-two first-tile case

At depth two, a first tile without a load starts directly in COMPUTE. Submission sets its deadline, but `total_compute_cycles` is normally credited only on PRELOAD→COMPUTE transition. That transition is skipped. With five compute cycles:

```text
sequential_total = 1 + 5 + 1 = 7
pipelined_total  = 0
saved            = 0
speedup          = infinity.
```

Canonical evidence records `PIPE_EMPTY ... seq=7 piped=0 ... speedup=inf`. Infinite reported speedup is an accounting defect, not exceptional overlap.

The controller credits load overlap from `total_bytes/32` when `active_count >= 2`, and similarly credits stores under an active-count condition. It does not prove simultaneous byte effects, independent ports, or command execution. It also reads the standalone double-buffer overlap ledger at tile completion, but never calls `tu_sram_record_overlapped_cycles()` itself. The controller's ledger and standalone ledger are separate producers even inside the same file-level bridge.

The rule is strict: **never cite controller `speedup` as latency hiding at this pin.** The safe evidence consists of exact state transitions and explicit ledger arithmetic, not the field name.

## 16.9 Worked example 4: capacity and historical M-tiling analysis

A historical report studies GEMM with `M=N=128`, `K=256`, a 16×16 PE array, **PE-array pipeline depth 2**, 32 B/cycle, and an ideal independent-port overlap formula while varying O-role capacity. It assumes 1.0 GHz and counts two operations per MAC, so `operations=2MNK=8,388,608` and `TOPS=operations/cycles/1000`. Canonical v4 recomputes all ten rows from the report's equations:

| O role capacity | M chunks | Sequential cycles | Ideal hidden cycles | Ideal DB total | Recomputed TOPS | Ideal speedup |
|---:|---|---:|---:|---:|---:|---:|
| 16 KiB | 32/32/32/32 | 28,752 | 9,216 | 19,536 | 0.429 | 1.472x |
| 24 KiB | 48/48/32 | 26,688 | 6,912 | 19,776 | 0.424 | 1.350x |
| 32 KiB | 64/64 | 24,624 | 4,096 | 20,528 | 0.409 | 1.200x |
| 40 KiB | 80/48 | 24,624 | 4,096 | 20,528 | 0.409 | 1.200x |
| 48 KiB | 96/32 | 24,624 | 4,096 | 20,528 | 0.409 | 1.200x |
| 56 KiB | 112/16 | 24,624 | 4,096 | 20,528 | 0.409 | 1.200x |
| 64 KiB | 128 | 22,560 | 0 | 22,560 | 0.372 | 1.000x |
| 80 KiB | 128 | 22,560 | 0 | 22,560 | 0.372 | 1.000x |
| 96 KiB | 128 | 22,560 | 0 | 22,560 | 0.372 | 1.000x |
| 128 KiB | 128 | 22,560 | 0 | 22,560 | 0.372 | 1.000x |

These values are **Historical / Analytical model / Estimated / uncalibrated**. Their arithmetic is reproducible under the report's assumptions; they are not produced by the controller and do not repair its byte bridge.

Four corrections constrain the interpretation.

First, 16 KiB is one role's logical capacity. Equal ping-pong allocation consumes 32 KiB. Relative to a 64 KiB single O buffer, the physical saving is 2×, not 4×. W/A duplication must also be included if the overlap schedule requires their shadow roles.

Second, the report's “512 bytes/cycle” premise conflicts with 256 PEs each receiving two FP16 operands under an independent-per-PE-read interpretation:

```text
256 PEs × 2 operands/PE × 2 bytes/operand = 1,024 B/cycle.
```

A systolic boundary-injection model could require fewer external bytes because operands are reused across the array, but it needs an explicit topology and injection equation. Neither 512 nor 1,024 may be selected without naming the physical movement model.

Third, the report's `m_tile >= 20` hiding threshold does not solve its tile-dependent equation. Continuous algebra gives `18.285714...`; after applying the report's ceiling-aware systolic timing, the first passing integer is **17**, because compute cost jumps at the 16-row boundary. Thresholds involving ceilings and alignment must be evaluated on the exact discrete equation, not rounded from one sample transfer cost.

Fourth, adding independent preload and store credits is legal only when the resources are independently serviceable. The v4 discriminator sets `C=100`, `P=80`, and `S=80`: `min(C,P)+min(C,S)=160`, which exceeds one 100-cycle compute window. For a shared resource, combined credit is capped at 100; independent resources require an explicit port/channel proof.

```text
CH16_SWEEP_RESOURCE_GUARD C=100 P=80 S=80 uncapped=160 shared_cap=100
```

The table can support a bounded insight: under its ideal assumptions, smaller role capacity creates more chunks and more potential overlap windows, while a one-chunk case has no inter-tile window. It cannot support “always beneficial,” “single highest-leverage optimization,” a fixed ~3% area claim, or compiler recommendations. The compiler path cited historically is not executable at this edition, and the model has no physical area, energy, arbitration, startup policy, or calibration evidence.

## 16.10 Trade-offs: choosing an architecture by regime

| Alternative | Useful regime | Potential performance effect | Capacity/area/energy cost | Control and verification burden |
|---|---|---|---|---|
| single buffer | capacity-bound workload; producer and consumer cannot legally overlap | no same-region preload/compute hiding; largest tile may reduce reloads | one data allocation; lowest leakage and movement metadata | simplest ownership and reset protocol |
| equal ping-pong | repeated similar tiles; explicit completion; genuinely independent access resources | steady interval may approach `max(D,C)` after fill and before drain | 2× data allocation per buffered region; possible extra dynamic traffic | role/generation tracking, completion, swap ordering, context/reset tests |
| bank/partition schedule | current and next tiles fit disjoint banks or partitions | partial overlap without duplicating full region | banking/ports, fragmentation, mapping constraints | conflict/arbitration proof; layout-sensitive tests |
| triple/ring | producer/consumer variance or deeper queues cause bubbles | extra slack can absorb jitter and improve occupancy | at least three slots or partitioned capacity; more metadata | head/tail generations, reclamation, backpressure, cancellation |
| event/queue-backed pipeline | system-level correctness and timing questions | composable start/completion schedule and explicit dependencies | queues/events/controller state; potentially more area/power | largest state space: failure, cancellation, ordering, clock crossing, liveness |

Single buffering is often preferable when doubling storage forces smaller tiles and additional transfers, when `D` is tiny relative to `C`, when startup/drain dominate a short workload, or when no independent port exists. Ping-pong is attractive when tile generations repeat, both roles fit, the producer and consumer use independent resources, and `D` and `C` are close enough that hidden time repays the duplicated capacity and control.

Bank partitioning trades full duplication for mapping complexity. It can work well when addresses can be statically separated, but “different banks” must be proved under the actual bank map and simultaneous request model. Triple/ring buffering addresses variance rather than changing fundamental bandwidth; if the producer is sustainably slower than the consumer, extra slots postpone but do not remove starvation. Event-backed integration is the strongest path when the research question concerns elapsed time, but it is also the most expensive to implement and verify.

Area and energy conclusions require a separate calibrated model. Equal-size arrays plausibly increase data-array area and leakage; more ports and banking plausibly add wires and arbitration; extra copies and accesses plausibly affect dynamic energy. Tusim's standalone allocation and counters quantify none of those physical costs. Accelergy illustrates an appropriate methodology—action counts combined with versioned primitive energy values—but its estimates would inherit technology and characterization uncertainty and do not validate Tusim automatically ([WU19](../../references/foundations.md#wu19-accelergy)).

## 16.11 A legal-overlap design and verification contract

A future integrated design should make the legal path explicit rather than relying on pointer convention. Full-stack accelerator studies reinforce that runtime and software integration materially affect achieved behavior; they do not establish Tusim's missing bridge ([GEN21](../../references/foundations.md#gen21-gemmini)). One possible contract is:

```text
FREE(g) -> PRODUCING(g) -> READY(g) -> ACTIVE(g) -> RETIRED(g) -> FREE(g+2)
```

Each slot carries a generation `g`, expected byte extent, produced extent, producer outcome, and reader count. The producer receives a capability naming one physical slot—not a role that can change while a descriptor is pending. Completion publishes `READY(g)` only after the full extent and memory visibility rules pass. A swap or active-generation update requires `READY(g)` and retirement of the prior active generation. Consumers acquire `ACTIVE(g)` and release it explicitly. Reset either drains/cancels all generations or fails while ownership is live.

Useful invariants include:

1. exactly one active generation per region;
2. active and producing generations occupy different physical slots;
3. a slot cannot become active before full successful completion;
4. a slot cannot be reused while any reader holds its generation;
5. every completion event names the same slot and generation the producer wrote;
6. a role change is atomic with respect to consumer address resolution;
7. reset/context save either preserves all ownership state or rejects the transition;
8. every accounted hidden interval is contained within a real common-clock overlap interval;
9. summed overlap credits never exceed elapsed compute or transfer windows;
10. failed, partial, canceled, and timed-out producers never authorize a swap.

Verification should combine source predicates, state-transition tests, and discriminating byte canaries. Use different sentinel patterns in both allocations; probe clean, partial, failed, and repeated writes; cross odd and even swap counts; disable with each role active; reset only after moving state; save/restore with a live generation; and test concurrent producer/consumer schedules at exact completion boundaries. Mutate one legality check and require the suite to fail. For elapsed-time claims, compare event traces against a named reference and state clock conversion and error.

## 16.12 Verification: reproducible evidence and what it proves

The sole predraft authority is:

```text
experiments/runs/ch16-double-buffer/20260804-ch16-canonical-v4/
```

It was sealed from book input commit `abf3278561fdf9263bcc8a92b4f5af1c61b74c9c` against the clean detached Tusim pin. The immutable bundle records:

- 31 exact pinned-source hashes;
- 60 structural/reachability predicates, 91 checks total;
- a source-hash mutation that fails, followed by successful restoration;
- archive membership for both objects and static linkage of chapter binaries;
- direct focused double-buffer execution, 10/10;
- a forced focused assertion mutation, 9/10 with inferior exit code 01;
- exact standalone, stale-bridge, no-load-swap, controller-ledger, reset, live-reinit, context-restore, and clock lines with probe `failures=0`;
- all ten historical table rows plus capacity, port-width, threshold, and shared-resource checks;
- an AddressSanitizer lifecycle run for address-error checks, with leak detection disabled globally (`detect_leaks=0`), and a fail-fast runner whose body exit is captured through `pipefail` and `PIPESTATUS[0]`;
- source/book provenance before and after execution.

The skeptical predraft review independently read the pinned source, rebuilt in a disposable tree, hand-derived the state transitions, and blocked provisional v1. Canonical v2 carried the amended evidence but its validator still expected v1's 25/42/67 counts instead of the produced 31/51/82. Canonical v3 passed the expanded evidence but is superseded because its runner could continue after stale grep failures and because the complete review added lifecycle, widened-bounds, and shared-resource gates. Only fail-fast v4 is drafting authority. The live reinitialization and context ownership-loss/leak conclusions come from source and pointer-lifecycle analysis, not LeakSanitizer, because v4 globally disabled leak detection. See the [skeptical-review dispositions](../../notes/chapter-16-skeptical-review-dispositions.md) and [predraft gate closure](../../notes/chapter-16-predraft-gate-closure.md).

From the book root, the maintained audit entry points are:

```bash
bash experiments/run_ch16_double_buffer_audit.sh
python3 experiments/ch16_predraft_validate.py
```

These results establish snapshot conformance for the bounded chapter claims. They do not prove the unsafe four-channel pipeline suite, general workloads, ordinary-operation integration, physical overlap, area, power, energy, or calibration.

## 16.13 Fidelity box: safe and unsafe conclusions

> **Executable:** equal-size shadow allocation; active/shadow pointer selection; clean and written swaps; caller notifications; additive ledgers; role-aware disable; direct destroy; active-aware generic SRAM accesses; descriptor destination precedence; bounded controller state transitions; and the exact negative bridge.
>
> **Integrated legal-overlap path: none at this pin.** Descriptor DMA and the double-buffer API meet only inside a library-present internal bridge candidate. That source-level composition is functionally wrong for shadow loading, and no non-test caller invokes the controller. Standalone double buffering is API-only; context and configuration do not provide a valid bridge.
>
> **Functional model:** the standalone state machine can represent bytes and role swaps when a correct external owner imposes legality. The pinned controller does not provide that owner.
>
> **Analytical model / Estimated:** controller overlap credits, sequential/pipelined totals, reported speedup, and historical M-tiling equations are uncalibrated arithmetic. Controller speedup is rejected as overlap evidence because exact zero-overlap cases report `1.142857x`, `1.666667x`, and infinity.
>
> **Historical:** documentation timelines and broad optimization recommendations express intent beyond pinned execution. Recomputed report rows remain useful only under their stated ideal assumptions.
>
> **Calibration:** none against RTL, FPGA, silicon, physical SRAM ports, a compiler/runtime schedule, or an external timing trace.

The chapter does not establish independent per-buffer banks, atomic hardware pointer exchange, coherent memory visibility, command execution, queue-backed completion, context compatibility, a common clock, sustainable bandwidth, elapsed pipeline latency, physical capacity overhead beyond allocated host bytes, or any universal performance winner.

## 16.14 Common failure modes

1. **Two arrays imply overlap.** Storage duplication creates capacity for roles, not simultaneous service or a schedule.
2. **Dirty means valid.** The bit can be set without changing bytes and carries no extent, generation, or outcome.
3. **Shadow means `shadow_data`.** After an odd swap, primary is the shadow role.
4. **Completed means elapsed service.** Descriptor execution, timestamp eligibility, DMA tick, and controller time differ.
5. **Setting `dst_host` redirects DMA.** A non-null `dst_region` takes precedence and resolves the active pointer.
6. **Swap after completion is safe.** The completed producer may have targeted the wrong physical allocation.
7. **Notify after swap repairs state.** It marks the post-swap shadow; it cannot make stale active bytes fresh.
8. **Stored `cmd_id` means compute happened.** The controller never dispatches or waits on that command.
9. **Positive speedup means hidden cycles.** Baseline asymmetry and skipped accounting produce gains with saved=0.
10. **Depth one is a safe baseline.** A descriptor-free tile still swaps unwritten storage.
11. **Reset restarts the controller.** It destroys state; later submission auto-initializes depth one.
12. **Context save preserves a region.** It drops and leaks live double-buffer ownership state.
13. **A config field enables behavior.** The hierarchy field is decorative; no shipped runtime selector enables this API.
14. **Logical role capacity equals physical cost.** Equal ping-pong consumes twice the role bytes.
15. **Ideal table equals executable result.** Historical equations assume resources and schedules the controller does not prove.
16. **`.PHONY` name means test target.** `test-double` has no recipe and is not aggregate.
17. **Scheduler “double buffering” is the same module.** It is a separate instruction-order/address-range model.

## 16.15 Development questions

1. Should descriptors target immutable physical buffer handles plus generations rather than mutable region roles?
2. Which event should authorize `READY`: executor return, transport completion, cache/coherence visibility, or a composed dependency?
3. How should partial, failed, canceled, and multicast producer outcomes affect validity?
4. Should swap return failure unless expected bytes and generation match?
5. Should dirty state be replaced by per-slot validity, extent, and epoch metadata?
6. Which component owns the common clock and advances DMA, SRAM, compute, and controller events?
7. Should the controller dispatch a command and consume its completion instead of using only a deadline?
8. How should load and store arbitration prevent overlap-window double counting?
9. Should bank meters be per physical allocation, shared by port, or replaced by an explicit arbiter model?
10. How should reset, context save/restore, cancellation, and destruction preserve or reject live ownership?
11. Which configuration surface selects buffered regions, slot count, ports, and policy, and how will each field show a discriminating effect?
12. What RTL, simulator, or hardware trace will calibrate startup, steady-state, drain, and contention by regime?

## Summary

Double buffering is a protocol over ownership, generations, completion, visibility, and shared resources; two allocations and a swap function are only storage machinery. Tusim's standalone primitive routes access by role but swaps unconditionally, shares one bank meter, and loses ownership under unsafe reinitialization or context restore. Its controller writes old-active bytes, can expose stale or unwritten data, never dispatches `cmd_id`, and reports speedups even when no cycles are saved. The historical M-tiling arithmetic is usable only under its ideal assumptions and corrected capacity, port, threshold, and resource guards. Single, ping-pong, partitioned, ring, and event-backed designs serve different regimes. At this pin, Tusim provides an executable standalone primitive and a negative controller bridge—not a validated ordinary-operation overlap pipeline.

## Review questions

1. What is the difference between the primary allocation and the active role?
2. List the minimum conditions that must hold before a swap is legal.
3. Why can `shadow_dirty=true` coexist with unchanged shadow bytes?
4. Why does descriptor DMA write active rather than shadow when both `dst_region` and `dst_host` are set?
5. Trace the `0x11/0x22/0x7a` bridge example through physical allocations.
6. Why are descriptor `completed`, `cycles_completed=53`, DMA cycle 1, and controller cycle 0 not contradictory?
7. Derive the controller's `8/7` and `5/3` ratios and explain why neither proves overlap.
8. How can a depth-two first tile produce infinite reported speedup?
9. What physical data capacity does a 16 KiB equal ping-pong role consume?
10. Why does a shared bank meter invalidate an inference of independent per-buffer ports?
11. Which parts of the historical M-tiling result are usable, and which recommendations are rejected?
12. What evidence would promote a ping-pong implementation from standalone machinery to legal integrated overlap?

### Review-question answer key

1. Primary is the fixed `r->banks.data` allocation; active is the logical role selected by `active_idx`. After an odd swap, `shadow_data` is active and primary is shadow.
2. Correct physical target, complete intended extent, successful producer completion, retirement of prior consumers, single authorized transition, new-active visibility, a common schedule for timing, and lifecycle preservation.
3. Only `tu_sram_notify_shadow_write()` sets the bit, and it does not inspect or copy bytes; the probe marks dirty while `0x00` remains `0x00`.
4. The executor gives non-null `dst_region` precedence and resolves it through `tu_sram_raw_ptr()`, which returns the current active pointer. `dst_host` is ignored in that branch.
5. DMA changes primary active from `0x11` to `0x7a`; `shadow_data` remains `0x22`; swap makes `shadow_data=0x22` active and primary=`0x7a` shadow; notification marks that post-swap shadow dirty.
6. Selection executes the copy and sets the descriptor fields during DMA tick 1; 53 is future retirement eligibility, while `tu_pipeline_advance()` does not increment the controller's own cycle. They are different producers and meanings.
7. One load: sequential `2+5+1=8`, pipelined `5+2=7`, saved 0. Compute-only depth one: sequential `1+3+1=5`, pipelined 3, saved 0. Absent-operation baseline charges create both ratios.
8. The tile starts directly in COMPUTE, skipping the transition that credits `total_compute_cycles`; sequential becomes 7 while pipelined remains 0, so division yields infinity.
9. 32 KiB of data allocation: two equal 16 KiB physical slots. Per-role usable capacity remains 16 KiB.
10. The meter, refill cycle, available words, stalls, and counters live once in `r->banks` and follow the active role. Distinct bytes alone do not create two service resources.
11. The ten rows and trends are reproducible under the report's ideal formula. They remain uncalibrated; physical capacity, 512 B/cycle, threshold 20, universal benefit, area percentage, and compiler recommendations are not supported as stated.
12. A traced ordinary-operation caller; immutable physical target identity; generation/extent validity; success and dependency events; command execution; shared-clock scheduling; resource arbitration; lifecycle safety; discriminating tests; and calibration for physical performance claims.

## Design exercises

1. **Legal state machine.** Define states and transitions for two slots with generation IDs, partial transfer, failure, cancellation, reader retirement, swap, and reset. State ten invariants and one mutation test per invariant.
2. **Pointer-resolution repair.** In a disposable source copy, redesign descriptor destinations to name a physical slot. Prove with three sentinels that role changes while a descriptor is pending cannot redirect the write.
3. **Timeline derivation.** For four tiles with `D=60`, `C=100`, `S=30`, derive sequential, load-only overlap, one-channel load/store overlap, and independent load/store-channel overlap of preload, compute, and prior-store, including startup and drain. Name every resource assumption and required slot capacity.
4. **Capacity crossover.** Compare a 64 KiB single O buffer with 16, 24, and 32 KiB ping-pong roles. Include physical bytes, chunk count, transfer traffic, startup/drain, and a leakage/area proxy. Identify regimes where the single buffer wins.
5. **Controller ledger redesign.** Replace absent-operation defaults with zero, credit compute on every path, and derive `pipelined_total` from an event trace. Require that speedup is 1.0 whenever overlap credits are zero and work is otherwise identical.
6. **Context protocol.** Specify save/restore for both allocations, active generation, valid extents, counters, and pending descriptors. Decide whether live producers may cross a context boundary and justify the verification cost.
7. **Bank/partition alternative.** Map two FP16 tiles onto disjoint banks under `(addr/4) mod 32`. Quantify padding and fragmentation, then design a conflict test that distinguishes the partition from equal ping-pong.
8. **Historical audit.** Recompute all M-tiling rows, derive the continuous `18.285714...` threshold and exact integer 17, and replace the 512 B/cycle statement with two explicit alternatives: independent per-PE reads and systolic boundary injection.
9. **Calibration plan.** Choose a named RTL or trace reference. Define producer/consumer events, clocks, workloads, fill/steady/drain metrics, error measures, training/validation regimes, and acceptable uncertainty.

### Selected worked design-exercise answers (Exercises 1–3)

Exercises 4–9 are open-ended projects. A complete submission must state assumptions and units, preserve the chapter's evidence labels, provide reproducible calculations or probes, compare at least two alternatives, identify one discriminating negative test, and bound every conclusion to the modeled resources and source revision.

#### Exercise 1 — legal state machine

Use per-slot state `FREE → PRODUCING(g) → READY(g) → ACTIVE(g) → RETIRED(g) → FREE`, where `g` is a generation. Each slot carries expected extent, produced extent, producer outcome, and reader count. Permit `PRODUCING→READY` only after successful full delivery; partial, failed, canceled, and timed-out production moves to an invalid/reclaim path and never authorizes activation. Permit `READY(g)→ACTIVE(g)` only when the previous active generation has no readers and exactly one owner consumes the matching authorization event. Reset must either prove quiescence or cancel producers, retire readers, invalidate both slots, and reconstruct a named initial state.

Ten useful invariants are: one active generation; distinct active/producing slots; ready implies full extent; failed output is never ready; reader count is zero before reuse; completion slot and generation match the producer capability; one authorization causes at most one role exchange; stale/duplicate generations are rejected; reset preserves or explicitly invalidates every generation; and overlap credit never exceeds a real common-clock intersection. Mutate each guard in a disposable source copy and require a focused negative test to fail—for example, remove the full-extent guard and submit a 63-byte result for a 64-byte consumer.

#### Exercise 2 — pointer-resolution repair

Give a descriptor an immutable physical-slot handle plus generation instead of both a mutable region and host fallback. Initialize primary `0x11`, added allocation `0x22`, and source `0x7a`. Submit a descriptor explicitly naming the added allocation and generation `g+1`; swap the region roles while it is pending as an adversarial action. After execution, the physical primary must remain `0x11` and the named added allocation must become `0x7a`, regardless of its current role. Activation is permitted only when completion reports the same slot and generation. The pinned controller instead writes primary through active-aware `dst_region`, yielding primary `0x7a`, added allocation `0x22`, then stale active `0x22` after swap. Checking both physical pointers before and after the transition distinguishes the repaired contract from role-dependent redirection.

#### Exercise 3 — timeline derivation

Assume four tiles, one common clock, `D=60`, `C=100`, `S=30`, enough input/output slots, legal dependencies, and no arbitration cost beyond the stated channels. Fully sequential execution costs

```text
4(D+C+S) = 4(60+100+30) = 760 cycles.
```

For **load-only overlap**, allow each next load to overlap current compute but serialize every store after its compute and before the next compute. The first fill is exposed; four computes and four stores remain:

```text
D + 3·max(D,C) + C + 4S
= 60 + 300 + 100 + 120
= 580 cycles.
```

For **one shared load/store DMA channel**, schedule at most one DMA operation at a time. Each 100-cycle intermediate compute window can hold a 60-cycle next preload plus a 30-cycle prior store without overlap between those DMA operations. The initial load and final store remain exposed:

```text
D + 4C + S = 60 + 400 + 30 = 490 cycles.
```

With **independent load and store channels**, next preload and prior store may overlap each other and compute, so this particular regime also gives `60 + 4·100 + 30 = 490` cycles. Equality is not general: it occurs because `D+S=90 ≤ C`. If `D+S>C`, one shared channel lengthens the steady interval while independent channels use `max(D,C,S)`. These are analytical schedules, not pinned-controller results.

## Primary references

- **[SMI84]** James E. Smith, “Decoupled Access/Execute Computer Architectures,” *ACM Transactions on Computer Systems*, 1984. DOI: [10.1145/357401.357403](https://doi.org/10.1145/357401.357403). Queue-connected streams motivate latency tolerance while preserving synchronization and capacity obligations.
- **[BAN02]** Rajeshwari Banakar et al., “Scratchpad Memory: A Design Alternative for Cache On-Chip Memory in Embedded Systems,” CODES 2002. DOI: [10.1109/CODES.2002.1003604](https://doi.org/10.1109/CODES.2002.1003604). Scratchpads motivate explicit placement and ownership; old-node quantitative results do not transfer.
- **[PAR19]** Angshuman Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019. DOI: [10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042). Workload, architecture, mapping, and constraints must remain explicit.
- **[KWO19]** Hyoukjun Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” MICRO 2019. DOI: [10.1145/3352460.3358252](https://doi.org/10.1145/3352460.3358252). Analytical reuse and performance inference depend on stated mappings and resources.
- **[GEN21]** Hasan Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” DAC 2021. DOI: [10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216). Full-stack integration affects achieved behavior; its results are not Tusim calibration.
- **[WU19]** Yannan Nellie Wu, Joel S. Emer, and Vivienne Sze, “Accelergy: An Architecture-Level Energy Estimation Methodology for Accelerator Designs,” ICCAD 2019. DOI: [10.1109/ICCAD45719.2019.8942149](https://doi.org/10.1109/ICCAD45719.2019.8942149). Action-based energy estimation supplies methodology, not physical values for this snapshot.
