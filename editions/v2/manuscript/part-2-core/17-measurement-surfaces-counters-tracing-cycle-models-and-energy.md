# Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-17)

A read requests 16 bytes; a write requests 80. One report says 0.75 GB/s, another says 1.5 GB/s. Both describe the **same two requests over the same interval**. The first counts bytes the caller asked for; the second counts bytes charged to an interface that rounds each request to a burst. Neither number tells us when a consumer could use its data.

At public Tusim `7a094ff6c5527eff8e4318de676f0c0221c448b4`, we will read those numbers from Chapter 15's shared experiment, then apply the same discipline to a fixed-process power sweep. The first experiment changes a byte-counting rule at a fixed clock. The second changes a clock at fixed activity and process. They do **not** measure one workload from two vantage points. The older counter and trace examples below are identified as such: a demonstration from the first edition is not a second-edition regression result.

## 17.1 Before interpreting a number, identify who advances it

A useful measurement record says **who recorded what, between which boundaries, and in which units**. For a rate, keep both raw operands. Add the configuration that reached the producer, the clock owner, the derivation, and the costs left out. For example, “1.5 GB/s” is incomplete; “192 occupied bytes / 128 model core cycles at 1 GHz, summed across read and write, decimal GB/s” can be checked without trusting a column heading.

A *producer* changes state: it counts an issued request, advances a model, or records a MAC. A *reporter* reads that state and may divide by a time supplied by someone else. An event count, a service estimate, a schedule and a physical measurement require different evidence. A reported event need not have retired. A returned service cost need not advance a clock. Two counters each equal to 100 need not delimit the same hundred cycles.

## 17.2 Choose the state owner

| Question | Where to look | What not to infer |
|---|---|---|
| What did ordinary core calls account for? | Legacy state such as `g_tu` DMA bytes, MMA calls and estimated cycles; find the operation that updates each field. | That every operation pays against a single elapsed clock. |
| What did my instrumentation record? | Caller-owned `tu_perf_counters_t`; operation recorders and explicit `tu_perf_tick`. | That a linked counter library populated itself during an ordinary workload. |
| Which value changed first? | Caller-owned event-trace context, or the separate process-global logging trace. | That files in the same format share clock, signal coverage or overflow policy. |
| What cost did this modeling choice assign? | Standalone cycle-model state, or the DRAM service API used in Chapter 15. Inspect the actual call and returned units. | That the caller consumed the wait, that a legal schedule exists, or that an enum certifies accuracy. |
| How much energy do these actions cost under these assumptions? | Scalar energy embedded in perf counters **or** the standalone `tu_power_model_t` action table. | That results from the two producers are disjoint charges that may be added. |

This distinction carries across chapters. [Chapter 10](10-dma-descriptor-contracts-and-tick-driven-execution.md) separates transfer from descriptor retirement. [Chapter 16](16-double-buffering-and-legal-overlap.md) asks whether the right bytes are visible **at swap**, not whether a controller incremented its overlap statistic. Four initialized channels at this pin fit the eight-entry backing; the old capacity objection belongs to the old pin. Removing that objection did not establish a legal preload. The Session 8 review retains the swap-time counterexample. [Chapter 14](14-operator-compute-engines-functional-semantics-and-engine-metrics.md) reports the public-pin attention, normalization and softmax experiments separately. Its logical transfer counts and operator-local penalties belong to those fixtures; they are not the DRAM occupancy or energy measured by this chapter’s probes.

## 17.3 Counter intervals: a recorder can already own the time

Consider the first edition's additive example. A perf DMA-read recorder receives ten active and two stall cycles. An MMA recorder receives five active and one stall. Sequential bookkeeping gives `12 + 6 = 18` perf cycles, six of them compute cycles. A subsequent explicit tick of six changes the total to **24**, not the compute counter. It is legitimate to tick six *new* cycles. Ticking for the MMA a second time silently changes every rate using total cycles and charges tick-based leakage again. These are historical probe values at `e918c80b6fce833cd1fcae97730fa841c2176f25`, not the timing of either experiment below.

Choose one time owner: let recorders charge their operation intervals, or let a scheduler charge deltas and record activity separately. In a model with overlap, adding local busy times is not a substitute for that scheduler. Write the interval policy down before comparing experiments. Even an apparently convenient `wall_clock_ns` derived from cycles and configured MHz is **converted model time**, not a host timer.

A snapshot also needs a contract. The v1 probe found that perf reset cleared ordinary counts but preserved frequency and the *whole* power substructure (including accumulated energy), while re-enabling the outer counter. Its diff omitted such fields as row hits/misses and wall time; merge retained the destination frequency. Some decreasing integer differences clamped to zero, but component energy differences could be negative. Standalone power diff instead subtracted unsigned activity and could wrap across a reset. Before subtracting, check object identity, counter generation, field coverage and ordering. Before merging, check clock and action definitions. A byte copy of a struct supplies none of those guarantees. These are reasons to test a lifecycle, not claims that Session 9 replayed every old case.

## 17.4 One payload, two rates

Use the same Chapter 15 record. Start a **fresh DRAM model for each arm**. At model core cycle 0 issue a 16 B read at address 0; at 64 issue an 80 B write at address 64. Read statistics at 128. DRAM and core clocks are both 1 GHz, bus width 8 B, configured peak 8 GB/s, burst granule 64 B. The observation interval **[0,128]** spans `128 − 0 = 128` core cycles, hence 128 ns. Use that same elapsed interval for *each* direction. The read does not get a 64-cycle denominator merely because the next call was issued at 64.

| Accounting over 128 ns | Exact-byte `burst_credit` | Per-request `burst_round_credit` |
|---|---:|---:|
| Requested bytes, read / write | 16 / 80 | 16 / 80 |
| Occupied bytes, read / write | 16 / 80 | 64 / 128 |
| Useful bandwidth, read / write (GB/s) | 0.125 / 0.625 | 0.125 / 0.625 |
| Occupied bandwidth, read / write (GB/s) | 0.125 / 0.625 | 0.500 / 1.000 |
| Sum across directions, useful / occupied (GB/s) | 0.75 / 0.75 | 0.75 / 1.50 |
| Payload efficiency: useful B / occupied B | 96/96 = 100% | 96/192 = 50% |

The 80 B write needs **two** rounded bursts by itself. Rounding the combined 96 B only once would predict 128 occupied bytes and erase a transaction boundary. Directional bandwidth is bytes in that direction divided by 128 ns; a byte/ns is one decimal GB/s. Thus the rounded write accounts for 1.000 GB/s of occupancy but only 0.625 GB/s of useful data. The two directional rates can be summed because their intervals are identical. The sum is not evidence of simultaneous reads and writes.

Efficiency answers “what fraction of occupied bytes was useful?” Utilization has a different denominator: at the configured 8 GB/s peak, rounded-arm useful utilization is `0.75/8 = 9.375%` and occupied utilization is `1.50/8 = 18.75%`. Neither is the 50% payload efficiency. These are **observation-window rates**, not achieved throughput. In both arms the read and write returned service estimates of 10 and 8 cycles and reported bandwidth stalls of 1,000 and 936 cycles against an initially empty bandwidth window. The calls did not consume those waits. The caller advanced the observation clock; adding service or stalls to 128 would invent a different denominator. A longer idle tail in the observation window would reduce both rates without changing the byte ratio. Do not convert the extra 96 occupied bytes into extra scratchpad writes, a latency increase or a power figure without a producer that records that effect.

Other common denominators are worth keeping beside the raw counters:

| Quantity | Numerator / denominator | Unit or trap |
|---|---|---|
| MAC throughput | recorded MACs / derived seconds | `mac_throughput_tops` divides by 10¹²: dimensionally **TMAC/s**. Multiply by two for TOPS only if one MAC counts as two operations. |
| MAC efficiency | recorded MACs / (compiled PE count × recorded cycles) | Fraction of nominal opportunities, not payload efficiency; check geometry and input consistency. |
| Scratchpad “hit rate” in the perf example | `1 − conflicts/(reads + writes)` | Count-based proxy, not a tag lookup; inconsistent counts can give a negative result. |
| Energy per MAC | component energy / MAC count | pJ/MAC, not power. |
| Average power | component energy / elapsed time | 1 pJ/ns = 1 mW. Use this as a unit check independently of any field name. |

## 17.6 Cycle models: executable does not mean integrated

A source file can compile and pass an isolated test without being linked into the ordinary runtime. Even a linked implementation needs a caller. The first-edition audit compiled `perf/cycle_model.c` separately: its `ESTIMATED` example gave `fill 6 + compute 4 + drain 4 = 14` for one tile. Its mode named `CYCLE_ACCURATE` selected private pipeline, bank, DMA and DRAM heuristics; the name was not a validation result. A 32-byte modeled write in that audit credited the attached perf **read** counter; another bridge passed an `is_read` argument where DRAM interpreted `is_write`. An isolated bank access could be called a conflict without any stall. Equal totals in attached objects did not rescue the mislabeled activity.

Those are examples of tests to repeat, not new-pin defect or suite claims. To use such a model in a new study, check build membership, trace the call from an actual workload, try one isolated read and one write, and compare private and attached state before and after reset. A route score, a returned service cost, a necessary lower bound and an elapsed schedule have different meanings even when all four are expressed in cycles.

## 17.7 Fixed process: why energy can fall as average power rises

The embedded perf estimator assigns scalar pJ costs to selected recorder actions and ticks. The old perf probe found that a cached-looking total could remain zero with nonzero components, and that its power conversion reported 1,000 mW for 1 pJ over 1 ns. **That is a historical unit check on the embedded estimator**, not a correction factor to apply to the separate table-based model below. The latter charges precision-specific MACs, register and memory actions, DMA bytes, clock cycles and area-dependent leakage. Recompute its cached total *after* recording the final action.

Run the actual public `make test-power-assumptions-sweep`. Its C fixture supplies a GEMM-*like activity count*: `64 × 64 × 256 = 1,048,576` FP16 MACs, 65,536 B in, 16,384 B out and **8,192 supplied cycles**. It records two register reads and one write per MAC, one scratchpad action per four endpoint bytes, 1,024 DRAM read transactions and 256 writes (both calls specify a page hit), 81,920 DMA bytes, and 8,192 clock-tree charges. It does not execute a GEMM, validate its output, or ingest the two DRAM calls of §17.4.

Hold the table at **7nm**. Hold geometry at 16 × 16 with 128 KiB weight scratchpad and 1,024 KiB global buffer for the area estimate. Hold all action counts fixed. Only the modeled clock changes in the three `7nm_clock` arms. Here is the unmodified program's output, with each row checked independently at display precision:

| 7nm clock (MHz) | 8,192 cycles (µs) | Total (µJ) | Average (mW) | Area (mm²) | MAC / DRAM / leakage share (%) |
|---:|---:|---:|---:|---:|---:|
| 750 | 10.923 | 0.588289 | 53.859 | 3.647 | 35.65 / 27.85 / 33.86 |
| 1500 | 5.461 | 0.488688 | 89.481 | 3.647 | 42.91 / 33.53 / 20.38 |
| 2500 | 3.277 | 0.448848 | 136.977 | 3.647 | 46.72 / 36.50 / 13.31 |

To reconstruct a row, first sum the terms that **do not** change with clock: MAC 209,715.20 pJ; register file 12,582.912; scratchpad 2,048; DRAM 163,840; DMA 819.200; clock tree 81.920. Total dynamic energy is **389,087.232 pJ**. The clock cost stays fixed because the *count of cycles* stays fixed. The area proxy is `[256 × 160 + (128 + 1024) × 2400] × 1.30 / 10⁶ = 3.647488 mm²`. The table's leakage density of 5 mW/mm² then gives a constant leakage power of 18.23744 mW.

At 1500 MHz, the time is `8192/1500` µs. Multiply that **unrounded** time by 18.23744 mW and by 1,000 pJ/(mW·µs): leakage is about 99,601 pJ. Add it to the dynamic subtotal to obtain 0.488688 µJ at display precision. Dividing the unrounded energy by the unrounded time gives 89.481 mW. The MAC share rises at the higher clock even though the model charges exactly the same MAC energy: leakage makes up a smaller part of the denominator. Energy falls because leakage accrues for less time; average power rises because the same dynamic work is charged over a shorter time.

The public test prints six `node_nominal` rows as well. Comparing, for example, 45nm/800 MHz with 3nm/3000 MHz changes *two* assumptions. It cannot isolate the effect of clock. The additional 7nm/2000 MHz nominal row is a useful same-table cross-check, not a fourth `7nm_clock` arm. These are fixed-coefficient, fixed-activity estimates. There is no voltage sweep, timing-closure test, thermal feedback, floorplan, RTL reference, or silicon observation. This is not DVFS or evidence that any implementation can run at 2500 MHz.

## 17.8 Trace the configuration into the consumer

The first edition described geometry and DRAM bandwidth as proxies for process and frequency. At this pin those are the **AUTO fallback**, not the only choice. The full config has `power.tech_node` and `power.clock_freq_mhz`; an explicit node selects a table and a nonzero validated clock selects the MHz value. Zero requests auto clock selection. In `tu_power_model_from_config`, an explicit node supersedes the geometry heuristic, and a nonzero clock supersedes the bandwidth heuristic. The helper uses `counters_enabled` to enable the model and supplies the area estimate used on the subsequent tick.

Follow the route actually tested: `tu_config_default` → explicit C fields → `tu_config_validate` → `tu_power_model_from_config` → action recorders → tick → total → report. This sweep proves the explicit **C-config-to-standalone-model** route for its cases. It did not run a JSON parser A/B, regenerate YAML headers, attach energy accounting to an ordinary operator, or gate every trace flag. For any such claim, distinguish a value merely shipped in a file, initialized by default, parsed and retained, and actually read by the named consumer. A distinguishing A/B changes an effective consumer setting and holds the work constant. [Chapter 4](04-configuration-as-the-architecture-contract.md) applies that method to runtime configuration.

[Next: Chapter 18 — Runtime Context Retention and Preemption Boundaries](18-runtime-context-retention-and-preemption-boundaries.md)
