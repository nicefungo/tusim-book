# Chapter 16 — Double Buffering and Legal Overlap

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-16)

A descriptor says that a tile transfer completed. The controller swaps buffers. Which bytes does the consumer see? At the public pin the copy completed, but the new active buffer did not contain the tile. Completion and readiness describe different events.

This chapter asks when a role exchange is legal, not how fast a descriptor scheduler runs. [Chapter 9](09-memory-hierarchy-and-banked-scratchpads.md) distinguishes stored bytes from bank service. [Chapter 10](10-dma-descriptor-contracts-and-tick-driven-execution.md) distinguishes a byte copy from channel retirement. Here the test is stricter: the old reader's bytes must survive, and the right new bytes must be visible **at the transfer of ownership**. A performance claim requires a schedule in addition to those functional conditions. The comparison used the standalone controller, not a timed accelerator workload.

## 16.1 A slot is a place; active is a role

Call `r->banks.data` **P** and `r->db->shadow_data` **Q**. After `tu_sram_init`, enabling double buffering adds a zeroed allocation as large as P. With `active_idx=0`, `tu_sram_raw_ptr(r)` selects P and `tu_sram_get_shadow_ptr(r)` selects Q. After one swap the pointers select Q and P respectively. Q is called `shadow_data` even while it is **active**. No bytes move on a swap. A second allocation of size *S* gives two roles of *S* bytes, not a tile of size *2S*. The bank service state still belongs to the region, not to each allocation. Neither independent SRAM ports nor simultaneous service follows from allocation size.

In `memory/double_buffer.c`, swap toggles the index, increments the count and clears `shadow_dirty`. It does not wait. `tu_sram_notify_shadow_write` marks dirty and adds the *caller's* byte and cycle counts; it neither writes memory nor verifies the range. Disabling when Q is active copies Q back to P before freeing Q; that is a different operation from swapping. A design with live readers also needs rules for reset, destruction and context switching. For example, the public context code copies scoped primary bytes and clears the restored regions' `db` links. A saved primary image is not a saved ping-pong generation. [Chapter 18](18-runtime-context-retention-and-preemption-boundaries.md) treats retention separately. We did not run a live-buffer context-switch test here.

To authorize a transfer of ownership, name the producer, physical destination, generation, and byte extent. Verify successful delivery of that extent, the old readers' release, and exactly one exchange by the owner. A consumer must resolve the newly active generation before reading. These conditions are distinct: an on-time copy into the wrong allocation is still wrong; a complete new tile does not authorize recycling storage still in use.

## 16.5 Where the apparent speedup comes from

The controller stores a compute deadline and command ID. Reaching a deadline advances the stage; it does not dispatch that ID and observe arithmetic. `tu_pipeline_get_stats` reports `sequential_total / pipelined_total`. The numerator charges estimated load + requested compute + estimated store on submission (one for each absent transfer). The denominator sums **credited compute** + (load − credited load overlap) + (store − credited store overlap). For this fixture the load estimate uses 64 bytes / 32 bytes per controller unit = 2. That is not the descriptor's 52-cycle service estimate. The stages and counters do not define a common clock for computation, load and SRAM service.

| Same 64-byte load, at transfer of ownership | Sequential estimate | Credited compute | Credited load overlap | Modeled denominator | Reported ratio | Ready? |
|---|---:|---:|---:|---:|---:|---|
| Only the loaded tile | `2+100+1=103` | 100 | 0 | 102 | 1.009804× | No |
| Add an older no-load tile | `103+(1+100+1)=205` | 100 | 2 | 100 | 2.050000× | No |

In the first row, even zero overlap credit gives a ratio above one: the absent store costs one only in the numerator. In the second row the no-load tile starts directly in COMPUTE, bypassing the transition that adds compute to the denominator. The preload transition credits load overlap when two tiles are active and the option is enabled. Neither rule examines the consumer's bytes. This explains why deleting the first edition's *capacity objection* must not delete its *overlap objection*.

## 16.6 A schedule worth calling overlap

Under a stated **analytical** model, let `D` be load time, `C` compute time, and `T` the number of identical tiles, all in one clock. With authorized role role exchanges, two slots, independent resources and no stores, the first fill is exposed, `T−1` intermediate windows each cost `max(D,C)`, and the last compute drains. Total: `D + (T−1)max(D,C) + C`. For a preload and a store sharing one serialized channel, do not hide each independently under the same compute window. With `C=100`, preload 80 and store 80, a shared channel can hide at most 100 units there, not 160. Separate channels still need independently serviceable endpoints. None of these equations is an observation of the controller.

The first edition's historical M-tiling example (`docs/exploration/double-buffer-mtiling-recovery.md`) illustrates why comparisons need a capacity budget. In that *idealized report*, changing O from a 64 KiB single role to two 16 KiB roles consumes 32 KiB, not 16 KiB. More M chunks can create more inter-tile windows; one chunk creates none. Count W/A duplicates, fill/drain, bus and bank contention before recommending a mapping. A PE operand demand is not necessarily a boundary-injection rate. No area, energy, or hardware speedup was measured in this replay.

Choose a single slot when a second slot cannot buy a useful window, equal ping-pong when full tiles fit twice and ownership is simple, disjoint bank partitions when padding and fragmentation are cheaper, or a deeper ring to absorb variable service. A ring cannot fix insufficient sustained producer bandwidth. A timing design needs events that bind an immutable physical slot and generation to success, produced extent, reader retirement and reuse. The scheduler's separately named “double-buffered” instruction sequence, a published analytical timeline and this standalone controller are not interchangeable evidence of such a design.

**Design exercises (carried forward from the first edition).**

1. Design `FREE → PRODUCING(g) → READY(g) → ACTIVE(g) → RETIRED(g)` for two slots. Include partial, failed, canceled and duplicate completion, old readers and reset. Give a negative test for each guard. *Worked check:* 63 of 64 bytes cannot publish READY even with the right generation; a stale completion for 64 cannot publish the next generation either.
2. Give a descriptor an immutable physical-slot handle and generation. Reverse the roles while a test descriptor is pending. *Acceptance:* delivering to the named allocation must not follow the changed index; activation still needs the matching completion and reader release. Keep the sentinels on both sides, not just a final active checksum.
3. Schedule four tiles with `D=60`, `C=100`, `S=30`. Compare serial, load-only, shared bidirectional DMA and independent load/store channels. *Worked answer:* serial 760. With next load under current compute but all stores exposed: 580. With sufficient distinct input/output slots, the intermediate compute windows fit one next load plus one previous store (`60+30≤100`); expose the first load and last store for 490. Independent channels also give 490 in this regime. Show where equality fails as `D+S` grows.
4. Compare 16, 24 and 32 KiB equal O roles with a 64 KiB single O. Charge both data arrays, any W/A duplication, traffic and start/drain. Find a regime where single wins.
5. Replace submission arithmetic with an event ledger. For equal work and no overlap, test that sequential and pipelined elapsed time agree. Include missing and rejected operations.
6. Specify how context save, cancellation and reset handle both arrays, generations, readers and live descriptors. Contrast drain-before-switch with prohibiting a live switch.
7. Map two FP16 tiles to disjoint banks with `(address/4) mod 32`; quantify padding and design a same-bank collision control. Explain why separate allocations alone do not pass it.
8. Audit the historical M-tiling report using its discrete ceilings as well as its continuous approximation; distinguish per-PE operands from boundary injection. Label which assumptions change the hiding threshold.
9. Propose a calibration trace: name fill, compute, visibility and drain events, clock conversion, contention regime, held-out workloads and acceptable error. Explain which simulated counters would *not* be reference observations.

[Next: Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy](17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md)
