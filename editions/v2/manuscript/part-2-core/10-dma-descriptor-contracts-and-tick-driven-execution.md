# Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-10)

A transfer description can be correct even though not a single byte has moved. On the public Tusim revision `7a094ff6c5527eff8e4318de676f0c0221c448b4`, a tiled iterator asks for **130 contiguous ranges**. A caller supplies space for 128. The result is neither an error nor permission to read 130 entries: it is a required count and a stored prefix. A second consumer builds all 130 descriptors. At that point the destination is still untouched.

This chapter follows those bytes from a logical coordinate to a host pointer, an SRAM offset and finally an observable change at the destination. The question is **which bytes can the consumer deliver, in what order, and who still owns them?** Channel selection and service policy are separate questions. By the end, you should be able to distinguish a valid range, a complete chain, an accepted submission, a performed copy and a retired channel slot; calculate payload independently of span; and test a transfer without trusting the generator that produced it.

## 10.1 Choose a descriptor by its endpoints

A descriptor describes memory events, not a tensor name. First locate both endpoints and determine whether each is contiguous, regularly strided or indexed. Then choose the form:

| Form | Useful bytes requested | Check before use |
|---|---:|---|
| Linear | elements × element width | One interval at each endpoint |
| 2D or 3D strided | planes × rows × row payload (one plane for 2D) | Independent source and destination row/plane strides |
| Scatter / gather | indices × element width | Every indexed interval; repeats are events, not additional unique storage |
| Multicast | source payload × number of targets | Each region and offset; distinguish source footprint from requested fanout |

For example, two rows each holding three two-byte elements contain **12 payload bytes**. If the source row stride is 11 and the destination row stride is 13, the half-open envelopes occupy 17 and 19 bytes respectively: one stride plus the six-byte last row. Copying 12 contiguous bytes is wrong on both sides. For a nonempty 3D volume add `(planes−1) × plane_stride` to the corresponding row envelope. Empty dimensions, index duplicates and overlapping spans need their own interpretation; calculating a payload is not checking an allocation. These are geometry calculations, not bus traffic measurements.

`descriptor_sram_spans_valid()` in `tu_cmodel/dma_descriptor.c` checks the SRAM address pattern for the form, including strided and indexed accesses. Submit checks the chain before queue insertion; the direct executor also checks the descriptor it receives. Neither sees a length for an arbitrary external host allocation. The caller must establish representable arithmetic and host extent **before** forming pointers. This applies even if a later SRAM check would refuse the copy.

## 10.4 The worked chain: where do the last 520 bytes come from?

Use a dense **3 × 129** row-major matrix with four-byte elements in each of two 1,584-byte allocations. The matrix starts at byte 12. Visit tiles in row-major order, using 2 × 2 tiles; within each tile visit the valid rows and columns only. Right-edge tiles have one column, bottom-edge tiles one row, and the corner one element. There are no padding elements. For cell `(r,c)` its first byte at either endpoint is `12 + 4 × (129r + c)`.

The first tile visits `(0,0), (0,1), (1,0), (1,1)`. The first two elements form `[12,20)`; the next two form `[528,536)`. The next tile returns to row zero at byte 20. **A range boundary is a break in consecutive addresses in visit order, not a tile boundary.** This matters at the far edge:

| Node (zero-based) | Visited elements | Byte interval, both endpoints | Bytes |
|---:|---|---|---:|
| 0 | row 0, columns 0–1 | [12,20) | 8 |
| 1 | row 1, columns 0–1 | [528,536) | 8 |
| 2 | row 0, columns 2–3 | [20,28) | 8 |
| 3 | row 1, columns 2–3 | [536,544) | 8 |
| … | alternating pairs on rows 0 and 1 | … | … |
| 126 | row 0, columns 126–127 | [516,524) | 8 |
| 127 | row 1, columns 126–127 | [1032,1040) | 8 |
| 128 | row 0, column 128 | [524,528) | 4 |
| 129 | row 1, column 128, then **all of row 2** | [1040,1560) | 520 |

Row 1's final element ends exactly where row 2 starts. Traversing two-column tiles across that last, one-row strip produces no gaps. The last range is therefore `(1 + 129) × 4 = 520` bytes, not a padded two-row tile, and not a separate descriptor for every bottom tile. The first 128 records account for 1,024 bytes; the two missing from the bounded prefix account for **524 more**. The builder produced all 130, for `128 × 8 + 4 + 520 = 1,548` bytes. Construction left both endpoints unchanged, with zero transfers, zero useful bytes charged and zero pending queue depth.

### How to check order when the final image cannot show it

Initialize host byte `i` to `(37i + 11) mod 251` and all SRAM bytes to `0xff`, which the source never produces. An independent Python oracle enumerates valid tile coordinates and the four byte lanes of each element. It checks that sorting the addresses gives **exactly** `[12,1560)` once each, then groups consecutive addresses *without sorting* to predict the descriptor sequence. Neither its ranges nor its byte order come from the iterator under test.

The C probe records the stored prefix, checks both endpoint selections and each descriptor's shape before execution, then compares the entire destination to its previous image after **every call**. The record contains each changed offset and new value, the completion flag and cumulative transfer/byte counts. Both complete endpoint images are checked at the end, including the 12-byte leading and 24-byte trailing guards. The oracle and the observed streams matched exactly. After the last node: 130 transfers, 1,548 useful bytes, no submission or retirement. This proves **descriptor order and logical byte coverage** for the fixture, not temporal order among individual byte writes inside a single `memcpy`.

Why not just compare checksums? Swapping the first two calls changes neither the final bytes nor the total count. It *does* change the first observed destination interval from `[12,20)` to `[528,536)`. Dropping the last two nodes can leave all 128 stored prefix entries correct; it cannot pass the full-image and multiplicity checks.

## 10.6 What a tick adds, and what it does not

Direct execution deliberately bypasses the queue. For an ordinary numbered descriptor, successful synchronous submission executes work inside the submit call. In tick-driven mode the pending descriptor has not yet copied bytes. Selection invokes the executor in the tick call; on a successful copy model bytes become visible then. The executor records `cycles_completed` relative to the engine's current clock. A subsequent eligible tick can clear the active slot and increment the channel's completion count. **Visible bytes, completion flag, eligibility timestamp and retired slot are four observations.** None is a command-queue dependency signal. This description follows `tu_dma_submit_desc()`, `tu_dma_tick()` and `tu_dma_execute_desc()` at the pin; the worked chain did not tick the engine.

The range walk and the scheduling experiment answer different questions. To measure scheduling, use independent one-node descriptors with identical logical ranges; construction is not admission.

Top-level reinitialization is not cancellation. `tu_init_with_config()` calls `tu_shutdown()` before replacing live state; the shutdown path flushes accepted DMA before releasing referenced SRAM and command-queue state. Keep borrowed destinations valid across that drain. Do not transfer that guarantee to a bare low-level engine initializer. Chapter 5 treats the lifecycle comparison; no reinitialization was needed for the chain.

## 10.7 Count at the interface that owns the event

| Observation | Owner | What it establishes |
|---|---|---|
| Range count | Iterator | Storage required to describe this visit, not bytes transferred |
| Useful bytes / transfer count | Descriptor executor | Payload charged / accounted descriptors, not retired slots |
| Occupied bytes | Descriptor payload model | Payload beats × configured bus width in bytes, not measured pin traffic |
| Estimated cycles / `cycles_completed` | Engine / descriptor | Sum of modeled service charges / one eligibility timestamp, not wall time |
| Pending depth / completed count | Channel | Queue bookkeeping / traversals or retirements, not an endpoint comparison |

The first edition used `50 + ceil(bytes/32)` without SRAM penalties for a particular default service example. It is not a general equation for this revision. The descriptor path now reads configured bus width and direction-dependent base/issue settings. [Chapter 4](04-configuration-as-the-architecture-contract.md) follows a 33-byte request through runtime conversion to distinguish descriptor service from a top-level copy charge. Similarly, **three is the default number of DMA channels, eight the engine storage capacity**. The initializer rejects a count above capacity rather than silently clamping it. The first edition's three-slot objection to a four-channel request no longer applies. A legal count does not establish readiness of any particular buffer.

[Chapter 9](09-memory-hierarchy-and-banked-scratchpads.md) exercised the local SRAM read/write API. The descriptor executor instead copies through a raw region pointer and can run its **own** meter: it charges `ceil(total_bytes / bank_width)` words starting from the SRAM base, stepping by bank width. It does not replay every strided row through Chapter 9's address-span API. The worked chain disables SRAM bandwidth modeling; its evidence concerns copied payload, not bank grants, penalties or elapsed time.

The descriptor engine is the process-global `g_tu_dma`. Ordinary W/A loads and O stores have fixed wrapper paths; neither an ordinary operation nor a command gains a general iterator operand because the descriptor code is linked. Likewise, describing host bytes as “external” does not establish a call to a DRAM timing model. One must trace the *consumer*, not just find the data structure.

## 10.9 Which queue owns the descriptor, and which queue gets the bus?

Binding chooses a queue **at admission**. Arbitration chooses a pending head **at service**. Round-robin (RR) binding does not imply round-robin arbitration, or even a shared bus. To separate them, take the 130 records from §10.4 in their published order. Construct one numbered linear load per record, with requested channel 0, priority 0, four-byte elements and the original endpoint offsets. Each new descriptor has `next == NULL` when offered. Binding may change the channel; it must not change which W-SRAM bytes the descriptor names.

Give each of four queues an outstanding limit of 130 rather than the default four. Admit the entire batch before the first tick; there is no later arrival, queue-full retry, flush or producer stall. All 130 submit calls returned a ticket at cycle zero, with zero copies and the destination still at `0xff`. This is a deliberately deep-queue experiment: refilling shallow queues as they drain would change the set of heads eligible at each decision. Retain the admitted objects until the engine has drained; a rejected submission would stop the experiment, not retry a possibly destroyed pointer.

| Data path (other settings fixed within each pair) | Binding | Tick calls to last retirement | Elapsed model cycles |
|---|---|---:|---:|
| Independent channel paths | Explicit | 6,647 | 6,647 |
| Independent channel paths | RR | 1,700 | 1,700 |
| Shared serial, deficit round-robin (DRR), zero stage charges | Explicit | 6,647 | 6,647 |
| Shared serial, DRR, zero stage charges | RR | 6,647 | 6,647 |

The binding change is visible even in the pair with **no change in elapsed time**. Counts and executor charges below apply to both topologies. Each submitted count equalled the channel's observed retirement count; every queue ended empty with no active descriptor.

| Binding | Channel | Submitted / retired | Useful bytes | Occupied bytes | Service cycles |
|---|---:|---:|---:|---:|---:|
| Explicit | 0 | 130 / 130 | 1,548 | 4,672 | 6,646 |
| Explicit | 1, 2, 3 (each) | 0 / 0 | 0 | 0 | 0 |
| RR | 0 | 33 / 33 | 260 | 1,056 | 1,683 |
| RR | 1 | 33 / 33 | 776 | 1,568 | 1,699 |
| RR | 2, 3 (each) | 32 / 32 | 256 | 1,024 | 1,632 |

Why does channel 1 finish last on the independent RR paths? It gets ordinal 129, the 520-byte tail. Channel 0 gets the four-byte tail. Equal descriptor counts need not mean equal service. Here a read costs 50 base cycles plus one cycle per 32-byte payload beat, rounded up *per descriptor*, with issue and SRAM penalties off. There are 146 beats, hence 4,672 bytes of modeled interface occupancy for 1,548 useful bytes. The service sum is 6,646 cycles in every arm. On independent paths the clock follows the **longest** queue (one initial tick plus 1,699); on the serial path only one head can occupy the bus, whatever the placement.

[Next: Chapter 11 — Instruction Surfaces and Command-Queue Ordering](11-instruction-surfaces-and-command-queue-ordering.md)
