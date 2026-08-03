# Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution

> **Edition scope.** This chapter describes Tusim at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. It treats descriptor construction, byte geometry, queue admission, tick-driven execution, counters, ownership, and operation reachability as separate contracts. “Asynchronous” means that a submitted descriptor waits for explicit engine ticks; it does not by itself establish dependency visibility, physical overlap, shared-fabric contention, or calibrated DMA latency.

## Learning objectives

After this chapter, you should be able to:

1. choose among linear, 2D, 3D, scatter/gather, and multicast descriptor forms;
2. distinguish copied bytes, accounted bytes, addressed span, unique bytes, and multicast fanout;
3. state which descriptor fields are copied and which caller-owned objects remain borrowed;
4. distinguish construction, acceptance, pending reachability, selection, executor return, flag setting, timestamp eligibility, and channel retirement;
5. explain why synchronous and tick-driven submission do not provide one uniform ownership contract;
6. calculate the pinned descriptor service estimate and identify its cycle domain;
7. explain why direct host-visible copying does not imply command-level dependency visibility;
8. identify the shared-`next` queue/chain defect and its safe-subset consequences;
9. trace parsed DMA configuration to the point where propagation stops;
10. distinguish focused-tested descriptor behavior from ordinary-operation integration;
11. recognize destructive reinitialization, fixed channel-array, and bounds-safety constraints;
12. design experiments that do not overclaim concurrency, throughput, or physical performance.

## Prerequisite graph

```text
Chapter 4: parsed configuration -> effective runtime state
                              |
Chapter 5: public API -> singleton ownership -> lifecycle and reset
                              |
Chapter 6: tensor geometry, tiling, and caller-provided extents
                              |
Chapter 9: SRAM regions, bank budgets, raw-pointer bypass, cycle domains
                              v
 descriptor geometry -> ownership -> admission -> execution -> retirement
          |                 |           |            |             |
          +-----------------+-----------+------------+-------------+
                                      |
                                      v
                    defensible data-movement conclusion
```

Chapter 4 established that a field can parse without reaching active state. Chapter 5 showed why initialization, destruction, and process-global ownership must be audited together. Chapter 6 separated logical tensor geometry from caller safety, and Chapter 9 separated storage, service accounting, and operation integration. Chapter 10 combines those lessons for the descriptor-transfer subsystem.

## Opening architecture question: submitted is not delivered

Suppose a compiler creates a 64-byte host-to-SRAM descriptor, submits it to an asynchronous channel, and receives a nonzero descriptor ID. May the dependent compute command run?

Not from that fact alone. At the pinned revision, a nonzero ID means that the submitted head passed channel/depth checks and was linked into engine state. The copy does not occur until a tick selects the descriptor. When selection does occur, the C executor copies bytes, sets selected descriptor state on successful paths, and computes a future timestamp in one host call. The active channel slot remains occupied until a later tick reaches that timestamp. No ordinary command dependency consumes the descriptor's `signal_id`, and no coherent-memory event is modeled.

At least seven questions must therefore remain separate:

1. **representability** — can the descriptor encode the intended addresses and fanout?
2. **span safety** — do all addressed elements fit, including strides and indices?
3. **lifetime** — which buffers, arrays, regions, and descriptors must remain alive?
4. **admission** — was the submitted head accepted into a channel?
5. **execution outcome** — did the executor copy/account successfully or return on error?
6. **retirement** — when does the channel release its active slot?
7. **integration** — what ordinary operation or dependency path observes the event?

The reader decision for this chapter is correspondingly narrow:

> Given a transfer pattern and caller-managed ordering plan, which pinned descriptor form, channel mode, queue depth, and synchronization action can represent it safely—and which byte, timing, completion, and integration conclusions does the executed path support?

## 10.1 Why descriptor DMA is its own architectural boundary

The chapter deliberately does not combine address generation, double buffering, pipeline control, DRAM calibration, and descriptor execution into one “data movement” story. Those modules have different owners, APIs, clocks, counters, and call-site reachability. Source presence or archive linkage cannot manufacture an end-to-end contract.

The pinned descriptor subsystem provides:

- a process-global engine, `g_tu_dma`;
- a fixed channel-state array;
- constructors for linear, strided, scatter/gather, and multicast forms;
- synchronous submission and explicit tick-driven submission;
- queue, byte, transfer, and estimated-cycle counters;
- focused tests and standalone consumers;
- limited pipeline-controller use of submitted descriptors.

It does not provide a general ordinary-operation descriptor operand, a scheduler that consumes descriptor priority, a completion registry keyed by `signal_id`, a descriptor-to-DRAM timing call, or a calibrated shared DMA fabric.

Decoupled access/execute architectures motivate queues and latency tolerance, but queue capacity, synchronization, and backpressure determine whether decoupling actually survives ([SMI84](../../references/foundations.md#smi84-decoupled-accessexecute)). Gemmini illustrates why software, ISA, runtime, and hardware integration matter together; its contract is not evidence that Tusim's standalone descriptor API is integrated ([GEN21](../../references/foundations.md#gen21-gemmini)). Production TPU results likewise show the importance of complete-system behavior, not transferable constants for Tusim ([JOU17](../../references/foundations.md#jou17-production-tpu-analysis)).

### Compact source map

| Pinned path | Role | Evidence boundary |
|---|---|---|
| `tu_cmodel/dma_descriptor.[ch]` | descriptor types, constructors, queueing, execution, ticks, counters | authoritative descriptor-engine contract |
| `tu_cmodel/tu_dma.[ch]` | legacy fixed-region wrapper API and global initialization | ordinary wrapper bridge, not general descriptor exposure |
| `tu_cmodel/tu_cmodel.[ch]` | top-level W/A/O wrappers and accounting | exposes global/embedded state split |
| `tu_cmodel/command_queue.c` | fixed DMA command dispatch | routes named operations through legacy wrappers |
| `tu_cmodel/infra/config.[ch]` | parses DMA configuration | conversion drops DMA fields before active initialization |
| `tu_cmodel/memory/address_generator.[ch]` | optional descriptor-chain helper | detailed address generation deferred; focused failure remains visible |
| `tu_cmodel/compute/pipeline_controller.[ch]` | bounded descriptor consumer and shadow-buffer actions | not proof of correct overlap or speedup |
| `tests/test_dma.c`, `test_scatter_gather.c`, `test_multicast.c` | focused behavior | local semantics, not ordinary-operation integration |

## 10.2 Choosing a descriptor geometry

A descriptor should express the transfer events the executor actually performs, not merely resemble the tensor's conceptual shape.

| Form | Intended representation | Caller must verify |
|---|---|---|
| linear | one contiguous element sequence | base, total byte extent, direction, lifetime |
| 2D strided | rows of contiguous columns | source and destination row spans, both strides |
| 3D strided | depth planes containing strided rows | depth and row spans on both sides |
| scatter | contiguous host elements to indexed SRAM elements | every index and duplicate policy |
| gather | indexed SRAM elements to contiguous host elements | every index and source lifetime |
| multicast | one source copied to several SRAM destinations | every target region/offset and fanout accounting |

Let:

- `n` be an element or index count;
- `m` be multicast target count;
- `e` be element size in bytes;
- `c`, `r`, and `d` be columns, rows, and depth;
- `s_r` and `s_d` be row and depth strides in bytes.

Then the relevant quantities are:

```text
linear copied/accounted bytes = n e

2D copied/accounted bytes = r c e
2D addressed span = 0                         if r = 0 or c = 0
                    (r - 1)s_r + c e          otherwise

3D copied/accounted bytes = d r c e
3D addressed span = 0                         if d = 0, r = 0, or c = 0
                    (d - 1)s_d + (r - 1)s_r + c e   otherwise

scatter/gather accounted bytes = n e
multicast source bytes = n e
multicast requested fanout bytes = m n e.
```

For an empty scatter/gather list, the addressed envelope is empty and its span is zero. For a nonempty list, an envelope can be formed from the minimum and maximum index, but unique bytes touched can still be smaller than `n e` because indices may repeat or overlap. In multicast, requested fanout can exceed delivered bytes when an invalid target is skipped.

These equations use nonnegative mathematical integers. The implementation uses unchecked `uint32_t` products and sums. It also checks selected linear/strided bounds using base plus `total_bytes`, not the maximum stride-derived address. A compiler or caller must therefore prove arithmetic, span, and index safety before submission.

### Executable geometry oracles

The canonical probe uses nonsymmetric geometry so swapped strides cannot pass accidentally:

- **2D:** two rows by three columns by two bytes, with 11-byte host and 13-byte SRAM row strides. Copied bytes are 12; source and destination spans are 17 and 19 bytes.
- **3D:** two depths by two rows by three columns by one byte, with host row/depth strides 5/13 and SRAM strides 7/20. Copied bytes are 12; source and destination spans are 21 and 30 bytes.
- **scatter duplicates:** offsets `{4,4,8}` generate three one-byte transfer events but touch two unique positions; the later write wins at offset four.
- **multicast:** four source bytes to two valid targets produce four source bytes and eight requested/delivered fanout bytes.

These are **Executable** functional checks for named in-bounds cases. They do not prove unchecked overflow safety or general physical traffic.

## 10.3 Descriptor fields are not all architectural controls

The public descriptor contains geometry, direction, channel, bookkeeping, and linkage fields. Presence is not consumption.

At the pin:

- constructors compute `total_bytes` for the selected form;
- `completed` and `cycles_completed` are written on successful accounted execution paths;
- `cycles_issued` remains zero on the audited executor path;
- `priority` has no descriptor-engine scheduling consumer;
- `signal_id` has no descriptor completion-registry consumer;
- `next` serves both descriptor-chain structure and channel-queue linkage.

The last point is a correctness defect, discussed in Section 10.6. The inert fields are an integration limitation. A compiler must not infer priority scheduling, timestamped issue, or dependency signaling merely because fields exist.

## 10.4 Ownership and borrowed state

There is no single rule that “the engine owns a submitted descriptor.” Ownership depends on outcome and lifecycle state.

| Object/state | Construction | While accepted/pending/active | After proven sync return or async retirement | Rejection/destruction hazard |
|---|---|---|---|---|
| descriptor and `next` chain | caller allocates through constructor | engine borrows and links; caller must not free | caller cleanup is required after proving no alias remains | rejected submission recursively destroys the chain |
| linear/strided host buffer | borrowed | must remain valid through executor return | caller may reuse after the required observation | never engine-owned |
| scatter/gather index list | borrowed | must remain stable through executor return | caller may reuse | never engine-owned |
| SRAM region object/storage | borrowed | must remain initialized and stable | caller-managed | never descriptor-owned |
| multicast source | borrowed | must remain valid | caller-managed | never descriptor-owned |
| multicast region/offset arrays | copied into descriptor allocations | descriptor owns copies; pointed-to regions remain borrowed | freed only by explicit descriptor destruction | raw pending-list free can leak nested arrays |
| process-global engine | singleton | owns queue/active references, not a uniform descriptor reclamation promise | explicit safe cleanup only after quiescence | reinitialization overwrites state without teardown |

The borrowed-state probe constructs a scatter descriptor, mutates the source byte and first index before submission, and observes the mutated byte at the mutated destination. This is direct evidence that both objects are borrowed until execution.

### Destructive reinitialization

`tu_dma_init_full()` begins by zeroing `g_tu_dma`. It does not first destroy pending or active descriptors. Reinitialization can therefore orphan descriptor objects and descriptor-owned multicast arrays. Top-level reinitialization reaches the same engine initialization path.

Reinitialization is not cleanup. A caller must reach a structurally safe quiescent state before initializing again. The canonical corruption probes do not use reinitialization to abandon unsafe state: each case runs in a separate child process, initializes once before submission, records the graph, and exits through `_exit()` without DMA flush, traversal, or destruction.

## 10.5 Synchronous and tick-driven lifecycle

Use operational predicates rather than the overloaded word “completed.”

| Predicate | Meaning at the pin |
|---|---|
| constructed | descriptor and copied/borrowed metadata initialized |
| accepted | submit returns nonzero; rejection may already have destroyed the chain |
| pending/reachable | node is reachable from channel `head` through `next` |
| selected | tick removes `head`, assigns `active`, and invokes the executor in that same call |
| executor returned | copy/accounting function returned, possibly on error |
| directly observable | host inspection sees copied model bytes |
| flag set | `desc->completed == true`; not universal all-target success |
| timestamp eligible | engine cycle reaches `cycles_completed` |
| channel retired | active slot clears and channel retirement counter increments |
| safely reusable | caller proves no pending, active, or corrupted-graph alias remains |

### Synchronous submission

With synchronous mode, submission walks and executes the linked descriptor sequence inside `tu_dma_submit_desc()`. There is no pending interval requiring ticks. The channel's `total_submitted` increments once for the submitted head, while execution and `total_completed` can advance once per traversed node. Queue depth is also decremented per node even though it was incremented once per submitted head.

Synchronous return does not automatically reclaim a successful descriptor. The caller must destroy it only after proving no alias remains. Rejection is different: the submit path destroys the rejected chain internally.

### Tick-driven submission

In tick-driven mode, accepted submission links a head into a channel. A tick first examines the existing active descriptor for timestamp retirement; if the slot is free, it removes the pending head, assigns it active, invokes the executor, and leaves the descriptor active until a future tick reaches the recorded timestamp.

For the canonical valid 64-byte host-to-SRAM case with SRAM bandwidth accounting disabled:

```text
engine cycle 0: accepted and pending; bytes unchanged
engine cycle 1: selected; bytes copied; completed flag true; timestamp = 53
engine cycles 2..52: active slot remains occupied
engine cycle 53: channel retires descriptor
```

The copy, flag write, and timestamp calculation occur within one C executor call. This evidence cannot resolve a finer sub-call issue time. Direct host visibility at cycle 1 is not a command dependency, coherent memory event, or interrupt.

### Failed executor paths

Bounds, null-pointer, direction, or type errors can return before setting `completed` or `cycles_completed`. Channel control nevertheless treats traversal or timestamp eligibility separately from outcome.

A controlled descriptor requests eight bytes at offset 60 in a 64-byte SRAM region. The descriptor executor rejects it before copying. The observed states are:

| Path | Descriptor flag/timestamp | Channel behavior | Engine transfers |
|---|---|---|---:|
| synchronous submit | false / 0 | `total_completed` increments | 0 |
| tick-driven | false / 0 | remains active after selection; next tick retires timestamp zero and increments counter | 0 |
| flush | false / 0 | `total_completed` increments | 0 |

Thus channel `total_completed` is an outcome-blind traversal/retirement count, not proof of successful delivery. The descriptor has no explicit error-status field that repairs this ambiguity.

## 10.6 Queue heads and descriptor chains do not compose

The channel queue and descriptor chain reuse the same `next` pointer. This makes two individually plausible structures non-composable.

### Chain followed by another submitted head

Start with:

```text
chain: a0 -> a1
channel after submit(a0): head = a0, tail = a0
```

The tail records the submitted head, not the chain tail. Submitting `q` executes:

```text
tail->next = q
```

which overwrites `a0.next`. The graph becomes:

```text
a0 -> q       a1 disconnected
```

### Submit while a chain head is active

After selecting `b0` from `b0 -> b1`, the engine can have:

```text
active = b0
head   = b1
tail   = b0     // stale relative to pending head
```

Submitting `q` writes `b0.next = q`. The new descriptor is not reachable from pending `head=b1`.

### Counter consequences

A three-node synchronous chain produces:

```text
total_submitted = 1 head
total_completed = 3 traversed nodes
queue_depth = 1 - 3 mod 2^32 = 4,294,967,294.
```

Submission/completion ratios and queue-depth utilization are therefore meaningless for chains. Generic engine destruction is also unsafe for active chains that alias pending nodes: pending traversal can free a node and recursive destruction can reach it again.

### Safe subset

At this pin, the defensible subset is:

- independent one-node descriptors;
- caller-held borrowed objects through executor use;
- caller-proven full spans, indices, and unchecked arithmetic;
- queue capacity interpreted in submitted heads;
- explicit ticks or flush with path-specific outcome checks;
- no caller destruction or engine reinitialization while work is pending/active;
- on rejection, submission has already destroyed the chain, so the caller must not access or free it;
- for accepted work, explicit cleanup only after synchronous return or asynchronous retirement and after proving that no pending, active, or corrupted-graph alias remains;
- effective direct-initializer channel count no greater than `TU_DMA_CHANNELS`.

Chains may be studied synchronously in isolation, but they must not be combined with another same-channel submission, generic queue ratios, flush assumptions, or generic destruction.

## 10.7 Service estimates are not elapsed transfer time

For audited linear/strided/scatter/gather descriptors, the pinned service estimate has the form:

```text
C_service = TU_LATENCY_DRAM_READ
          + ceil(total_bytes / TU_DMA_BUS_WIDTH_BYTES)
          + C_sram.
```

With compiled defaults:

```text
TU_LATENCY_DRAM_READ = 50 model cycles
TU_DMA_BUS_WIDTH_BYTES = 32 bytes.
```

A direction sweep shows that descriptor store uses the read-latency macro on this path. The compiled read and write latency constants both happen to equal 50, but equal values do not make their producers interchangeable. The name of either constant must not be upgraded into a calibrated DRAM read/write model.

With SRAM bandwidth accounting disabled:

| Bytes | Service estimate |
|---:|---:|
| 0 | 50 |
| 1 | 51 |
| 31 | 51 |
| 32 | 51 |
| 33 | 52 |
| 64 | 52 |
| 65 | 53 |

The 64-byte tick-driven example is selected at engine cycle 1 and receives `cycles_completed = 1 + 52 = 53`. This future timestamp governs active-slot occupancy. It does not delay the host copy until cycle 53.

Counter units remain distinct:

| Counter/field | Unit and producer |
|---|---|
| channel `queue_depth` | submitted heads on enqueue, traversed nodes on selected decrements |
| channel `total_submitted` | accepted submitted heads |
| channel `total_completed` | sync/flush traversed nodes or async retired active nodes, outcome-blind |
| engine `total_transfers` | executor-accounted descriptors |
| engine/channel `total_bytes` | descriptor `total_bytes` after accounting |
| engine `estimated_cycles` | sum of descriptor service estimates |
| descriptor `cycles_completed` | engine-cycle eligibility timestamp on successful accounted paths |
| descriptor `cycles_issued` | inert at the pin |

Queue wait, active occupancy, per-descriptor service, and accumulated service sum are not interchangeable. `estimated_cycles` is not one wall-clock makespan.

## 10.8 What the SRAM bandwidth term means

The descriptor executor can call the generic SRAM bank-budget model described in Chapter 9. For a 1024-byte contiguous transfer at pinned defaults:

```text
bank_count = 32
bank_width = 4 bytes
words_per_cycle budget = 1 per bank
stall penalty = 2 model cycles
modeled words = 1024 / 4 = 256
initially served words = 32
stalled words = 224

C_service,bw = 50 + ceil(1024/32) + 224 × 2
             = 50 + 32 + 448
             = 530 model cycles.
```

Turning SRAM bandwidth modeling off produces 82 cycles. Two same-tick descriptors produce 530/530 when they target one shared region and 530/530 when they target separate regions. The result shows that the selected per-descriptor budget changes the estimate. It does not show realistic shared-fabric contention or independence. Channel loop order also does not create an observed estimate difference in this case.

Two channels can be selected into the C executor during one engine tick. This is parallel executor dispatch in one tick call, not evidence that bytes traverse a shared physical fabric simultaneously.

This is an **Analytical model** implemented in executable accounting and remains **Estimated**: it is not calibrated against RTL or silicon. No descriptor-engine call reaches the standalone DRAM model. Physical throughput, sustainable bandwidth, energy, and overlap cannot be derived from these numbers.

## 10.9 Channel and configuration boundaries

### Fixed channel-array safety

The engine stores:

```text
channels[TU_DMA_CHANNELS]
TU_DMA_CHANNELS = 3.
```

`tu_dma_init_full()` maps a zero channel request to the compiled default and clamps positive requests only above eight. It then iterates through the effective count. Therefore:

```text
safe effective num_channels <= 3
zero request -> 3
requests 4..8 -> unsafe out-of-array initialization
requests above 8 -> clamp to 8 -> likewise unsafe.
```

The unmodified pipeline test requests four channels and is intentionally not executed. This is not merely a test defect; it is a public initializer safety invariant.

### Parsed configuration does not become active DMA state

The JSON parser stores nondefault values for:

- bus width;
- maximum burst bytes;
- channel count;
- maximum outstanding depth;
- asynchronous mode;
- multicast enable.

The canonical probe parses 128-bit width, 32-byte burst, one channel, depth two, async enabled, and multicast disabled. All six appear in `tu_config_t`. Yet `tu_runtime_config_t` has no DMA fields, `tu_config_to_runtime()` omits them, and top-level initialization uses compile-time constants. Active state remains synchronous, three channels, depth four, and 256-bit bus width. A direct `tu_dma_init_full(true,1,2)` does activate async mode, one channel, and depth two.

This is the same configuration lesson as Chapter 4:

```text
parsed value != propagated value != active state != demonstrated effect.
```

Direct initialization is not a workaround for the safety rules: effective channel count must remain at most three, and the engine must be quiescent before reinitialization.

## 10.10 Ordinary-operation reachability and split state

Focused descriptor tests establish local behavior. Ordinary Tusim operations expose a narrower path:

- public W and A loads use legacy raw-copy DMA wrappers;
- public O store uses a legacy wrapper;
- public O load bypasses legacy DMA;
- command-queue DMA operations route through fixed wrappers;
- ordinary operations do not accept general descriptor geometry;
- descriptor execution does not call the standalone DRAM model;
- address-generator chain helpers are not ordinary operation routing;
- pipeline-controller submission is a bounded consumer, not proof of correct overlap.

There is also a state split. Wrapper execution updates process-global `g_tu_dma`, while top-level cycle accumulation samples embedded `g_tu.dma`. In the canonical probe, a 64-byte public W load increments top-level bytes by 64 and live global DMA estimate by 52, but changes embedded DMA and top-level elapsed-cycle fields by zero.

Static archive membership establishes linkability. Focused tests establish named local semantics. Only a traced call path plus discriminating state proves integration. Timeloop's separation of workload, architecture, mapping, and constraints is useful methodology here; it does not validate Tusim's counters ([PAR19](../../references/foundations.md#par19-timeloop)).

The engine is the process-global singleton `g_tu_dma`. The pin does not provide independent descriptor-engine state per core or per `tu_state_t` instance.

### Adjacent mechanisms remain bounded or deferred

The focused address-generator suite reports 12/13: its transposed case returns `0x10c` where the expected address is `0x110`. A separate range helper can return a logical address count larger than the caller-provided storage capacity. These findings bound the helper API; they do not prove that address generation is generally correct or generally incorrect.

The bounded pipeline probe also does not establish valid DMA-to-shadow overlap. In the observed sequence, DMA wrote the old active storage, the swap then exposed stale data as active, and the intended new tile was not established. This rejects overlap correctness and speedup at the pin. It does not replace the unexecuted pipeline suite or justify a broader pipeline redesign in this chapter.

## 10.11 Reproduce and interpret the evidence

From the book root:

```bash
bash experiments/run_ch10_data_movement_audit.sh
python3 experiments/ch10_predraft_validate.py
```

The runner creates, finalizes, and verifies the exact run it reports. The canonical committed snapshot is:

```text
experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard/
```

See the [audit report](../../experiments/ch10-dma-descriptor-audit-2026-07-27.md), [framing plan](../../notes/chapter-10-framing-and-evidence-plan.md), [claim ledger](../../notes/chapter-10-source-and-claim-ledger.md), and [skeptical-review dispositions](../../notes/chapter-10-skeptical-review-dispositions.md).

### Evidence-family results

| Family | Result | Correct interpretation |
|---|---:|---|
| descriptor DMA | 10/10 reported cases | named functional/accounting behavior |
| scatter/gather | 15/15 | focused in-bounds forms |
| multicast | 10/10 | includes expected invalid-target skip behavior |
| address generator | 12/13 | transposed case returns `0x10c`, expected `0x110` |
| double buffer | 10/10 | standalone component behavior only |
| command queue | 9/9 | fixed wrapper routing |
| CModel | 19/19 | ordinary functional path |
| configuration | 20/20 observed | harness is not fail-closed because its macro can return zero on failure |
| pipeline | not executed | four-channel request is unsafe against the three-entry array |
| Chapter 10 probes | zero failures | fail-closed named contract cases |
| source audit | 65/65 | 33 exact source hashes plus 32 structural predicates |

These are heterogeneous evidence families, not one numerator/denominator. The canonical result `AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS` means snapshot conformance: it includes the known address-generator failure and intentional pipeline skip and is not a correctness, integration, performance, or calibration certificate.

The corruption guard pins the complete extended-probe SHA-256 and separately checks the isolated child structure. This prevents a regenerated manifest from silently admitting reinitialization, DMA cleanup, traversal loops, or misplaced ticks into those hazardous cases.

## 10.12 Safety boundaries

1. **Bounds are not uniformly failure-atomic.** The controlled descriptor error case returns before copying, but public wrapper and low-level SRAM bounds reporters are void and may continue toward memory access. Unsafe public overflow is kept static.
2. **Stride and index coverage is incomplete.** `total_bytes` does not prove full addressed span; scatter/gather indices require caller validation.
3. **Arithmetic can wrap.** Geometry and address products/sums use `uint32_t` without checked arithmetic.
4. **Chains and queues share linkage.** Do not combine a chain with another same-channel head or generic queue/destruction assumptions.
5. **Reinitialization is destructive overwrite.** Do not reinitialize pending or active engine state.
6. **Channel count can exceed storage.** Do not request effective counts above three at this pin.
7. **Multicast completion is not all-target success.** Invalid targets can be skipped while the flag and requested accounting still advance.
8. **Error retirement is outcome-blind.** A failed async executor can retire on timestamp zero at the next tick.
9. **The pipeline suite is unsafe.** It remains unexecuted; a bounded one-channel probe is not replacement coverage.
10. **The address-generator failure remains real.** The transposed focused case is not hidden or repaired in the pinned source.

These findings are development constraints, not instructions to patch the authoritative Tusim checkout during book reproduction.

## 10.13 Multi-objective descriptor choices

| Choice | Potential gain | Costs and risks | Best-fit pinned regime |
|---|---|---|---|
| linear descriptor | simplest geometry and validation | no native row/depth gaps | contiguous one-node transfer |
| 2D/3D strided | fewer explicit descriptors for regular layouts | full span and overflow proof required | regular padded tensors |
| scatter/gather | represents irregular indices | borrowed index lifetime; duplicate/unique-byte ambiguity | bounded validated sparse events |
| multicast | one source description for fanout | requested versus delivered divergence; copied arrays and borrowed regions | all targets prevalidated |
| synchronous mode | simple caller ordering | submit call executes work; chain counters diverge | isolated one-node transfers or isolated synchronous chain study |
| tick-driven mode | explicit active-slot occupancy | no scheduler/dependency event; caller must tick and retire | controlled engine experiments |
| deeper queue | more accepted heads | no physical overlap proof; chain linkage hazard | independent one-node descriptors only |
| more channels | multiple channel states | fixed array of three; loop order is not fabric concurrency | one to three validated channels |
| SRAM bandwidth term | sensitivity to bank budget | immediate copy; no shared-fabric queue/calibration | scoped service-estimate study |
| legacy wrapper | ordinary-operation reachability | fixed geometry and split cycle state | W/A load and O store compatibility path |

No row is universally best. The regime includes geometry, number of live descriptors, caller lifetime control, synchronization mechanism, queue capacity in heads, target validation, desired fidelity, and verification cost. The chapter has no evidence for selecting the fastest physical DMA, minimizing area/power, or proving compute overlap.

## 10.14 Fidelity box

> **Executable:** linear, 2D, 3D, scatter/gather, multicast, sync/tick, controlled error, queue-corruption, config, and bank-budget cases named in the canonical static-linked probes.
>
> **Integrated:** fixed legacy W/A load and O store wrappers plus command-queue routing. General descriptors, address-generator routing, descriptor-to-DRAM timing, dependency signaling, and valid compute overlap are not integrated into ordinary operations at the pin.
>
> **Functional model:** audited in-bounds bytes move according to named descriptor geometry. Direct host observation is not coherent-memory or command-readiness evidence.
>
> **Analytical model / Estimated:** descriptor service formulas and SRAM penalty sums use model cycles and are not calibrated against RTL or silicon. Copy timing and active-slot occupancy are separate.
>
> **Calibration:** none for physical DMA latency, sustainable bandwidth, concurrency, area, power, energy, or end-to-end DMA-plus-compute performance.

## 10.15 Common failure modes

1. **Submitted means delivered.** Acceptance only establishes channel linkage.
2. **Completed counter means success.** Channel completion is outcome-blind on controlled error paths.
3. **Timestamp means copy time.** Successful copies occur during selection; the future timestamp controls retirement.
4. **Async means concurrent hardware.** It means tick-driven engine state here.
5. **Queue depth counts work.** It counts heads on admission and can decrement per chain node.
6. **Chain plus queue is composable.** One `next` pointer serves both structures.
7. **Engine owns everything after submit.** Rejection, pending use, successful return, and cleanup have different rules.
8. **Reinit cleans up.** It zeroes singleton state and can orphan live allocations.
9. **Accepted channel count is safe.** The initializer accepts values beyond fixed storage.
10. **Logical bytes equal span.** Strides, indices, duplicates, and fanout change the relevant quantity.
11. **Multicast completion means every destination succeeded.** Invalid targets can be skipped.
12. **Field means behavior.** Priority, signal, and issue timestamp are inert on the descriptor engine path.
13. **Parsed config means active config.** DMA fields stop before runtime initialization.
14. **Linked means integrated.** Archive membership and focused tests do not prove ordinary-operation reachability.
15. **Estimated cycles equal elapsed time.** Wait, service, occupancy, sum, and top-level counters differ.
16. **Equal channel estimates prove no contention.** The modeled experiment does not implement a physical shared fabric.
17. **A bounded pipeline probe replaces the suite.** It does not; the unsafe suite remains skipped.

## 10.16 Development questions

1. Should chain linkage and queue linkage use separate fields or container nodes?
2. Should admission capacity count heads, descriptor nodes, bytes, or outstanding service?
3. Which explicit descriptor outcome states are required: accepted, running, succeeded, partially delivered, failed, canceled?
4. Should `signal_id` feed a completion registry and command dependency graph?
5. Should `cycles_issued` record selection, enqueue, or transport start?
6. How should reinitialization reject nonquiescent state or reclaim it safely?
7. Should channel storage be dynamic, or should initialization reject values above `TU_DMA_CHANNELS`?
8. What checked-arithmetic API can validate full 2D/3D spans and scatter/gather indices before execution?
9. Should multicast account requested, delivered, and failed fanout separately?
10. Which single event timeline connects DMA, SRAM, DRAM, command queues, and compute?
11. What arbitration, backpressure, and shared-fabric state are required for a concurrency claim?
12. How should parsed DMA configuration propagate into active state and demonstrable behavior?
13. Should ordinary operations accept general descriptors, or should a compiler lower them into fixed wrappers?
14. What reference—RTL, FPGA, silicon, or trace-calibrated simulator—would calibrate service estimates?

## Summary

- Descriptor selection begins with representability, span safety, borrowed-object lifetime, and caller-managed ordering—not with a presumed asynchronous speedup.
- Linear, strided, scatter/gather, and multicast forms use different copied, accounted, unique, span, and fanout byte quantities.
- Host buffers, index lists, SRAM regions, and multicast sources are borrowed; selected multicast arrays are copied into descriptor-owned storage.
- Synchronous submission executes in the submit call; tick-driven submission copies at selection and retires later by timestamp.
- Channel completion counters can advance after executor failure and are not success predicates.
- Queue heads and chains reuse `next`, causing disconnection, unreachable nodes, counter divergence, and unsafe destruction.
- The pinned service estimate is `50 + ceil(bytes/32) + SRAM penalty` model cycles; it is not calibrated elapsed transfer time.
- A 1024-byte bandwidth-enabled case estimates 530 cycles from 82 base cycles plus 448 bank penalties; shared/separate equality is not a physical contention result.
- Parsed DMA configuration does not reach top-level initialization; direct initialization remains bounded by a fixed three-entry channel array.
- Reinitialization overwrites singleton state without teardown and must not occur with pending or active descriptors.
- Ordinary operations expose fixed legacy wrappers, not general descriptor geometry or descriptor-to-DRAM timing.
- The chapter supports carefully scoped functional and accounting studies, not physical throughput, overlap, area, power, or energy claims.

## Review questions

1. Why does a nonzero descriptor ID not authorize dependent compute?
2. How do copied bytes and addressed span differ for a 2D descriptor?
3. Which scatter/gather objects are borrowed?
4. Why can `completed` and channel `total_completed` support different conclusions?
5. When are bytes visible and when does the channel retire in the 64-byte tick example?
6. Why can a descriptor chain underflow queue depth?
7. What does the 530-cycle result model and omit?
8. Why are direct channel requests 4–8 unsafe?
9. Where do parsed DMA settings stop propagating?
10. What evidence would be needed to claim physical overlap?

### Review-question answer key

1. It proves admission of a submitted head, not selection, successful execution, dependency signaling, or retirement.
2. Copied bytes are `rce`; span includes inter-row gaps as `(r-1)s_r + ce` for nonzero dimensions.
3. The source/destination host storage as applicable, index list, and SRAM region objects remain caller-owned through execution.
4. The descriptor flag is path-specific, while the channel counter counts traversal/retirement and advances on controlled failures.
5. Bytes become directly host-observable during selection at engine cycle 1; the active slot retires at timestamp cycle 53.
6. Admission increments once per submitted head, while synchronous chain traversal decrements once per node.
7. It sums a 50-cycle named constant, 32 bus beats, and 224 two-cycle SRAM bank-budget penalties; it omits calibrated transport, queueing, and shared-fabric behavior.
8. Storage has three entries, but initialization clamps only above eight and loops through the effective count.
9. They are stored in `tu_config_t` but omitted from `tu_runtime_config_t` and `tu_config_to_runtime()`; top-level init uses constants.
10. A coupled event model with dependency consumers, arbitration, shared-resource occupancy, calibrated timing, and a traced ordinary-operation path.

## Design exercises

1. **Descriptor selector.** Given five tensor layouts, choose linear, 2D, 3D, or scatter/gather forms and prove every span using checked arithmetic.
2. **Ownership protocol.** Specify an API that makes rejection, pending ownership, success, failure, and reclamation unambiguous.
3. **Queue redesign.** Separate chain and queue links; define invariants and tests for active, pending, cancel, flush, and destroy.
4. **Completion model.** Add explicit status and delivered-byte fields; define multicast partial failure.
5. **Channel validation.** Design fail-closed initialization for static and dynamic channel storage, including zero/default semantics.
6. **Config propagation.** Carry all six parsed DMA fields into active state and add one discriminating effect test per field.
7. **Timeline coupling.** Define events connecting descriptor selection, SRAM service, DRAM transport, command dependencies, and compute readiness.
8. **Calibration plan.** Choose a named RTL or hardware reference, workloads, clocks, error metric, and uncertainty report for DMA service.
9. **Compiler lowering.** Lower a 3D tensor copy into descriptors while proving borrowed-object lifetimes and queue-head capacity.
10. **Regression mutation.** Propose safe source mutations that the source audit, manifest, and corruption hash guard must reject.

## Primary references

- **[SMI84]** James E. Smith, “Decoupled Access/Execute Computer Architectures,” *ACM Transactions on Computer Systems*, 1984. DOI: [10.1145/357401.357403](https://doi.org/10.1145/357401.357403).
- **[GEN21]** Hasan Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” DAC 2021. DOI: [10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216).
- **[JOU17]** Norman P. Jouppi et al., “In-Datacenter Performance Analysis of a Tensor Processing Unit,” ISCA 2017. DOI: [10.1145/3079856.3080246](https://doi.org/10.1145/3079856.3080246).
- **[PAR19]** Angshuman Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019. DOI: [10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042).
