# Chapter 15 — DRAM Service Models and Bandwidth Claims

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

## Learning objectives

After this chapter, you should be able to:

1. identify whether a DRAM number came from a preset declaration, stateless bulk estimator, caller-ticked stateful access, cumulative statistic, hierarchy wrapper, separate cycle model, or historical analytical report;
2. distinguish base latency, returned stall, caller time, channel availability, bandwidth-window state, and elapsed completion time;
3. derive the HBM2 first-access, refill, channel-contention, and fixed-window admission results from the pinned equations;
4. explain why the bandwidth admission path double-counts traffic and why reset is not equivalent to fresh construction;
5. trace DRAM fields independently through JSON loading, YAML generation, compiled constants, full-config consumers, runtime conversion, and manual construction;
6. state the hierarchy and descriptor-DMA integration boundaries without promoting archive linkage or focused tests into ordinary-operation reachability;
7. recompute a historical type×clock sweep and reject its recommendations when its own equations contradict its table; and
8. compare DRAM-model alternatives across performance, area/power, control complexity, configuration, and verification cost without treating preset names as physical-device validation.

## Prerequisite graph

This chapter assumes:

- Chapter 2's evidence ladder and snapshot-conformance discipline;
- Chapter 4's distinction among declared, parsed, converted, retained, consumed, and effective configuration;
- Chapter 9's separation of the generic SRAM, hierarchy, and cycle-model memory surfaces;
- Chapter 10's distinction among byte effects, descriptor service estimates, explicit ticks, and elapsed completion; and
- Chapter 12's rule that linked, tested, and adjacent model surfaces do not automatically form one integrated system.

```text
Chapter 2 evidence discipline
          │
          ├──── Chapter 4 configuration ladders
          ├──── Chapter 9 distinct memory surfaces
          ├──── Chapter 10 bytes vs service vs elapsed time
          └──── Chapter 12 integration and cycle-domain discipline
                         │
                         ▼
          Chapter 15 DRAM service models and bandwidth claims
```

This chapter does not reopen descriptor ownership, SRAM banking, pipeline overlap, or the complete performance-counter and power contracts. Chapter 10 owns descriptor DMA; Chapter 16 will own double buffering and legal overlap; Chapter 17 will own cross-producer measurement provenance.

## Opening architecture question: what does a number labeled “DRAM cycles” actually mean?

Suppose an architecture report says that a 64-byte HBM2 read costs 51 cycles. A second trace says the first read returns 50 cycles and 1,000 stall cycles. A statistics printout reports 1,024 GB/s and 400% utilization. A hierarchy call returns a 1,000-cycle stall while leaving the destination buffer untouched. These statements can all be reproduced at the same pinned revision—and they do not describe one event.

The 51 is a **stateless estimate**: `ceil(64/256) + 50`. The 50 and 1,000 are two outputs from a **stateful access call** whose bandwidth budget starts empty. The 1,024 GB/s and 4.0 utilization are **cumulative arithmetic** over bytes divided by caller-advanced time, clamped only by `max(current_cycle,1)`, not by peak bandwidth. The hierarchy wrapper delegates to the stateful model but retains only the stall, discards the 50 base cycles, and performs no DRAM backing-store copy.

None of these values is elapsed memory completion time. No request queue, completion event, command scheduler, data bus transfer, bank machine, refresh mechanism, or calibrated timing reference connects them. The correct reader decision is therefore not “Which DRAM type is fastest?” It is:

1. Which surface produced the number?
2. Which state, clock, and equation did that surface use?
3. Which configuration path reached it?
4. Is the quantity an implemented declaration, deterministic analytical result, integration observation, historical calculation, or calibrated physical claim?
5. Which conclusions remain safe after the omitted mechanisms and known defects are made explicit?

The source basis is the frozen edition commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. The sole predraft evidence authority is canonical v3, `experiments/runs/ch15-dram/20260804-ch15-canonical-v3/`. Exact hashes, predicates, mutation controls, focused suites, probe output, historical recomputation, and containment checks are recorded in the [Chapter 15 audit](../../experiments/ch15-dram-audit-2026-08-04.md).

### Source map

| Contract | Exact pinned source or evidence |
|---|---|
| standalone presets, estimator, stateful access, ticks, reset, and statistics | `tu_cmodel/memory/dram_model.{h,c}` |
| hierarchy construction and DRAM delegation | `tu_cmodel/memory/memory_hierarchy.{h,c}` |
| descriptor-DMA integration boundary | `tu_cmodel/dma_descriptor.c` |
| JSON loader, runtime conversion, and direct power consumer | `tu_cmodel/infra/config.{h,c}`, `tu_cmodel/tu_config.h`, `tu_cmodel/perf/power_model.c` |
| YAML generator and compiled constants | `config/tu_config.yaml`, `scripts/gen_config.py`, generated `tu_config.h` |
| focused tests | `tests/test_dram.c`, `tests/test_memory_hierarchy.c`, `tests/test_cycle_model.c`, `tests/test_power_model.c`, `tests/test_config.c` |
| separate DRAM abstraction | `tu_cmodel/perf/cycle_model.{h,c}` |
| current/historical documentation | `docs/dram-model.md`, `docs/bandwidth-modeling.md`, `docs/exploration/dram-type-clock-sweep.md` |
| sealed executable evidence | `experiments/runs/ch15-dram/20260804-ch15-canonical-v3/` |

All repository paths refer to the pinned edition. Documentation supplies claims to audit; it does not override reproduced source behavior.

---

## 15.1 Begin with the producer, not the DRAM label

The pinned tree contains several adjacent surfaces that use DRAM vocabulary. They must be classified before any number is interpreted.

| Producer | State | Output | Safe use | Unsafe promotion |
|---|---|---|---|---|
| preset/custom record | parameters only | bandwidth, latency, channels, geometry labels | inspect implemented defaults and parameter sensitivity | validated HBM/DDR device model |
| `tu_dram_estimate_transfer` | stateless | one scalar estimate | compare bytes/bandwidth plus selected latency under fixed 1 GHz arithmetic | scheduled or contention-aware completion time |
| `tu_dram_read/write` + `tick` | caller-ticked mutable state | base cycles and stall separately; counters mutate | reproduce exact state transitions and accounting | queued memory-controller execution |
| `tu_dram_get_stats` | cumulative access state plus caller time | bytes, cycle sums, derived GB/s/utilization | inspect source-defined cumulative arithmetic | clamped achieved bandwidth or measured utilization |
| memory hierarchy | own tick plus embedded standalone model | hierarchy counters and standalone stall only | study delegation boundary | DRAM byte storage or ordinary execution feed |
| `perf/cycle_model` DRAM channel | separate source-linked model | different row/bank timing and counters | contrast abstraction boundaries | the same model as `memory/dram_model.c` |
| historical type×clock report | independent equations | analytical table and recommendations | forensic equation audit and hypothesis generation | live-model or calibrated decision evidence |

This producer-first table is the chapter's main tool. A field named `cycles`, a statistic named “effective bandwidth,” or a report headed “DRAM sweep” does not establish common semantics. Each quantity inherits the state, assumptions, and omissions of its own producer.

The evidence ladder is likewise per surface:

```text
source present -> archive member -> focused test -> non-test caller
-> ordinary operation integration -> shared timeline -> external calibration
```

The standalone DRAM implementation reaches the **non-test-caller** rung because `memory_hierarchy.c` delegates to it, and canonical v3 executes that delegation. It does not reach ordinary-operation integration. The hierarchy reaches archive membership and a focused suite but has no external non-test caller of its own. Descriptor DMA does not call `tu_dram_*`. Thus the two surfaces stop at different rungs, and neither reaches an ordinary operation, shared timeline, or external calibration.

---

## 15.2 The stateless estimator answers one narrow question

`tu_dram_estimate_transfer(dram, num_bytes, is_read)` does not execute an access. For a non-ideal model it computes

```text
bandwidth_bytes_per_cycle = bandwidth_gbps × 10^9 / 10^9
estimate = ceil(num_bytes / bandwidth_bytes_per_cycle)
           + (read_latency_cycles or write_latency_cycles).
```

The two factors of `10^9` cancel, so the numeric GB/s value is treated as bytes per cycle under a fixed 1 GHz assumption. For the HBM2 preset, `bandwidth_gbps=256` and read latency is 50 cycles. A 64-byte read therefore gives

```text
ceil(64/256) + 50 = 1 + 50 = 51 cycles.
```

For HBM3, 819 bytes at 819 GB/s and 40-cycle read latency give

```text
ceil(819/819) + 40 = 41 cycles.
```

Canonical v3 prints exactly `ESTIMATE hbm2_read64=51 hbm3_read819=41`.

What does the estimate omit? It does not inspect `current_cycle`, per-channel availability, pending bytes, the bandwidth window, row mode, bus width, burst length, channel count, bank count, or row size. Calling it does not mutate statistics or reserve future capacity. The latency is simply added once, independent of transfer shape and address. It is therefore a **deterministic analytical estimate** for bulk payload service under a named parameter record—not a simulation of a request flowing through a controller.

This distinction explains why “51 cycles” cannot be reconciled by adding or subtracting the stateful call's outputs. The estimator and access API answer different questions. A useful estimator comparison keeps bytes, preset, direction, and fixed 1 GHz arithmetic constant. It does not establish physical ordering, sustainable throughput, or overlap with compute.

The ideal type is a special sentinel: the estimator returns zero, and ideal accesses return zero cycles/stalls while incrementing access and byte counters. It still has no backing store. “Ideal” therefore means zero-cost accounting behavior, not infinitely fast functional memory carrying data.

---

## 15.3 The stateful access contract separates service fields from time

A newly allocated non-ideal model is zero-initialized:

```text
current_cycle = 0
bw_window_size_cycles = 0
bandwidth_available = 0
channel_available_cycle[*] = 0.
```

The first access calls `ensure_bandwidth`. That helper establishes a 1,000-cycle window and records its start, but it fills the budget only when

```text
current_cycle - bw_window_start >= bw_window_size_cycles.
```

At cycle zero the condition is false. The budget remains zero. For a 64-byte HBM2 read at address zero, the API therefore returns:

```text
cycles_out = 50
stall_out = 1000
current_cycle = 0
bandwidth_available = 0
pending_read_bytes = 64
channel_available_cycle[0] = 50.
```

The crucial point is that the access does **not** advance `current_cycle`. The caller must invoke `tu_dram_tick()` explicitly. The 50 is the selected base latency; the 1,000 is accumulated contention accounting. Neither is a completion timestamp. The model records channel availability at `current_cycle + base_latency`, but it does not enqueue a request or later emit a completion.

### Channel bookkeeping is overwritten, not queued

Channel selection is

```text
channel = (addr / burst_length) % num_channels.
```

With the HBM2 burst length of 64 bytes and eight channels, addresses 0 and 64 select channels 0 and 1. At fixed caller time zero:

- the first channel-0 read records availability 50;
- a second channel-0 read sees the 50-cycle availability gap and returns stall 1,050 (50 channel + 1,000 bandwidth-window);
- a channel-1 read returns stall 1,000 because that channel was fresh;
- a third channel-0 read again returns 1,050, not 1,100.

Why does the third request not accumulate another service slot? Every access sets

```text
channel_available_cycle[channel] = current_cycle + base_latency,
```

so fixed-time accesses overwrite the same value 50. There is no `max(old_available,current_cycle)+service` queued update. Canonical v3 prints availability behavior `1000, 1050, 1050`. The safe description is **per-channel availability bookkeeping**. “Concurrent request queue,” “serialized channel service,” and “completion schedule” are overclaims.

### Exactly 1,000 caller ticks refill the budget

Each call to `tu_dram_tick()` increments current time once and then checks the window. At exactly cycle 1,000, HBM2 refills

```text
256 bytes/cycle × 1,000 cycles = 256,000 bytes.
```

Pending counters are reset. A following 64-byte access on an available channel returns base cycles 50, stall 0, and leaves 255,936 bytes. This is a fixed-window refill driven by caller ticks. It is not sliding-window accounting, and time does not move unless the caller explicitly advances it.

---

## 15.4 Two state defects bound every bandwidth claim

The stateful path is executable, but executable does not mean faithful. Two discriminating probes show why it must not be described as enforcing the advertised bandwidth.

### Admission double-counts prior traffic

After refill, the implementation tracks both:

- cumulative `pending_read_bytes + pending_write_bytes`, which increases after each request; and
- `bandwidth_available`, which decreases after each request.

Admission then compares

```text
pending_read_bytes + pending_write_bytes + request_bytes
    > bandwidth_available.
```

Prior traffic appears on both sides: once as growing pending bytes and once as shrinking remaining budget. For fixed-time 64-byte HBM2 reads after a 256,000-byte refill, request `n` is admitted without a bandwidth-window stall only while

```text
64(n-1) + 64 <= 256000 - 64(n-1)
128n <= 256064.
```

Thus `n <= 2000`; request **2,001** first receives the **bandwidth-window stall**. Earlier repeated-channel requests may already carry channel stalls, so 2,001 is an admission threshold, not the first nonzero stall of any kind. At that point only 128,000 prior bytes have been issued—half the nominal 256,000-byte window. After accounting the request, the probe prints `pending=128064` and `budget=127936`.

This is not a faithful token bucket, and it does not enforce 256 GB/s. It is a deterministic defect in the admission equation. Comparisons that keep the defect fixed may still reveal source-defined sensitivities, but a physical bandwidth conclusion would inherit a two-sided accounting error.

### Reset retains stale window state

`tu_dram_reset()` clears statistics, current time, budget, pending counters, and channel availability. It does **not** clear `bw_window_start` or `bw_window_size_cycles`.

If caller ticks have moved the window start to 1,000, reset sets `current_cycle=0` while retaining `bw_window_start=1000` and size 1000. The next access evaluates unsigned subtraction:

```text
current_cycle - bw_window_start = 0 - 1000,
```

which wraps to a very large value and immediately satisfies the refill condition. The first post-reset access then returns stall 0 and leaves 255,936 bytes, unlike a fresh model's first access, which returns a 1,000-cycle bandwidth stall.

Reset is therefore history-dependent and not fresh-construction-equivalent. A superficial reset test performed before moving the window start cannot expose the defect. Any experiment that compares phases across reset must either reconstruct the model or explicitly account for the stale window fields.

These findings illustrate a general verification rule: state-machine probes must cross the discriminating boundary. One access after refill would not expose double accounting; reset at initial state would not expose stale-window history.

---

## 15.5 Row mode, statistics, and clock controls are narrower than their names

### Row mode is a flat read-only penalty

When `model_row_conflicts` is enabled, every **non-ideal standalone** read adds ten base cycles and increments `total_row_conflicts`; ideal reads return early with zero cost. No address-derived row identity, open-row register, hit state, bank state, precharge timing, activation timing, or replacement policy exists. Writes have no row-mode branch.

Canonical v3 demonstrates a row-enabled read returning 60 base cycles and one conflict, followed by a write returning 50 base cycles. The safe label is **optional flat read penalty**. “Row hit/miss model,” “row-buffer behavior,” and “conflict rate” are rejected for the standalone surface. The separate `perf/cycle_model` does carry open-row state, but that is a different model (15.8), not evidence that the standalone path does.

### Derived bandwidth is bytes divided by caller ticks

`tu_dram_get_stats()` computes elapsed denominator as `max(current_cycle,1)`. It then reports

```text
effective_read_bandwidth = total_read_bytes / denominator
                           × 1 GHz / 10^9
effective_write_bandwidth = analogous
utilization = (read_bandwidth + write_bandwidth) / preset_peak.
```

A 1,024-byte read recorded at cycle zero therefore reports 1,024 GB/s and utilization `1024/256 = 4.0` on HBM2. These values are neither clamped nor coupled to returned stalls. They are cumulative caller-clock-dependent ratios. “Effective” and “utilization” are field names, not proof of achieved bandwidth.

A valid report must name the interval and caller ticks. If accesses are recorded without ticks, the denominator stays one; if a caller advances time independently, the ratios change even though no queued bytes complete. These statistics are useful for auditing the accounting surface itself, but not for claiming sustained traffic.

### One setter is a no-op; one helper takes an independent clock

`tu_dram_set_core_clock()` discards both arguments. The estimator, window refill, and derived statistics retain their internal 1 GHz assumption. By contrast, `tu_dram_peak_bw_per_cycle(dram, core_clock_ghz)` accepts a caller-provided clock and computes a separate conversion. HBM2 yields 256 B/cycle at 1 GHz and 128 B/cycle at 2 GHz, without mutating the model. The sealed probe confirms that the 64-byte estimate remains 51 before and after calling the no-op setter.

The model therefore has no single effective clock setting. Every clock-dependent claim must name its producer: fixed 1 GHz internal arithmetic or the peak helper's explicit argument.

---

## 15.6 Presets are implemented declarations, not device validation

The standalone model declares ideal, HBM2, HBM2e, HBM3, DDR4, DDR5, LPDDR5, and custom records. The HBM2 record, for example, names 256 GB/s, 50-cycle read/write latency, 128-byte bus width, 64-byte burst, eight channels, sixteen banks per channel, and a 2,048-byte row buffer.

Only a subset affects execution:

| Field | Stateful access effect | Estimator effect | Qualification |
|---|---|---|---|
| bandwidth | window budget/admission | bytes-per-cycle term | admission is double-counted; fixed 1 GHz |
| read/write latency | base cycles and channel availability | added latency | no completion queue |
| channels | availability-array size and address mapping | none | no queued channel service |
| burst length | channel mapping divisor | none | zero can be unsafe with multiple channels |
| row-mode flag | flat +10 on reads | none | no row identity/state |
| bus width | none | none | decorative in these equations |
| banks per channel | none | none | decorative |
| row-buffer size | none | none | decorative |
| preset clock | none in active equations | none | separate no-op core-clock setter |

A preset name is therefore a convenient parameter bundle, not a calibrated representation of an HBM2 or DDR5 device. No audited evidence compares latency, sustained bandwidth, row behavior, energy, area, or timing distributions against RTL, DRAMSim/Ramulator, FPGA, silicon, or measured device traffic.

Custom construction broadens the hazard. `tu_dram_create_custom()` copies parameters without validation. Zero channels can lead from a zero-length allocation to an index-0 access; multiple channels with zero burst length can divide by zero; negative or non-finite bandwidth, zero geometry, and arbitrary latency values are accepted. The audit records these paths statically and does not execute undefined behavior. Type checks also reject only `type >= COUNT`: on the pinned GCC C ABI the all-nonnegative enum is represented unsigned, so casting `-1` is rejected by that comparison, but a signed-enum implementation or C++ caller could let a negative value index before the preset/name arrays. This is an implementation-dependent portability hazard, not reproduced pinned-C behavior. Safe experiments validate custom parameters before construction and never execute invalid cases merely to prove they are hazardous.

---

## 15.7 Configuration is six paths, not one pipeline

The word “configured” hides materially different routes. Chapter 4's ladder must be applied separately to each DRAM field.

### JSON loading

The full-config loader reads JSON. It parses DRAM type, bandwidth, row mode, and memory read/write latency. `core_clock_ghz` is ignored. `dram_channels` remains its default because the shipped JSON has no channels key and the parser has no reader. Unsupported DRAM strings silently map to ideal. Full-config validation does not enforce valid DRAM type, positive finite bandwidth, channel count, latency, or clock.

The canonical probe loads a configuration with HBM3, 777.0 GB/s, row mode enabled, and read/write latencies 33/44. Those values land in the full config: `type=3 bw=777.0 row=1 rlat=33 wlat=44`.

### YAML generation and compiled constants

`scripts/gen_config.py` reads the shipped YAML, not the JSON. It emits DRAM latency macros but does not emit type, bandwidth, channels, row mode, or core clock. The tracked compiled header also carries its own constants. YAML-generated latency, JSON-loaded fields, and compiled constants are separate authorities; similarity among defaults does not prove propagation.

### Runtime conversion and construction

`tu_config_to_runtime()` drops every DRAM field. No full/runtime-config path constructs the standalone model. An explicit caller may manually pass the parsed `dram_type` enum to `tu_dram_create`, but enum construction selects the preset's bandwidth and row mode—not the JSON overrides. In the probe, manually constructing the parsed HBM3 enum gives 819 GB/s and row mode off, not the parsed 777 GB/s and row mode on.

### A separate full-config power consumer

`tu_power_model_from_config()` directly reads `dram_bandwidth_gbps` and uses `>500` as a heuristic to choose 2 GHz instead of 1 GHz. The linked power suite passes 20/20. This does not propagate bandwidth into standalone DRAM; it proves a distinct full-config consumer with a different purpose and model domain.

The safe ladder is therefore:

```text
JSON parse ───────────────> full config ──> power heuristic
                               │
                               └──X runtime conversion

YAML ──> generator ──> latency macros
tracked header ──────> compiled constants
manual enum call ────> standalone preset construction
```

A configuration claim must name the path and consumer. “The DRAM config selects model behavior” is false without that qualification. `tests/test_config.c` contains no DRAM assertion, so parser presence is not backed by a discriminating focused config test at this pin.

---

## 15.8 Integration stops before ordinary data movement

### Hierarchy delegation

`tu_mem_hierarchy_init()` constructs HBM2 unconditionally, falling back to ideal only if allocation fails. It does not use full/runtime config or a compiled DRAM-type selection. A hierarchy DRAM read/write calls the standalone model with local `cyc` and `st` outputs, discards `cyc`, retains only `st`, and updates hierarchy counters.

The hierarchy has no DRAM backing store. A 64-byte read into a 64-byte sentinel leaves **every byte unchanged**. Canonical v3 reports `rc=0 stall=1000 unchanged64=1 dram_cycle=0`: successful delegation, the standalone first-window stall, no byte effect, and no implicit tick. Hierarchy time advances only through `tu_mem_hierarchy_tick`, which separately increments hierarchy time and invokes one standalone DRAM tick per cycle.

The hierarchy is linked and its focused suite passes 10/10. Yet outside `memory_hierarchy.c` itself, no non-test C source calls its init/read/write/tick API. It is a demonstrated wrapper surface, not an ordinary execution path.

### Descriptor DMA

Descriptor DMA contains no `tu_dram_*` call. Its `50 + ceil(bytes/32) + SRAM penalty` service estimate, described in Chapter 10, remains independent. The standalone header's claim that DMA queries the DRAM model is documentation intent, not current reachability. A descriptor transfer does not reserve standalone bandwidth, alter its channels, or consume its latency.

### Separate cycle-model DRAM

`tu_cmodel/perf/cycle_model.{h,c}` implements another DRAM channel with actual open-row state and different equations. Its DRAM channel retains its own hit/miss/byte/stall state; the encompassing transfer records through the DMA performance-counter path, not the standalone DRAM counter fields. At the pin it is source-present but absent from `TU_OBJS`; the chapter runner links it directly and its focused suite passes 21/21. That result establishes executable behavior for a separate source-linked surface—not archive integration, standalone-DRAM counter integration, or identity with `memory/dram_model.c`.

These boundaries prevent a tempting fictional pipeline:

```text
config -> descriptor DMA -> hierarchy -> standalone DRAM -> cycle-model row state
```

No such chain exists. The actual evidence is a set of adjacent surfaces with different configuration authorities, callers, clocks, state, and outputs.

---

## 15.9 Historical sweeps are hypotheses until their arithmetic survives

`docs/exploration/dram-type-clock-sweep.md` analyzes 42 DRAM-type×clock combinations for GEMM 128×128×256. It states:

```text
total DMA bytes = 196,608
compute cycles = 16,416
bus limit = 32 B/cycle
effective bandwidth = min(32, DRAM_GB/s / clock_GHz)
DMA cycles = bytes / effective bandwidth
total cycles = DMA cycles + compute cycles
TOPS = 8,388,608 operations × clock_GHz / total cycles / 1,000.
```

This report does not call `dram_model.c`. It is a separate analytical formula. Its printed methodology omits the final GHz-to-TOPS `/1,000` conversion; canonical v3 applies that necessary unit conversion, fingerprints the historical document, and recomputes representative rows from its own constants.

At 8 GHz:

| Type | Effective B/cycle | DMA cycles | Total cycles | Recomputed TOPS | Historical table |
|---|---:|---:|---:|---:|---:|
| HBM2 | 32.0 | 6,144 | 22,560 | **2.975** | 2.839 |
| DDR5 | 6.4 | 30,720 | 47,136 | **1.424** | 0.776 |
| DDR4 | 3.2 | 61,440 | 77,856 | **0.862** | 0.435 |

At 1 GHz, DDR4's 25.6 B/cycle gives about 0.348 TOPS, approximately 6.4% below ideal. That contradicts the report's actionable conclusion that DDR4, DDR5, and HBM deliver identical performance and that DRAM type is a “don't-care” at 1 GHz.

The result is not that analytical sweeps are useless. Their crossover equation is a useful hypothesis generator: bus width, clock, payload, and DRAM bandwidth jointly define regimes. The lesson is that a table must survive recomputation before its recommendation can be used. Here material rows and prose conclusions contradict the report's own constants, so the report is **Historical** and rejected as decision evidence. Its values must not be silently promoted into live-model results.

Even a corrected table would remain an uncalibrated analytical study. It serially adds DMA and compute, assumes one payload count and mapping, ignores latency amortization details, queues, refresh, row locality, controller policy, overlap, power, capacity, packaging, and software effects. Roofline supplies safe vocabulary—performance is bounded by compute peak and bandwidth times operational intensity—but not a latency simulator or validation of these equations ([WAT09](../../references/foundations.md#wat09-roofline-model)).

---

## 15.10 A decision workflow for safe bandwidth claims

1. **Name the producer.** State preset, estimator, stateful access, stats, hierarchy, cycle model, or historical formula. Never write only “DRAM cycles.”
2. **Name the interval and clock.** For stateful access, give caller tick history and window state. For estimates, state the fixed 1 GHz assumption. For historical formulas, state the independent clock argument.
3. **Separate outputs.** Report base latency, stall, current cycle, channel availability, and cumulative counters separately. Do not construct elapsed completion by adding fields unless a producer defines that operation (none here does).
4. **Trace configuration to the consumer.** Identify JSON, YAML generator, compiled constant, full-config direct consumer, runtime conversion, or manual enum construction. Require a discriminating effect, not just parsing.
5. **Check integration.** Prove a non-test caller and ordinary-operation route. Archive membership and a green suite stop below integration.
6. **Cross the state boundaries.** Test initial empty budget, exact 1,000-tick refill, request 2,001, fixed-time repeated-channel accesses, and reset after moving the window start.
7. **Recompute reports.** Evaluate formulas and conclusions independently. Preserve contradictory reports as historical forensic evidence, not as current recommendations.
8. **State calibration.** No Chapter 15 quantity is calibrated. A physical claim requires a named external reference, traffic trace, clock mapping, error metric, and representative regimes.

A well-formed statement looks like this:

> **Executable / Analytical model / Estimated:** At Tusim commit `e918c80`, a freshly constructed HBM2 standalone model, before caller ticks, returns base latency 50 cycles and bandwidth-window stall 1,000 cycles for a 64-byte read; the access does not advance time or move bytes. This reproduces source accounting, not physical HBM2 latency.

That sentence names the surface, pin, initial state, workload, units, outputs, omission, and calibration boundary.

---

## 15.11 Trade-offs among model alternatives

| Alternative | Useful regime | Performance meaning | Area/power and complexity | Configuration and caller/runtime obligation | Verification burden |
|---|---|---|---|---|---|
| ideal sentinel | isolate functional consumers from service cost | zero cycles/stalls; counters only | minimal | explicit construction; current config/runtime path does not select it | ensure no physical conclusion leaks from ideal runs |
| stateless bulk estimator | early payload and latency sensitivity | `ceil(bytes/BW)+latency` at fixed 1 GHz | no controller state; cheapest model | caller supplies bytes/direction and chooses a preset manually | equation/unit tests and overflow/parameter guards |
| repaired fixed-window meter | coarse sustained-budget experiments | deterministic admission per caller-ticked epoch | small counters; no queue | caller owns ticks/reset and must propagate config explicitly | exact threshold, reset, mixed read/write, and interval tests |
| faithful token bucket | burst tolerance plus rate enforcement | token replenishment and debt under explicit time | more arithmetic/state; still no controller | runtime must define clock, tick ownership, and parameter validation | invariants, saturation, precision, reset, long traces |
| queued channel model | ordering and per-channel occupancy | request start/completion under named scheduling | queues, arbitration, backpressure; larger area/power proxy | operation/DMA route must create requests and consume completion events | event ordering, fairness, capacity, deadlock, cancellation |
| bank/row timing model | locality and controller-policy studies | row hits/misses, activation/precharge/refresh under stated abstraction | bank machines and policy complexity | compiler/runtime must preserve address trace and mapping semantics | differential traces against a trusted simulator/RTL |
| trace/calibrated model | physical technology decisions | error-bounded predictions for named workloads/devices | characterization and data infrastructure | versioned trace ingestion, device/config identity, and replay ownership | calibration split, confidence/error reporting, drift tests |

No alternative is universally best. A stateless estimator is easier to reason about and cheap to verify, but cannot answer contention questions. A repaired fixed-window meter can expose rate sensitivity without controller complexity, but burst shape and fairness remain absent. A queued bank/row model can study locality and arbitration, but grows state space, control complexity, and verification cost. Calibration adds confidence only within the characterized workload, technology, clock, and policy domain.

Technology choice also has costs outside this chapter's model: HBM may offer bandwidth but changes packaging, area, power, capacity, cost, and verification; DDR may be sufficient in a bus-limited regime but can become the bottleneck as operational intensity, clock, or bus width changes. Tusim's preset table models none of those physical trade-offs. It can preserve alternatives and generate questions; it cannot select a device by name.

---

## 15.12 Verification evidence and test provenance

Canonical v3 is the sole predraft evidence authority. It seals 23 source/config/test/document hashes and 62 structural/reachability predicates (85 checks total). A live source mutation fails the hash audit and restoration passes, proving the source gate is fail-closed.

The runner proves `dram_model.o` and `memory_hierarchy.o` are archive members and uses static/source-explicit linkage to avoid stale shared-library selection. Results:

| Suite or probe | Canonical v3 result | Meaning |
|---|---:|---|
| standalone DRAM focused suite | 12/12 | broad API/preset/counter checks; aggregate `make test` member |
| hierarchy focused suite | 10/10 | wrapper behavior under focused construction |
| separate cycle model | 21/21 | source-linked, not an archive member |
| power model | 20/20 | linked separate full-config consumer |
| mutated DRAM suite | 11/12, `wrong BW`, inferior code 01 | negative gate is live |
| discriminating Chapter 15 probe | zero failures | exact state/integration boundaries |
| historical sweep recomputation | four contradictions | report rejected as decision evidence |

The runner parses GDB inferior status explicitly. Passing binaries must say `exited normally`; the deliberate mutation must say `exited with code 01`. GDB's own process status is not accepted as the inferior status.

The 12/12 standalone suite does not cover the initial empty budget, double-counted admission threshold, moved-window reset, returned-cycle/stall separation, fixed-time overwrite behavior, row read/write asymmetry, over-peak statistics, invalid custom geometry, config reachability, hierarchy byte effects, or descriptor integration. The custom probe and source predicates cover those boundaries. Test success is evidence for the assertions the test actually makes, not a certificate for every documentation claim.

---

## 15.13 Fidelity box: what remains unknown

> **Executable:** standalone DRAM and hierarchy are archive-linked and focused-tested; the separate cycle model is source-linked by the chapter runner. Exact canonical state transitions are reproduced.
>
> **Integrated:** hierarchy delegates to standalone DRAM internally, but no non-test hierarchy caller is demonstrated. Descriptor DMA does not call standalone DRAM. Runtime conversion drops all DRAM fields.
>
> **Analytical model / Estimated:** estimator results, bandwidth-window stalls, channel bookkeeping, cumulative bandwidth/utilization, cycle-model results, power heuristics, and historical sweep equations are deterministic source-defined arithmetic. They are not measured elapsed time.
>
> **Historical:** the type×clock report is a separate formula with material arithmetic and conclusion contradictions; it is forensic evidence only.
>
> **Calibration:** none against RTL, FPGA, silicon, DRAMSim/Ramulator, or measured device traffic.

The evidence does not establish queued completion, backing-store byte effects, a faithful token bucket, row-hit behavior in the standalone model, refresh/turnaround/timing constraints, sustainable bandwidth, physical latency, area, power, energy, device recommendations, or a shared timeline with DMA/SRAM/compute. It also excludes unsafe custom parameter and negative-enum execution.

---

## 15.14 Failure modes

1. **Producer erasure.** Writing “DRAM cycles=51” without saying that 51 came from the stateless estimator.
2. **Adding base and stall into elapsed time.** The access does not advance time or schedule completion; the outputs remain separate ledgers.
3. **Calling the meter a token bucket.** Pending traffic and remaining budget double-count prior bytes; HBM2 first receives the bandwidth-window stall at request 2,001 after only 128,000 prior bytes.
4. **Resetting between phases.** Reset retains stale window start/size and can make the first post-reset access differ from fresh construction.
5. **Promoting row mode.** A flat +10 on every non-ideal standalone read is not row-buffer hit/miss state.
6. **Trusting field names.** “Effective bandwidth,” “utilization,” and “row conflicts” are wider names than the implemented arithmetic.
7. **Conflating configuration routes.** JSON parse, YAML generation, compiled constants, power consumption, runtime conversion, and manual construction are independent.
8. **Promoting linkage to integration.** A linked hierarchy with 10/10 tests still has no non-test caller; descriptor DMA does not query standalone DRAM.
9. **Importing historical tables.** The 8-GHz rows and 1-GHz conclusion contradict the report's own equations.
10. **Treating presets as physical devices.** Names and constants are uncalibrated declarations with decorative geometry fields.

---

## 15.15 Summary

Tusim's DRAM territory is not one timing model. It is a collection of adjacent producers whose outputs must remain separate:

1. The stateless estimator returns `ceil(bytes/bandwidth)+latency` under fixed 1 GHz arithmetic (HBM2 64-byte read = 51; HBM3 819-byte read = 41).
2. Stateful access returns base cycles and stalls separately and never advances caller time. The first HBM2 access returns 50 and 1,000 at cycle zero.
3. Channel availability is overwritten, not queued (`1000,1050,1050` fixed-time stalls); exactly 1,000 ticks refill 256,000 HBM2 bytes.
4. Bandwidth admission double-counts prior traffic, first adding the bandwidth-window stall at request 2,001 after 128,000 prior bytes, and reset retains stale window state.
5. Row mode is a flat read-only +10 penalty; derived bandwidth/utilization can exceed nominal peak; the core-clock setter is a no-op.
6. JSON, YAML generation, compiled constants, full-config power consumption, runtime conversion, and manual preset construction are different routes. Runtime conversion drops all DRAM fields.
7. Hierarchy delegation drops base latency and moves no DRAM bytes; it has no non-test caller. Descriptor DMA does not call standalone DRAM. The separate cycle model is source-present/non-archive and not the same surface.
8. The historical type×clock report is not live-model evidence and fails self-consistency checks. No DRAM quantity in this chapter is calibrated.

The safe architecture decision begins by choosing the fidelity needed: payload sensitivity, coarse caller-ticked accounting, queued controller behavior, bank/row timing, or calibrated physical prediction. A model should be no more detailed than the question requires—but every claim must stop at the evidence rung the chosen model actually reaches.

---

## Review questions

1. Why can the HBM2 estimator return 51 while the first stateful access returns 50 base cycles and 1,000 stall cycles?
2. Derive the first-access state and explain why no output is elapsed completion time.
3. Why do three fixed-time same-channel accesses produce bandwidth/channel stalls `1000,1050,1050` rather than `1000,1050,1100`?
4. Derive the HBM2 budget after exactly 1,000 ticks and one 64-byte access.
5. Derive why request 2,001 first receives the bandwidth-window stall after refill.
6. Why is reset not fresh-construction-equivalent after a refill?
7. Which DRAM fields affect the standalone estimator/access paths, and which are decorative?
8. Trace a JSON request for HBM3, 777 GB/s, and row mode on to the standalone model. Which values survive?
9. What does the hierarchy retain and discard from a standalone DRAM read, and what byte effect occurs?
10. Why is the historical type×clock report rejected as decision evidence even though its methodology states explicit equations?

### Review-question answer key

1. The estimator is stateless: `ceil(64/256)+50=51`. Stateful access returns the 50-cycle preset latency separately from a 1,000-cycle initial empty-window stall; it does not call the estimator.
2. Fresh state has cycle/window/budget zero. The first access initializes a 1,000-cycle window without filling it, records 64 pending bytes, channel availability 50, returns cycles 50/stall 1000, and leaves current time zero. No request queue or completion event exists.
3. Every access overwrites channel availability with `current_cycle+base_latency=50`; it does not append service to old availability. Thus each later fixed-time channel-0 read sees only a 50-cycle gap.
4. `256 B/cycle × 1000 = 256000 B`; after one 64-byte access the remaining budget is 255,936, pending read bytes 64, and stall zero on an available channel.
5. Before request `n`, pending is `64(n−1)` and budget is `256000−64(n−1)`. Admission requires `64n > 256000−64(n−1)`, first true at `n=2001`; only 128,000 prior bytes were issued.
6. Reset clears current time and budget but retains window start/size. With stale start 1000, unsigned `0−1000` triggers an immediate refill, so the first post-reset access stalls zero rather than 1000.
7. Bandwidth and latency affect equations; channels and burst length affect availability/mapping; row flag adds +10 to non-ideal standalone reads. Bus width, banks/channel, and row-buffer size are decorative in these paths; preset clock is not consumed.
8. JSON lands all three in full config, but runtime conversion drops them. Manual `tu_dram_create(parsed_type)` constructs HBM3's preset: 819 GB/s and row mode off, not 777/on.
9. The hierarchy retains only `stall_out`, discards base `cycles_out`, updates wrapper counters, does not tick implicitly, and performs no backing-store copy; the 64-byte sentinel remains unchanged.
10. Independent recomputation gives HBM2/DDR5/DDR4 at 8 GHz as 2.975/1.424/0.862 TOPS rather than 2.839/0.776/0.435, and DDR4 at 1 GHz loses about 6.4%, contradicting the report's “identical/don't-care” conclusion. Explicit equations still require correct evaluation and bounded provenance.

---

## Design exercises

1. **Producer labeling.** Rewrite each canonical probe line as a quantitative sentence naming producer, state, clock, units, omissions, and calibration status.
2. **Window boundary.** In a disposable archived source tree, probe ticks 999 and 1000 and requests 1999–2001. Do not modify the pinned checkout.
3. **Reset equivalence.** Compare fresh construction, reset-before-refill, and reset-after-refill. List every state field required for true equivalence.
4. **Queued-channel alternative.** Specify an update equation using `max(channel_available,current_cycle)` and predict the first three fixed-time same-channel availability values. State what queues/events remain missing.
5. **Configuration reachability.** Build a field-by-field matrix for type, bandwidth, row mode, channels, latencies, and core clock across JSON, YAML generator, compiled header, runtime conversion, power model, hierarchy, and standalone construction.
6. **Historical recomputation.** Recompute all 42 report rows from the stated constants, separate arithmetic errors from modeling omissions, and write a corrected but still uncalibrated conclusion.
7. **Model-choice memo.** For an early architecture sweep, choose among stateless estimate, repaired fixed window, token bucket, queued channels, and bank/row timing. Justify performance, area/power proxy, control complexity, and verification cost.
8. **Calibration plan.** Define a comparison against a named RTL or memory simulator: traffic traces, clocks, mapping, outputs, error metrics, train/validation split, and acceptable error by regime.

---

## Primary references

- [WAT09] Williams, Waterman, and Patterson, “Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures,” CACM 2009 — compute/bandwidth ceilings and operational-intensity vocabulary; an upper-bound reasoning tool, not a latency simulator. Full entry in [references/foundations.md](../../references/foundations.md#wat09-roofline-model).
- [PAR19] Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019 — separation of workload, architecture, mapping, and constraints; model estimates are not automatically physical measurements. Full entry in [references/foundations.md](../../references/foundations.md#par19-timeloop).
- [KWO19] Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” MICRO 2019 — analytical inference of movement and performance from explicit mappings; it does not validate Tusim's DRAM equations. Full entry in [references/foundations.md](../../references/foundations.md#kwo19-maestro).
- [GEN21] Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” DAC 2021 — system/software integration can materially change accelerator performance; its evidence does not transfer numerically to Tusim. Full entry in [references/foundations.md](../../references/foundations.md#gen21-gemmini).
- [JOU17] Jouppi et al., “In-Datacenter Performance Analysis of a Tensor Processing Unit,” ISCA 2017 — memory organization, workload, software, and latency constraints shape measured accelerator behavior; the silicon numbers are not Tusim calibration. Full entry in [references/foundations.md](../../references/foundations.md#jou17-production-tpu-analysis).

All Tusim-specific claims in this chapter are sourced from the pinned commit and canonical-v3 evidence. The references provide vocabulary and design obligations only; no historical analytical report is promoted into live-model evidence.
