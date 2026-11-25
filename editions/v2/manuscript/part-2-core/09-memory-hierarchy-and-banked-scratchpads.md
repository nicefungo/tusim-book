# Chapter 9 — Memory Hierarchy and Banked Scratchpads

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-9)

Move the start of a four-byte read from byte 0 to byte 2. The caller still gets four bytes. Has the bank demand changed? On Tusim the answer depends on **which word meter the caller reaches**. At byte 2 the compatibility meter charges one word; the address-span meter charges two. Neither answer, by itself, tells us how long a processor would wait.

**Edition scope.** Session 6 tests the scalar and bulk SRAM APIs at public simulator `7a094ff6c5527eff8e4318de676f0c0221c448b4`. Observations marked **historical** are from the v1 Chapter 9 audit at `e918c80b6fce833cd1fcae97730fa841c2176f25`; they were not rerun. Source readings are distinguished from new measurements.

## Learning objectives

Use the working-set equations from Chapter 6, the route distinction from Chapter 7 and the storage widths from Chapter 8 to answer three questions:

1. Do the operands fit **in the regions where the operation needs them**?
2. For a given request, which banks are charged, whose grants are spent, and what bytes move?
3. Does the operation actually use that meter and its clock?

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

A cache decides placement and replacement in hardware using tags and a policy. A scratchpad exposes addressable storage and leaves placement, movement, and lifetime to software or a compiler. That explicit control can improve predictability and avoid tag/replacement overhead, but it transfers correctness and performance responsibility to mapping software. Banakar et al. provide the architectural distinction; their old-node quantitative results do not transfer to Tusim (BAN02).

Tensor accelerators favor software-managed storage because tensor shapes and tile schedules expose reuse. Yet “software managed” does not mean “free.” A compiler must decide:

- which W, A, and O tiles are simultaneously live;
- whether a tile is reused before eviction;
- which bank each access reaches;
- whether transfers overlap compute;
- whether a wider or larger memory repays its area and energy cost.

Production TPU evidence shows that on-chip storage, software, workload mix, and latency requirements jointly affect achieved performance, but its silicon measurements are not Tusim constants (JOU17). Eyeriss demonstrates hierarchy-aware reuse for convolution, not a universal proof that one dataflow or storage layout wins (CHE16).

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

The aggregate is necessary but not sufficient: 200 KiB can be below the 256 KiB total yet overflow the 64 KiB A or O partition. These inequalities assume each offset is inside its own region. They express required extents; they do not establish that an MMA caller enforces them. If W is loaded once and reused across several A matrices, host-to-W traffic can be lower than repeatedly counting the footprint. If O is initialized and later stored at a host/direct-SRAM boundary, O alone contributes 8MN transferred bytes even though its resident footprint is 4MN. Every traffic claim needs a boundary and lifetime.

The Roofline model bounds attainable performance by compute peak and bandwidth multiplied by operational intensity (WAT09):

```text
attainable rate <= min(compute peak, bandwidth × operations/byte).
```

For one explicitly scoped host/direct-SRAM lifetime that loads W and A, initializes O, and stores O once,

```text
T_host = 2MK + 2KN + 8MN bytes
OI_host = 2MNK / T_host operations/byte
OI_crossover = compute_peak / host_bandwidth.
```

Tusim counts two operations per MAC here. `OI_host < OI_crossover` identifies the bandwidth-limited side of this upper-bound model; it still does not predict latency or bank aliases. Changing the boundary, reuse lifetime, or O initialization changes the denominator. Timeloop and MAESTRO similarly separate workload, architecture, mapping, and constraints when deriving reuse and traffic; their methodology motivates that separation but does not validate Tusim's counters (PAR19, KWO19).

## 9.3 Three memory surfaces, not three stages of one request

| Surface | What it represents | How to interpret its counters |
|---|---|---|
| Direct W/A/O regions | By default 128/64/64 KiB, respectively. W and A hold two-byte FP16, O four-byte FP32. Each region has a backing store and its own bank meter. | An SRAM API request is metered; dereferencing a pointer into the same store is not. |
| Standalone memory hierarchy | RegFile (L0), LocalSPAD (L1, caller-supplied), GlobalBuf (L2) and DRAM (L3). | The hierarchy dispatches requests and keeps level totals. A hierarchy call is not one stage in every MMA. |
| `perf/cycle_model.[ch]` | A separate tile model with its own bank state and clock. It charges a tile to a starting bank using byte address modulo bank count. | This is not the generic SRAM word-interleaving rule below. The Makefile lists the hierarchy object in `TU_OBJS`, not `cycle_model.o`. Library membership alone would not establish a call path. |

## 9.4 From byte span to bank events

Let `a` be a byte offset, `n` the number of bytes, `w` bytes per word, and `B` the bank count. Word `j` selects bank `j mod B`. The first word is `floor(a/w)`. With the generic defaults (`w=4`, `B=32`), bytes 0–3 select bank 0, bytes 4–7 bank 1, and a stride of 128 bytes returns to the same bank. Sharing a bank index is an alias, not evidence that two requests competed for a port.

After admission, `sram_meter` chooses how many consecutive word indices to charge:

| Mode | Number of word events for `n > 0` | What it counts |
|---|---|---|
| `size_only` (default) | `ceil(n/w)` | Enough words for the byte count, starting in the first bank; ignores the offset within the first word. |
| `address_span` | `floor((a+n−1)/w) − floor(a/w) + 1` | Every aligned word containing at least one requested byte. |

An admitted empty bulk request charges neither meter. The distinction for a nonempty request is easiest to see on paper: `[0,4)` contains bytes from word 0 only; `[2,6)` contains the last two bytes of word 0 and the first two of word 1. The latter still moves **four bytes**, not eight. An address-span event is not a transfer of an entire physical word.

### Same four bytes per call, different accounts

Use two banks, four bytes per word, one grant per bank per four SRAM ticks, and a penalty of two per word without a grant. Start each case with full budgets `(1,1)`. Make two identical-address calls at tick zero, with no advance between them. Run reads and writes in **separate fresh regions**; the scalar (one bank word) and bulk (four bytes) interfaces give the same rows here. Pairs below are ordered `(bank 0, bank 1)`.

| Meter | Start | Attempts **per call** | Granted on call 1 | Grants left after call 1 and after call 2 | Ungranted on call 2 | Returned penalties (call 1, call 2) |
|---|---:|---|---|---|---|---|
| `size_only` | 0 | (1,0) | (1,0) | (0,1) | (1,0) | 0, 2 |
| `size_only` | 2 | (1,0) | (1,0) | (0,1) | (1,0) | 0, 2 |
| `address_span` | 0 | (1,0) | (1,0) | (0,1) | (1,0) | 0, 2 |
| `address_span` | 2 | (1,1) | (1,1) | (0,0) | (1,1) | 0, 4 |

Read the last row in two ways. After two reads the region reports **four read words**, but only two words received grants: each bank reports one served and one stalled. After two writes the same counts appear on the write side instead. Both calls completed their byte copies. The offset-2 reads returned `32 33 34 35` (hex) both times. The writes first placed `85 86 87 88` there, then replaced them with `89 8a 8b 8c` **despite the second penalty**. The comparison checks every byte of the region and guarded host buffer, not just the counter totals.

## 9.5 Grant width is not refill period

**Word width** is bytes per bank word. **Grant width** is words available per bank at a refill. **Period** is how far that region's counter must advance before another refill. In `tu_sram.c` an eligible advance resets each budget to its configured grant and stamps the current region cycle. It does not accumulate unused credits for every window crossed. A call with no grant copies normally, records a stall event, and returns the penalty; it does not advance the region clock or arrange a retry.

Keep four-byte reads on bank 0 and the penalty at two. First change only the period; then change only the grant in a fixed burst. Each row begins with a fresh region.

| Read ticks supplied by caller | Grant | Period | Penalty returned at each read | Sum |
|---|---:|---:|---|---:|
| 0,1,2,3,4 | 1 | 4 | 0,2,2,2,0 | 6 |
| 0,1,2,3,4 | 1 | 1 | 0,0,0,0,0 | 0 |
| 0,0,0,0 | 1 | 1 | 0,2,2,2 | 6 |
| 0,0,0,0 | 2 | 1 | 0,0,2,2 | 4 |
| 0,0,0,0 | 4 | 1 | 0,0,0,0 | 0 |

In the first row the budget runs out on the first read and returns at tick 4. In the last three rows no time passes: the entire difference comes from the initial grant width. The field historically named `words_per_cycle` means words **per refill**. A period of one gives per-tick replenishment when ticks actually advance. Even then, “two grants” does not mean two implemented SRAM ports.

## 9.6 Penalty, utilization and arbitration

A stall count is the number of metered words that found an empty bank. `stall_cycles` sums the assigned penalties. Neither is requester waiting time. In the v1 audit (**historical**), writes to addresses `0,0,4` returned `0,3,0` under a three-unit penalty; the second write was immediately visible. The low-level `conflicts` counter stayed zero. The current `sram_bw_consume` records served/stalled words, not pairs of contending requesters. Do not substitute a conflict count from the separate cycle model.

The utilization helper is also an accounting convention. For positive region time its denominator uses the grant times the bank count times `max(1, floor(current_cycle/period))`; it caps the ratio at one. Initial grants can be spent **before** the first refill. Historically one bank served two words across the initial and first refilled budgets but reported 100%, not a measurement of busy physical cycles. Inspect the grant ledger rather than reverse-engineering a schedule from a clipped ratio.

`arb_mode` is stored metadata on this path. There is no requester ID, pending queue, grant-order choice, or completion event; serial calls cannot distinguish round-robin fairness from priority. Likewise, the presence of `read_latency` or `write_latency` fields does not charge base latency in `sram_bw_consume`. Follow the chain: **declared → initialized → consumed → observable effect**.

## 9.7 Requested versus active configuration

**Historical v1 fixture:** JSON requested W/A/O = 16/8/12 KiB and eight banks of eight-byte words. Capacities reached the direct allocations, but the banks stayed at the compiled 32 × 4 B. That observation is not the v2 conversion rule.

**Public-pin source trace:** `infra/config.c` parses `tu.memory.banking` and `tu_config_to_runtime` carries count, width, grant (`words_per_refill`), period (`refill_window_cycles`), penalty and `word_metering`. Follow those values one step further. `tu_init_with_config` passes the runtime count, grant, penalty and period to the W/A/O constructors and applies the word-meter mode to all three. It passes **`TU_SRAM_BANK_WIDTH` (4)**, not the converted width, to those constructors. A field can survive conversion without determining active geometry. The lower-level constructor accepts an explicit width; a scalar caller must supply a buffer of that word size. The Session 6 probe constructs its regions directly; it is not another JSON-ingress test.

## 9.8 Hierarchy semantics and cycle domains

In `memory/memory_hierarchy.c`, RegFile counts activity: writes retain no bytes and reads zero-fill. LocalSPAD delegates to a supplied region; GlobalBuf has storage, but a “hit” means the requested span is in range, not that a tag matched or a tile was reused. DRAM delegates to a different model. The hierarchy tick advances hierarchy time and ticks DRAM; it does not call the SRAM refill helper. Historically, four hierarchy ticks failed to replenish an exhausted GlobalBuf; advancing the SRAM itself did. A pre-init 2 KiB GlobalBuf override in that audit also gave way to the 1 MiB compiled default. Neither observation was remeasured here.

A named level is not a cache, and a counter named `current_cycle` is not a clock shared by every level. Before combining numbers, identify who advances each clock, when, and which events it owns.

## 9.9 Raw pointers and operation-specific fidelity

In `tu_cmodel.c` direct MMA takes the W, A and O pointers from `tu_sram_raw_ptr` and passes tensor views to the dataflow path. A pointer dereference does not call `sram_meter`. **Historical:** immediately around a 1×1×1 MMA the v1 probe saw no region read/write counter changes. That observation does not mean the multiply required no operands; it means the meter was not on the compute access path. A nonzero dataflow cycle estimate is consistent with this result.

Selected operators call the SRAM API; descriptor DMA has its own accounting. Changing the SRAM word-meter mode need not change a DMA descriptor's charges or model an MMA operand fetch. Adding bank penalties to a dataflow estimate would require a schedule connecting the two, not merely a common label of “cycles.”

## 9.10 What the checks establish

The byte-and-grant experiments covered reads, writes, both meters and the refill controls. They did not execute the hierarchy, descriptor DMA, context switching or a complete operator.

**Historical suite results only:** v1 reported 10/10 hierarchy functions, 19/19 cmodel cases and 20/20 config cases. These were different coverage units; in particular the old config harness did not reliably turn assertion failures into a failing process exit. None of those totals is a Session 6 result.

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

**Measured here:** completed four-byte SRAM copies, word events, per-bank grants/stalls, logical admission and returned penalties under explicit advances. **Read in source:** which configuration fields reach the region, which clock refills it, and where raw pointers bypass the meter. **Not established:** physical bank conflicts, port count, arbitration, usable hardware bandwidth, silicon time, area, energy, or end-to-end latency.

[Next: Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution](10-dma-descriptor-contracts-and-tick-driven-execution.md)
