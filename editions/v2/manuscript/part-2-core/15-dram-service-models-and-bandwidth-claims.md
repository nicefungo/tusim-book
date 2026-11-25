# Chapter 15 — DRAM Service Models and Bandwidth Claims

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-15)

Should a memory controller keep the last row open? Four reads of 64 bytes each make a useful test. When the reads reuse one row, keeping it open costs **220** model service cycles against **280** for closing it. Change only the addresses so that the reads alternate between two rows of the same bank, and the order reverses: **340** against **280**. No data volume, clock or peak bandwidth changed. What changed was the kind of miss that an open bank can incur.

Those numbers come from the standalone, caller-ticked DRAM model in public Tusim `7a094ff6c5527eff8e4318de676f0c0221c448b4`. They are sums of what `tu_dram_read` returns in its `cycles` output, **not elapsed cycles**. Indeed, all four calls occur at the same caller tick. We'll use that distinction twice: first to explain the reversal, then to decide what it means for a request to occupy the bus. The row and burst replay contains the predictions, the actual streams and the commands to compare them.

## 15.1 Decode the addresses before naming the pattern

A row is local to a **channel and bank**. Switching row numbers in two different banks need not evict either row. Our custom instance has two channels, two banks per channel, 256-byte rows and 64-byte address stripes. We explicitly select `BURST_INTERLEAVED`. For byte address `a`, `a / 64` (integer division) gives the stripe number. Successive stripes alternate channels; four stripes per channel fill a row's worth of columns before advancing the bank; after both banks the row number advances.

| Byte address | Channel | Bank | Row | Use in the experiment |
|---:|---:|---:|---:|---|
| 0 | 0 | 0 | 0 | First read |
| 64 | 1 | 0 | 0 | Different channel, not a same-bank replacement |
| 128 | 0 | 0 | 0 | Different address that reuses the first row |
| 512 | 0 | 1 | 0 | Different bank on the first channel |
| 1024 | 0 | 0 | 1 | Different row that competes for the first bank |

These are decoder outputs, not guesses from the size of the stride. Row-interleaved and XOR-interleaved mappings also exist; neither is selected here. The **64-byte stripe** selects an address destination. The **8-byte bus width** sets bytes per serialization cycle. A **64-byte protocol granule** will determine occupied bytes in a later experiment. Equal numbers do not make the stripe and the granule the same control.

The core clock and the DRAM parameter record's clock are both 1 GHz. Read/write base latencies are explicitly **50/40 core cycles**, not values entered as nanoseconds. Peak bandwidth is 64 decimal GB/s. Refresh is off. Each arm constructs a fresh model and ticks it 1,001 times before the first call; the observed budget then holds 64,000 bytes. Thus the initial empty bandwidth window does not dominate these short traces. Turnaround is off for the row comparisons. These are direct constructor/setter choices, not a claim about the settings an application got from JSON. At this pin a separate `tu_dram_create_from_config` constructor applies full-config settings, and the core-clock setter is effective; don't carry forward the first edition's contrary conclusions.

## 15.2 A miss on an empty bank is not a replacement

Call the first trace **reuse**: addresses `0, 128, 0, 128`. Call the second **alternate**: `0, 1024, 0, 1024`. For an explicit page policy, a hit pays no extra row service. Accessing an empty bank pays activation cost *A*. Finding another row open pays replacement cost *R*, the **whole** replacement penalty, not *A + R*. Closed-page treats each access as an empty activation; it doesn't charge to evict a row left open by the previous request. For our four reads without refresh or direction changes:

```text
service sum = 4 × 50 + empty activations × A + replacements × R
```

| Row policy | Reuse: hits / empty / replacements | Service, A/R = 20/20 → 20/40 | Alternate: hits / empty / replacements | Service, A/R = 20/20 → 20/40 |
|---|---|---:|---|---:|
| Open-page | 3 / 1 / 0 | 220 → 220 | 0 / 1 / 3 | 280 → 340 |
| Closed-page | 0 / 4 / 0 | 280 → 280 | 0 / 4 / 0 | 280 → 280 |
| Adaptive timeout, no tick between calls | 3 / 1 / 0 | 220 → 220 | 0 / 1 / 3 | 280 → 340 |

On the alternating trace both static policies report **four conflicts**. With equal costs their service is also identical. The counts of empty activations and replacements reveal the difference that the total hides. Doubling *R* charges three replacements another 20 cycles each; it changes nothing in closed-page. Open-page is preferable on reuse but not on this alternating trace with expensive replacement. This is a choice conditional on **both trace and timing**, not a universal controller ranking. The unchanged public sweep provides a longer example with different geometry: on its 64 alternating reads, equal costs give 4,480 for both policies, but split costs give 5,740 open against 4,480 closed.

**Legacy is a fourth policy, not shorthand for closed-page.** With the legacy row flag off, both traces return 200 and record no conflicts. With the flag on and the flat penalty set to 20, both return 280 and record four conflicts, but **zero** empty activations and replacements. A separate fresh read/write control returns 70 for the read and 40 for the write: only the read takes the flat charge. It would be a mistake to interpret the four legacy conflicts as four address-derived misses. Conversely, the explicit policies account for writes as well as reads. Full row results · read/write control.

Service is only one output. On the split-cost, open-page alternating trace the service sequence is `70, 90, 90, 90`. With no intervening ticks, the calls see previous channel-availability gaps of `0, 70, 90, 90`: **250 stall cycles** in a separate ledger. Availability is set from the current caller time, not appended to the tail of a request queue. The caller clock is still 1,001. Neither 340 nor 340 + 250 is a measured makespan.

## 15.3 Eight ticks is not more than eight

`ADAPTIVE_TIMEOUT` keeps a row open for reuse but may close it on the next access to that bank. Which side of the threshold includes equality? Read address 0, advance the caller clock, then read 128. Both addresses decode to the same row. Set the timeout to eight **core cycles** and hold *A/R* at 20/40.

| Gap from first access (ticks) | Second service: open / closed / adaptive | Adaptive second stall | Adaptive timeout precharges after second read |
|---:|---|---:|---:|
| 7 | 50 / 70 / 50 | 63 | 0 |
| 8 | 50 / 70 / 50 | 62 | 0 |
| 9 | 50 / 70 / 70 | 61 | 1 |

The test is **strictly greater than** eight, measured since the last access to that bank. The ninth tick by itself has not closed the row: just before the second access the probe still sees row 0, last access 1,001, zero timeout precharges. The access performs the lazy closure, then pays an empty activation, not a replacement. Even here the channel is not idle in the ordinary sense: the previous 70-cycle service boundary still lies ahead. Before/after state distinguishes two notions of idle: **age since bank access** controls this row timeout, whereas **time since channel availability** controls bus turnaround credit.

## 15.5 Which bandwidth did the extra bytes consume?

Use the shared Chapter 15/17 payload experiment, not the row fixture, for a bandwidth comparison. One 16-byte read at address 0 is issued at tick 0; one 80-byte write at address 64 at tick 64. Sample at tick 128. Both arms use a 1 GHz core clock, an 8-byte bus and an 8 GB/s peak. The interval is **128 caller cycles**, not the sum of service or stalls. The same two raw records support both chapters.

| Accounting over those 128 cycles | Exact burst credit | Size-rounded burst credit (64 B) |
|---|---:|---:|
| Useful read + write | 16 + 80 = 96 B | 16 + 80 = 96 B |
| Occupied read + write | 16 + 80 = 96 B | 64 + 128 = 192 B |
| Useful / occupied bytes | 100% | 50% |
| Combined useful bandwidth | 0.75 GB/s | 0.75 GB/s |
| Combined occupied bandwidth | 0.75 GB/s | 1.50 GB/s |

At 1 GHz, 96 bytes in 128 caller cycles gives `96/128 × 1 = 0.75` decimal GB/s. Rounded occupancy doubles that numerator without doubling useful work. **Payload efficiency** divides useful bytes by occupied bytes; **occupied utilization** instead divides occupied bandwidth by the 8 GB/s peak (9.375% exact, 18.75% rounded). The read/write service outputs remain 10/8 in both arms; the separate stalls are 1,000/936 from the initially empty window. The calls still record the requests. The reported rates describe this observation interval, not a schedule proving the interface completed two transfers in 128 cycles. Nor does twice the occupied traffic mean twice the energy.

## 15.6 What the window, the estimator and the caller can tell us

The first edition ran a different, HBM2 fixed-window experiment at `e918c80b6fce833cd1fcae97730fa841c2176f25`. After refill, pending bytes grew while remaining budget shrank. For successive 64-byte requests against 256,000 starting bytes, the first **window** stall occurred on request 2,001, after 128,000 prior bytes; that was not the first channel stall. In a separate moved-window reset, the first post-reset read stalled zero rather than the fresh instance's 1,000: reset rewound caller time without clearing the old window start. Those are **historical observations**, not results of the row or payload runs here.

Choose the producer to match the question. The standalone **estimator** takes size and direction, no address; for positive non-ideal bandwidth and nonzero work it adds a base latency to `ceil(requested bytes / (GB/s ÷ core GHz))`. It cannot distinguish our two address traces. The **stateful access** sees addresses and updates row, direction, occupancy and channel state; `tu_dram_tick` owns the advance of caller time. The **statistics** divide cumulative bytes by caller cycles (denominator at least one), not by estimated completion time. The [descriptor engine in Chapter 10](10-dma-descriptor-contracts-and-tick-driven-execution.md), a hierarchy wrapper and the separate `perf/cycle_model` are different producers. These probes do not execute an ordinary operator, copy backing-store data, or establish a shared timeline with any of them.

**Reader check.** If an experiment reports four misses and 280 service cycles, can you infer the policy? No: with equal costs, alternating open-page has one activation and three replacements; closed-page has four activations. Even legacy with the flat flag can report those two totals without tracking any row. Ask for the decoded addresses, the event breakdown and the caller ticks before interpreting a result. To go from service estimates to a device recommendation would additionally require a feasible issue/completion schedule and calibration against a named device or controller. A preset name and a green test supply neither.

[Next: Chapter 16 — Double Buffering and Legal Overlap](16-double-buffering-and-legal-overlap.md)
