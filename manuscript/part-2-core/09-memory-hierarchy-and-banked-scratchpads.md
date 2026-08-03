# Chapter 9 — Memory Hierarchy and Banked Scratchpads

> **Edition scope.** This chapter describes Tusim at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. It distinguishes capacity, placement, bank mapping, service budgets, latency accounting, and operation integration. A linked memory-hierarchy module or a field named `read_latency` does not imply that direct MMA executes through that hierarchy or charges that latency.

## Learning objectives

After this chapter, you should be able to:

1. distinguish a software-managed scratchpad from a hardware-managed cache;
2. calculate W, A, and O working-set bytes for Tusim's direct MMA contract;
3. separate capacity, traffic, bandwidth, latency, bank conflicts, and utilization;
4. derive Tusim's byte-address-to-bank mapping;
5. reproduce the pinned per-bank budget and refill behavior;
6. explain why a returned stall penalty is not a queued-access simulation;
7. trace parsed memory settings into effective W/A/O storage and banking;
8. distinguish library linkage, focused execution, and direct-operation integration;
9. identify raw-pointer paths that bypass SRAM counters and budgets;
10. choose defensible memory experiments without claiming physical SRAM or end-to-end calibration.

## Prerequisite graph

```text
Chapter 4: requested configuration -> effective runtime state
                              |
Chapter 6: O[M,N] += W[M,K] A[K,N]; callers must provide valid extents
                              |
Chapter 7: logical dataflow != executed physical movement
                              |
Chapter 8: W/A are 2-byte FP16; O is 4-byte host float
                              v
       capacity -> placement -> bank map -> service -> integration
            |          |           |          |           |
            +----------+-----------+----------+-----------+
                                   |
                                   v
                 defensible memory-system conclusion
```

Chapter 6 established the direct-MMA byte footprints:

```text
W bytes = 2 M K
A bytes = 2 K N
O bytes = 4 M N
```

Internal PE tiling partitions computation but does not stream partial operands through the direct call. Chapter 7 then showed that WS, OS, and RS have logical stationary narratives but execute the same scalar array accesses. Chapter 8 fixed the storage widths. Chapter 9 asks where those bytes reside, which accesses are metered, and whether a memory result belongs to the operation being compared. “Must fit” is a caller safety precondition: the pinned DMA and MMA checks report overflow but do not reject execution.

## Opening architecture question: fitting is not feeding

Suppose W, A, and O fit in 256 KiB of on-chip SRAM. Is the accelerator compute-bound?

No. Capacity answers whether bytes can reside somewhere. It does not establish enough banks, ports, or transfer bandwidth; a favorable layout; overlap with computation; or even that the compute path uses the modeled memory API. Conversely, an analytical bandwidth limit does not prove a specific latency because queues, arbitration, dependencies, and overlap can change request service.

A useful pre-spec model must keep at least five contracts separate:

1. **capacity and placement** — which bytes can reside at which level;
2. **mapping** — which address selects which bank;
3. **service** — how many requests or bytes a level accepts over an interval;
4. **accounting** — which counter or formula reports cost and in what cycle domain;
5. **integration** — whether the target operation actually traverses that path.

Tusim implements pieces of all five, but not as one coherent direct-MMA hierarchy at the pinned revision.

## 9.1 Scratchpads, caches, and explicit responsibility

A cache decides placement and replacement in hardware using tags and a policy. A scratchpad exposes addressable storage and leaves placement, movement, and lifetime to software or a compiler. That explicit control can improve predictability and avoid tag/replacement overhead, but it transfers correctness and performance responsibility to mapping software. Banakar et al. provide the architectural distinction; their old-node quantitative results do not transfer to Tusim ([BAN02](../../references/foundations.md#ban02-scratchpad-memory)).

Tensor accelerators favor software-managed storage because tensor shapes and tile schedules expose reuse. Yet “software managed” does not mean “free.” A compiler must decide:

- which W, A, and O tiles are simultaneously live;
- whether a tile is reused before eviction;
- which bank each access reaches;
- whether transfers overlap compute;
- whether a wider or larger memory repays its area and energy cost.

Production TPU evidence shows that on-chip storage, software, workload mix, and latency requirements jointly affect achieved performance, but its silicon measurements are not Tusim constants ([JOU17](../../references/foundations.md#jou17-production-tpu-analysis)). Eyeriss demonstrates hierarchy-aware reuse for convolution, not a universal proof that one dataflow or storage layout wins ([CHE16](../../references/foundations.md#che16-eyeriss)).

## 9.2 Capacity, traffic, bandwidth, and latency

These quantities answer different questions:

| Quantity | Question | Typical unit |
|---|---|---|
| capacity | how many bytes can reside? | B, KiB, MiB |
| traffic | how many bytes cross a named boundary? | B |
| bandwidth | how many bytes can cross per time? | B/cycle or B/s |
| latency | how long does one dependency or operation take? | cycles or seconds |
| occupancy | how much capacity is allocated or live? | B or fraction |
| utilization | how much modeled service capacity was used? | fraction over an interval |
| stall accounting | what penalty did a model attribute? | cycles in a named domain |

For a direct MMA, placement is constrained by three independent regions and offsets:

```text
2MK <= W_capacity - w_offset
2KN <= A_capacity - a_offset
4MN <= O_capacity - o_offset.
```

Their aggregate footprint is:

```text
B_working = 2MK + 2KN + 4MN.
```

The aggregate is necessary but not sufficient: 200 KiB can be below the 256 KiB total yet overflow the 64 KiB A or O partition. These inequalities are required extents, not fail-closed admission checks. If W is loaded once and reused across several A matrices, host-to-W traffic can be lower than repeatedly counting the footprint. If O is initialized and later stored at a host/direct-SRAM boundary, O alone contributes 8MN transferred bytes even though its resident footprint is 4MN. Every traffic claim needs a boundary and lifetime.

The Roofline model bounds attainable performance by compute peak and bandwidth multiplied by operational intensity ([WAT09](../../references/foundations.md#wat09-roofline-model)):

```text
attainable rate <= min(compute peak, bandwidth × operations/byte).
```

For one explicitly scoped host/direct-SRAM lifetime that loads W and A, initializes O, and stores O once,

```text
T_host = 2MK + 2KN + 8MN bytes
OI_host = 2MNK / T_host operations/byte
OI_crossover = compute_peak / host_bandwidth.
```

Tusim counts two operations per MAC here. `OI_host < OI_crossover` identifies the bandwidth-limited side of this upper-bound model; it still does not predict latency or bank aliases. Changing the boundary, reuse lifetime, or O initialization changes the denominator. Timeloop and MAESTRO similarly separate workload, architecture, mapping, and constraints when deriving reuse and traffic; their methodology motivates that separation but does not validate Tusim's counters ([PAR19](../../references/foundations.md#par19-timeloop), [KWO19](../../references/foundations.md#kwo19-maestro)).

## 9.3 Tusim's three memory surfaces

The pinned source exposes three related but incompatible surfaces.

### Direct W/A/O SRAM

`g_tu` owns three `tu_sram_region_t` objects. Their default capacities are:

| Region | Capacity | Direct-MMA stored type |
|---|---:|---|
| W | 128 KiB | FP16, two bytes |
| A | 64 KiB | FP16, two bytes |
| O | 64 KiB | host `float`, four bytes on the audited build |

Runtime W/A/O capacities propagate through `tu_runtime_config_t`. The direct DMA wrappers and operator paths access these regions through a mixture of bulk SRAM calls and raw pointers.

### Standalone four-level hierarchy

`tu_memory_hierarchy_t` names:

1. RegFile (L0);
2. LocalSPAD (L1);
3. GlobalBuf (L2);
4. DRAM (L3).

It owns RegFile activity state, a 1 MiB GlobalBuf, and a DRAM model; callers supply LocalSPAD regions. It records per-level reads, writes, bytes, and stalls.

The hierarchy object is compiled into `libtucmodel.a`, aggregate-listed through `test-memhier`, and passes 10/10 focused tests. An enforced call-site audit nevertheless finds `tu_mem_hierarchy_*` calls only in `memory_hierarchy.c` and `test_memory_hierarchy.c`. Neither `tu_cmodel.c` nor `tu_core.c` drives direct MMA through it. The correct label is **executable standalone API at compiled defaults**, not **integrated direct-MMA hierarchy**.

### Source-present cycle/performance bank model

`tu_cmodel/perf/cycle_model.[ch]` defines another `tu_bank_model_t`, its own clock, budget, conflict producer, and tile-execution API. Cycle-model tile execution selects each operand's starting bank as `byte_address % num_banks`, without dividing by bank width, then charges the whole tile to that bank. This differs from generic SRAM interleaving. `cycle_model.o` is absent from `TU_OBJS`, no Make target builds `tests/test_cycle_model.c`, and direct MMA does not call it. It is **source-present, focused-test-source-present, but not library or direct-MMA integrated** at this snapshot.

### Compact source map

| Pinned path | Role | Integration boundary |
|---|---|---|
| `tu_cmodel/tu_sram.[ch]` | generic byte storage, banks, budget/refill, raw pointer | used by direct buffers, but raw access bypasses accounting |
| `tu_cmodel/memory/memory_hierarchy.[ch]` | standalone RegFile/LocalSPAD/GlobalBuf/DRAM dispatch | implementation and focused-test call sites only |
| `tu_cmodel/perf/cycle_model.[ch]` | separate bank/tile timing model | source present; absent from `TU_OBJS` and direct MMA |
| `tu_cmodel/infra/config.c` | parse and runtime conversion | capacities cross; banking does not |
| `tu_cmodel/tu_cmodel.c` | direct allocation, DMA wrappers, MMA raw-pointer path | authoritative direct-operation path |
| `tests/test_memory_hierarchy.c`, `tests/test_config.c` | focused assertions | hierarchy test gates normally; config harness is not fail-closed |

## 9.4 Bank mapping

Generic SRAM construction uses 32 banks and a four-byte bank word. The mapping is:

```text
bank(addr) = floor(addr / bank_width) mod bank_count
           = floor(addr / 4) mod 32     // pinned generic defaults
```

For aligned word starts, byte addresses 0–3 select bank 0, 4–7 select bank 1, and 128–131 wrap to bank 0. This interleaving spreads sequential words across banks but maps a 128-byte stride back to the same bank. A physical byte transaction `[addr, addr+bytes)` may intersect more than one aligned bank word; the implementation instead meters `ceil(bytes/bank_width)` starts at `addr + i*bank_width`. For example, four bytes at address 2 physically span words 0 and 1 but are metered once from start address 2. Chapter evidence and bank-stride conclusions therefore apply to aligned transfers.

Increasing banks can expose more parallel service but costs decode, wiring, arbitration, and verification. Increasing bank width moves more bytes per accepted word but can waste service on narrow accesses and changes alignment. Padding or swizzling may remove a hot-bank stride while increasing footprint and compiler complexity.

A bank equation alone does not establish conflicts. A conflict requires simultaneous or interval-overlapping requests under a specified port model. Tusim's pinned low-level module has a `conflicts` field and prints it, but `tu_sram.c` never increments it. The Chapter 9 probe observes zero low-level conflicts even when it repeatedly exhausts one bank. The separate source-present cycle model does increment its own `conflict_count` under a different mapping and interval. Neither counter belongs to direct MMA. Reported budget stalls and either conflict domain must not be treated as synonyms.

## 9.5 The effective bandwidth-budget model

Each bank stores `words_available`. An accepted access decrements it. Once it reaches zero, later accesses return a fixed `stall_penalty`. Explicit `tu_sram_advance_cycle()` triggers a refill when the configured window has elapsed.

The default names suggest “one word per cycle,” but the effective state machine initializes one available word and refills it every four advanced cycles. For the exact implementation, the sustained accepted budget under regular advancement is closer to:

```text
accepted words per bank per refill interval = words_per_cycle
```

not `words_per_cycle × refill_window`. Names and comments do not override state transitions.

The probe uses one word, a four-cycle window, and a three-cycle penalty. Writes to addresses 0, 0, and 4 return `0,3,0`: bank 0 is exhausted on the second access, while bank 1 still has budget. Three advanced cycles do not refill; the fourth does.

Crucially, the stalled write still copies data immediately. The returned three cycles are an attached accounting penalty. There is no request queue, waiter, requester identity, service completion event, or backpressure. Repeated exhausted accesses can each add the same penalty without advancing time. This is **executable functional accounting behavior; estimated and uncalibrated**. No lower- or upper-bound relationship to physical latency is established.

Bandwidth utilization has an internal interval defect. Banks begin with an initial budget, but the denominator counts only `current_cycle / refill_window` periods. After service in the initial and first refilled windows, a bank can have two served words over a denominator of one; the API clips the resulting value to 1.0. Different histories can therefore collapse to 100%. This metric is unsafe for comparative conclusions until its endpoints and initial window are repaired.

## 9.6 Arbitration and latency fields are not behavior

`tu_sram_init_bw()` retains an arbitration enum. The documentation names none, round-robin, and fixed priority. The implementation has no branch on that field. Identical write/write/read sequences under all three modes return ten total penalty cycles. Round-robin state, requester ordering, and read-over-write priority are absent.

Likewise, hierarchy configurations contain base read and write latency fields. Generic SRAM access does not charge them. The LocalSPAD path sums returned budget penalties; GlobalBuf does the same; RegFile returns zero; DRAM delegates to its own model. A table containing `read_latency = 4` is not evidence that an access costs four cycles.

This distinction is important for architecture exploration. A parameter is useful only if it completes an evidence ladder:

```text
declared -> initialized -> consumed -> observable effect -> tested
```

At the pinned revision, several memory parameters stop before consumption.

## 9.7 Requested versus active memory configuration

The canonical JSON parser recognizes W/A/O capacities, bank count, bank width, conflict mode, and other memory fields. Full-config validation checks bank width and count. Conversion to `tu_runtime_config_t` copies W/A/O capacities but not bank count or width. Generic SRAM construction then assigns compiled `TU_SRAM_BANKS` and `TU_SRAM_BANK_WIDTH`.

The executable fixture requests:

```text
W/A/O = 16/8/12 KiB
banks = 8
bank width = 8 B
```

Initialized direct storage becomes:

```text
W/A/O = 16/8/12 KiB
banks = 32
bank width = 4 B
```

The capacities are source-proven to control allocation and recorded region sizes; the 1×1×1 workload does not prove a capacity-sensitive behavioral boundary, and failure-open checks make overflow a caller precondition. Banking is parse-only on this path. Canonical JSON has no GlobalBuf parsing block: its struct defaults are neither a parsed request nor a runtime conversion result. This qualifies documentation that calls banking fully runtime configurable.

The hierarchy has a separate override problem. Its header says to call `tu_mem_hierarchy_set_level_config()` before initialization. Initialization immediately zeroes the object and reinstalls defaults. The probe's pre-init 2 KiB GlobalBuf request becomes the compiled 1 MiB, 16-bank, eight-byte-word GlobalBuf. Intended API sequence and executable sequence disagree.

## 9.8 Hierarchy semantics and cycle domains

The standalone hierarchy remains useful when interpreted exactly.

- **RegFile:** writes increment activity but store no bytes; reads zero-fill. It is an activity abstraction, not functional register storage.
- **LocalSPAD:** delegates word-by-word to a caller-supplied SRAM region.
- **GlobalBuf:** owns a banked SRAM and increments a “hit” when the address range fits. No tags, allocation, lookup, replacement, or reuse test exists; “hit” means in range.
- **DRAM:** delegates request timing to the separate DRAM model; Chapter 9 does not validate its presets.

Cycle advancement is also split. `tu_mem_hierarchy_tick()` advances the hierarchy counter and ticks DRAM. It does not call `tu_sram_advance_cycle()` on GlobalBuf or caller-owned LocalSPAD regions. The probe exhausts GlobalBuf, advances the hierarchy by four cycles, and remains stalled; directly advancing GlobalBuf SRAM refills it. `tu_mem_hierarchy_reset()` then zeros hierarchy time and selected aggregate counters but preserves GlobalBuf SRAM time, available words, refill timestamps, and per-bank counters. Reset can therefore return one clock to zero while an exhausted bank remains exhausted.

Therefore these clocks are not one timeline:

```text
hierarchy current_cycle != GlobalBuf SRAM current_cycle != direct W/A/O SRAM current_cycle
```

Counters from different domains must not be added without an explicit synchronization rule.

## 9.9 Raw-pointer bypass and operation-specific fidelity

`tu_sram_raw_ptr()` returns backing storage without incrementing reads, writes, stalls, or per-bank service. Direct MMA obtains W, A, and O through three raw-pointer calls and hands those pointers to the dataflow plug-in. The probe samples all three regions immediately around a 1×1×1 MMA and observes zero read/write-counter deltas.

This does not mean all operators bypass accounting. Softmax and normalization use low-level SRAM calls for selected accesses; pooling and elementwise use raw pointers in important paths; DMA paths vary. Memory fidelity is operation-specific.

It also explains why a direct MMA can have a nonzero dataflow cycle estimate while its SRAM bank counters show no compute traffic. The cycle formula and memory budget are parallel abstractions, not a coupled simulation. Adding hierarchy stalls to MMA cycles would fabricate integration that the source does not execute.

### Reproduce this chapter's evidence

From the book root:

```bash
bash experiments/ch09_reproduce.sh
```

See the [audit report](../../experiments/ch09-memory-hierarchy-audit-2026-07-26.md), [probe](../../experiments/ch09_memory_probe.c), [framing plan](../../notes/chapter-09-framing-and-evidence-plan.md), and [claim ledger](../../notes/chapter-09-source-and-claim-ledger.md).

## 9.10 What the focused tests prove

The archive-only run reports 10/10 top-level hierarchy test functions, 19/19 cmodel cases, and 20/20 config cases passing. These are not comparable coverage units. The config result describes this successful run but is not a fail-closed regression gate: its `CHECK` macro executes bare `return;` inside `int main(void)`, so a forced assertion can print failure and exit zero instead of reaching `test_exit()`.

The hierarchy suite verifies construction, names, aligned LocalSPAD/GlobalBuf data movement, RegFile activity, DRAM delegation, compiled on-chip-total arithmetic, reset, hierarchy ticking, and print smoke behavior. It does not assert:

- direct-MMA hierarchy integration;
- arbitration-mode differences;
- base-latency charging;
- pre-init override survival;
- GBuf refill through hierarchy tick;
- parsed-bank propagation;
- partial-word canaries;
- failure-atomic bounds handling.

One reset test even passes the GlobalBuf SRAM as a LocalSPAD region, which checks generic dispatch mechanics rather than real placement. Passing tests remain valuable; their assertions define their scope.

## 9.11 Safety boundaries

Low-level `bounds_check()` reports overflow and returns to its caller, but the caller proceeds to bank selection and `memcpy`. Direct `check_sram_bounds()` behaves the same way: DMA and MMA continue after warning-only W/A/O checks. The hierarchy header promises `-1` on bounds violation, but the implementation returns success after the unsafe low-level call; `addr + size` checks can also wrap. The chapter records these facts statically and does not execute an out-of-bounds probe. Required extent, allocated capacity, and enforced rejection are three different contracts.

Partial-word handling also deserves caution. LocalSPAD hierarchy writes preserve the tail of a word through a fixed temporary buffer and direct primary backing-store access. GlobalBuf transfers whose byte count is not a multiple of bank width perform full-word reads from or writes to the caller's host buffer and can cross its bounds. These unsafe tails remain static-only findings.

The public `tu_gbuf_init()` also allocates per-bank meter state using the compiled generic count and only afterward overwrites `bank_count` from its custom configuration. A direct custom count above 32 can make later meter indexing exceed the allocation. Safe standalone hierarchy evidence is limited to compiled defaults; changing bank geometry requires allocation-consistent construction.

These are development questions, not invitations to contaminate the pinned source during book reproduction.

## 9.12 Multi-objective memory choices

| Choice | Potential gain | Costs and risks | Best-fit regime |
|---|---|---|---|
| larger LocalSPAD | more tile reuse, fewer upper-level transfers | SRAM area/leakage, longer wires, allocation pressure | working sets just beyond a capacity threshold |
| more banks | more independent word budgets | decode/wiring/arbiter cost; stride aliases remain | parallel accesses distributed by layout |
| wider banks | more bytes per accepted word | overfetch and alignment constraints | naturally wide vector transfers |
| GlobalBuf | sharing and intermediate capacity | extra level, ownership and coherence questions | multicore/shared tensors with proven reuse |
| raw-pointer functional path | simple and fast host simulation | no bank traffic or service evidence | functional correctness only |
| deterministic budget model | cheap sensitivity study | no queues, requester order, or calibrated latency | controlled formula comparison |
| padding/swizzle | reduces specific bank aliases | extra capacity, address logic, compiler complexity | known periodic conflict patterns |

No row is universally best. The decision regime includes shape, tensor lifetime, reuse distance, access stride, simultaneous request set, precision, DMA schedule, area/power budget, compiler maturity, and desired fidelity. A larger memory can worsen physical access time; more banks can increase control cost; a layout that helps one operator may hurt another.

## 9.13 Fidelity box

> **Executable:** generic SRAM storage, bank mapping, budget/refill, returned penalties, statistics, raw-pointer access, and standalone RegFile/LocalSPAD/GlobalBuf/DRAM hierarchy APIs.
>
> **Integrated:** direct W/A/O capacities and selected DMA/engine SRAM accesses. The standalone four-level hierarchy and runtime banking request are **not integrated** into direct MMA.
>
> **Functional model:** bytes move correctly for audited aligned in-bounds paths. RegFile is activity-only; GlobalBuf “hits” are range checks.
>
> **Functional model / estimated:** exhausted banks return fixed uncalibrated penalties while copies complete immediately. Arbitration requester order, queues, backpressure, and base SRAM latency are not modeled; no physical bound direction is established.
>
> **Calibration:** none against physical SRAM, RTL, FPGA, or silicon. Area, power, energy, and end-to-end DMA+MMA latency are not established.

## 9.14 Common failure modes

1. **Fits means fast.** Capacity does not establish bandwidth or integration.
2. **Field means effect.** Parsed or initialized parameters may have no consumer.
3. **Linked means integrated.** A library member and focused test do not prove direct-operation reachability.
4. **Stall means delayed service.** Tusim copies immediately and returns accounting penalties.
5. **Round-robin name means arbiter.** No requester-order state exists on the audited path.
6. **Hit means cache hit.** GlobalBuf hit is only an in-range access.
7. **Conflict equals stall.** The low-level conflict counter has no producer; the separate cycle-model counter and budget stalls are different domains.
8. **One cycle counter rules all.** Hierarchy, SRAM, DRAM, DMA, and MMA domains differ.
9. **Raw pointer is free hardware access.** It is a host-model bypass, not physical bandwidth.
10. **Passing aligned tests prove byte safety.** Partial and bounds paths need dedicated checks.
11. **Traffic equals footprint.** Traffic needs a boundary and lifetime.
12. **Model utilization equals physical utilization.** It is a formula over selected counters and intervals.

## 9.15 Development questions

1. Should `tu_runtime_config_t` carry bank count, width, ports, and refill semantics into every SRAM constructor?
2. Should hierarchy configuration be passed into initialization rather than written into state that initialization erases?
3. Which single clock advances LocalSPAD, GlobalBuf, DMA, DRAM, and compute?
4. Should a stalled access wait, enqueue, or merely return an estimate—and how should APIs distinguish these modes?
5. What requester identities and fairness state are required for real round-robin or priority arbitration?
6. Should direct MMA use an access trace, analytical traffic model, or explicit SRAM requests?
7. How should GBuf residency, allocation, reuse, and replacement be represented without pretending it is a cache?
8. Which bounds errors must become fail-closed before fuzzing partial accesses?
9. How should memory action counts connect to a separately calibrated area/energy model?
10. Which cross-model workload and mapping could compare Tusim with Timeloop, MAESTRO, SCALE-Sim, or RTL without changing assumptions?

## Summary

- Capacity, traffic, bandwidth, latency, stalls, and integration are separate contracts.
- Direct MMA callers must provide complete in-bounds `2MK`, `2KN`, and `4MN` byte images; the implementation does not reject overflow safely.
- Generic SRAM maps aligned word starts as `(addr / 4) mod 32`; a separate non-integrated cycle model maps starting byte addresses modulo bank count.
- Exhausted accesses still copy immediately; returned penalties are functional accounting estimates, not queue simulation or calibrated bounds.
- The low-level conflict counter has no live producer; the separate cycle model has another producer and domain. Base SRAM latency fields are not charged by low-level access.
- Parsed W/A/O capacities determine allocations; parsed `8×8 B` banking remains compiled `32×4 B`, while overflow rejection remains failure-open.
- The four-level hierarchy is executable and focused-tested but disconnected from direct MMA.
- RegFile stores no data, GlobalBuf hits are range checks, and hierarchy ticks do not refill SRAM budgets.
- Direct MMA uses raw pointers and changes no modeled SRAM access counters.
- Tusim can support carefully scoped formula and API studies, not calibrated physical-memory or coherent end-to-end claims.

## Review questions

1. Why does a 200 KiB footprint not prove a 256 KiB scratchpad can feed the array?
2. Which boundary must accompany an operational-intensity number?
3. What address stride repeatedly selects one pinned generic SRAM bank?
4. Why is a returned stall penalty not evidence of delayed completion?
5. What evidence separates library linkage from direct-MMA integration?
6. Why can parsed banking coexist with compiled active banking?
7. Why is a GlobalBuf hit not cache evidence?
8. Which counters can safely be added without a synchronization contract?

### Review-question answer key

1. Capacity omits mapping, service, ports, overlap, and path integration.
2. Name the byte-transfer boundary and lifetime, such as DRAM-to-GBuf per operation.
3. Any stride that is a multiple of `32 × 4 = 128` bytes preserves the bank index.
4. The copy occurs immediately; only a fixed accounting value is returned.
5. Show a call path from the operation plus discriminating counter or behavior changes.
6. Parsing and runtime conversion are separate stages; bank fields are dropped before construction.
7. The implementation checks only whether the address range fits; it has no tags or replacement.
8. Only counters with the same producer, interval, clock, and scope—or an explicit conversion—may be combined.

## Design exercises

1. **Bank-layout study.** For FP16 row-major matrices, compare strides that distribute or alias 32 four-byte banks. Include padding cost.
2. **Fail-closed SRAM API.** Specify status returns and canary tests for bounds and partial words without executing undefined behavior.
3. **Trace-coupled MMA.** Design an access-trace interface that preserves functional speed while producing bounded bank traffic.
4. **Hierarchy clock.** Define one event/tick contract for LocalSPAD, GlobalBuf, DMA, DRAM, and compute.
5. **Arbitration model.** Add requester IDs, queue depth, fairness, and completion events; state verification invariants.
6. **Capacity threshold.** Sweep a workload across a LocalSPAD fit boundary while keeping mapping and byte boundary fixed.
7. **Energy study.** Combine action counts with versioned primitive energy estimates; report uncertainty and technology assumptions.

## Primary references

- **[BAN02]** Rajeshwari Banakar et al., “Scratchpad Memory: A Design Alternative for Cache On-Chip Memory in Embedded Systems,” CODES 2002. DOI: [10.1109/CODES.2002.1003604](https://doi.org/10.1109/CODES.2002.1003604).
- **[WAT09]** Samuel Williams, Andrew Waterman, and David Patterson, “Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures,” *CACM*, 2009. DOI: [10.1145/1498765.1498785](https://doi.org/10.1145/1498765.1498785).
- **[JOU17]** Norman P. Jouppi et al., “In-Datacenter Performance Analysis of a Tensor Processing Unit,” ISCA 2017. DOI: [10.1145/3079856.3080246](https://doi.org/10.1145/3079856.3080246).
- **[CHE16]** Yu-Hsin Chen, Joel Emer, and Vivienne Sze, “Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,” ISCA 2016. DOI: [10.1109/ISCA.2016.40](https://doi.org/10.1109/ISCA.2016.40).
- **[PAR19]** Angshuman Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019. DOI: [10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042).
- **[KWO19]** Hyoukjun Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” MICRO 2019. DOI: [10.1145/3352460.3358252](https://doi.org/10.1145/3352460.3358252).
