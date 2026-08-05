# Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

> **Chapter contract.** A metric is meaningful only with a named producer, event or action definition, interval, units, configuration authority, clock or timestamp owner, derivation, and fidelity label. This chapter keeps legacy state counters, `tu_perf_counters_t`, event tracing, logging trace, the standalone cycle model, embedded perf energy, and standalone power separate. It does not combine them into one fictional execution timeline. Canonical v4 is the drafting authority.

## Learning objectives

After this chapter, you should be able to:

1. write a complete measurement contract for a counter, trace, cycle estimate, or energy result;
2. distinguish a producer from a reporter and a field declaration from an active consumer;
3. identify the interval and denominator behind bandwidth, the field labeled TOPS, efficiency, hit-rate, energy-per-MAC, and power values, while distinguishing MAC/s from operations/s;
4. explain how explicit recorder calls and explicit ticks can double-count one logical interval;
5. describe the incomplete snapshot/diff/merge/reset semantics of `tu_perf_counters_t`;
6. keep Tusim's two VCD-producing APIs separate and reason about their timestamp behavior;
7. classify the standalone cycle model by linkage, reachability, assumptions, and known accounting defects;
8. distinguish embedded scalar energy accounting from the standalone table-based power model;
9. decide when a configuration field is operational, decorative, default-only, or retained without a consumer;
10. choose a measurement surface by decision regime and verification cost; and
11. state which conclusions are executable, analytical, estimated, historical, or rejected at the pinned edition.

## Prerequisite graph

```text
Chapter 4: configuration declaration -> parser -> runtime -> consumer
                              │
Chapter 5: ownership, reset, lifecycle, and public API contracts
                              │
Chapter 9: SRAM banks, capacity, access accounting, and stalls
                              │
Chapter 10: DMA descriptors, ticks, completion, and byte ownership
                              │
Chapter 14: operator-local metrics and heterogeneous counter meanings
                              │
Chapter 15: DRAM clocks, service models, and denominator discipline
                              │
Chapter 16: legal overlap requires an explicit common schedule
                              ▼
 producer + event + interval + units + clock + derivation + fidelity
                              │
                              ▼
                   defensible measurement claim
```

Earlier chapters repeatedly encountered numbers that looked compatible but were not. Chapter 10 separated copied bytes from channel retirement. Chapter 14 showed that engines labeled similar events differently. Chapter 15 separated a stateful DRAM service API from stateless estimators and historical reports. Chapter 16 showed that adjacent cycle fields do not establish a legal overlap schedule.

This chapter turns that recurring discipline into an explicit method: **select a measurement producer before interpreting a value**.

## Opening architecture question: what does “100 cycles” mean?

Suppose a report prints `100 cycles`. Before comparing it with another number, ask:

1. Which object produced it?
2. What event advanced it?
3. Was the interval operation-local, model-global, or manually authored?
4. Which frequency, if any, converts it to time?
5. Did another recorder advance the same interval again?
6. Was the object enabled, reset, merged, or restored?
7. Does the value include stalls, data movement, arbitration, leakage, or only selected components?
8. Is the producer linked and reached by the workload?
9. Is the result calibrated, analytically estimated, or merely named “cycle accurate”?

At the pinned commit, “cycles” can refer to at least the following distinct quantities:

- legacy `g_tu.estimated_cycles` formulas;
- caller-owned `tu_perf_counters_t.total_cycles`;
- event-trace tick deltas;
- logging trace's process-global cycle scalar;
- private `tu_cycle_model_t.current_cycle`;
- private DRAM-channel cycles;
- operator or engine return values;
- manually authored benchmark intervals;
- standalone power-model cycles used for leakage and average power.

A numerical equality between two such fields proves only equality of integers. It does not prove shared ownership, shared interval, shared units, or calibration.

A practical measurement contract is:

```text
measurement = {
    producer,
    event_or_action,
    caller,
    interval_start_and_end,
    units,
    configuration_authority,
    clock_or_timestamp_owner,
    derivation,
    fidelity,
    omitted_costs
}
```

If any member is unknown, qualify the conclusion rather than filling the gap with a name.

## 17.1 Theory: observations, estimators, and reports

### Counters are state transitions, not facts by themselves

A counter has meaning because some transition increments it. A field named `dma_read_bytes` could represent payload requested, bytes copied, bus transactions, cache-line transfers, or manually supplied accounting. The field name does not choose among these definitions.

For a delta counter, the intended interval is often:

```text
Delta = counter(end) - counter(start).
```

That equation assumes compatible snapshots, monotonic state, and an agreed subtraction rule. Tusim's surfaces violate these assumptions in different ways: perf diff clamps many decreasing integers to zero but directly subtracts energy doubles; standalone power diff subtracts unsigned fields directly and wraps on decreasing snapshots.

### Rates inherit every defect in numerator and denominator

A rate is not more trustworthy than its inputs. Let recorded cycles be `C` and configured frequency be `f_MHz`. The perf conversion is:

```text
seconds = C / (f_MHz × 10^6)
wall_clock_ns = floor(C / f_MHz × 1000).
```

Bandwidth and throughput then use different numerators over those derived seconds:

```text
bandwidth_GB/s = bytes / seconds / 10^9
reported_mac_throughput_field = MACs / seconds / 10^12.
```

Tusim names the second field `mac_throughput_tops`, but the numerator is MACs. It is dimensionally TMAC/s, not operations/s. Under the book's explicit convention of two operations per MAC, convert it to TOPS by multiplying by two. Both rates are over a **caller-authored counter interval**, not host measurements. If the caller double-records six cycles, both rates change even though the modeled operation did not.

Other metrics use unlike denominators:

```text
MAC efficiency = MACs / (TU_PE_ROWS × TU_PE_COLS × C)
energy_per_MAC = sum(component energy in pJ) / MACs
SPAD hit rate  = 1 - conflicts / accesses.
```

MAC efficiency uses compiled geometry and cycles, not frequency or runtime core geometry. Energy-per-MAC uses MAC count, not elapsed time. Hit rate uses access count. A chapter about measurement must preserve these distinctions.

### Traces add ordering, not automatic truth

A VCD file can encode declarations, timestamps, and value changes. IEEE 1800 defines syntax and ordering, but syntax does not prove that a producer observed complete state or that its integer timestamp is a physical nanosecond. Tusim's two VCD-producing APIs differ in storage, lifecycle, enablement, schema, capacity, and timestamp ownership. They cannot be treated as two front ends to one hidden trace service.

### Models are selected abstractions

A cycle or energy model chooses which events matter and assigns equations or table costs. Such a model can be useful without being calibrated. The safe label depends on evidence:

- **Executable:** linked and exercised by a runnable test.
- **Integrated:** reached through an ordinary runtime path.
- **Analytical model:** equations estimate behavior without executing the modeled hardware.
- **Estimated:** not compared with a named reference implementation or hardware target.
- **Calibrated:** compared using a retained method, data, and error report.

At the pin, Tusim's standalone cycle and power models are estimated abstractions. Their names and hardcoded tables do not raise their fidelity rung.

## 17.2 Source map: seven producers and one forensic consumer

| Surface | State owner | Non-test caller / ordinary reachability | Build/reachability | Clock or interval | Safe label |
|---|---|---|---|---|---|
| Legacy `g_tu` counters | process-global `tu_state_t` | ordinary core operations | linked and integrated | field-specific formulas/actions | executable counters, heterogeneous intervals |
| `tu_perf_counters_t` | caller-owned struct | standalone `cycle_model.c` and manual benchmark; no ordinary core owner | object linked; no ordinary `g_tu` owner | caller-authored additive cycles | executable API, not automatically integrated |
| `perf/event_trace` | caller-owned trace context | none outside implementation/tests/docs | linked | caller tick deltas | executable trace API, unintegrated |
| `infra/logging` trace | process-global fixed buffer | `tu_mma()` inserts events | linked and partially reached | separate global cycle scalar | executable event log with weak timing reachability |
| Standalone cycle model | caller-owned model and private submodels | none outside its implementation | source-present; absent from `TU_OBJS`; runner-compiled | private current cycle | estimated analytical/executable-in-isolation |
| Embedded perf energy | substructure inside perf counters | perf recorder calls | linked with perf counters | perf actions and ticks | estimated scalar accounting |
| Standalone power model | caller-owned model | none outside tests/docs | linked | caller actions and model cycles | estimated table-based accounting |
| Manual benchmark | local benchmark context | standalone benchmark only; no ordinary workload caller | standalone target, not aggregate | invented costs plus explicit ticks | forensic smoke consumer |

The architecture lesson is not that Tusim has “a performance model.” It has several independent state machines and reporting surfaces. A user must choose and bridge them deliberately.

## 17.3 Legacy state versus `tu_perf_counters_t`

The ordinary cmodel maintains legacy fields in `g_tu`: DMA bytes, MMA calls, tile counts, FLOPs, and formula-derived `estimated_cycles`. These are reached by ordinary operations. They do not alias `tu_perf_counters_t`, and no common elapsed clock is proved.

`tu_perf_counters_t` is a broad caller-owned structure with DMA, compute, memory, stall, utilization, timing, and embedded-energy substructures. Its implementation is linked into `libtucmodel.a`, and its focused suite passes 12/12 at the pin. Yet ordinary `g_tu` or `tu_core_t` construction does not allocate one. The main non-test implementation caller is the separately compiled cycle model. The benchmark authors values manually.

This distinction matters because “linked” and “integrated” answer different questions:

```text
linked: can this symbol be resolved in the library?
integrated: does an ordinary workload construct and drive it?
```

### Additive time and duplicate ownership

Perf recorder functions call `tu_perf_tick()` according to their own conventions:

- DMA read/write add active plus supplied stall cycles;
- internal DMA adds active cycles;
- MMA and generic operations add active plus stall cycles;
- idle adds idle cycles;
- SPAD and DRAM access recorders add only supplied stall cycles;
- GBuf, request-file, and pipeline-bubble recorders add no global time;
- the descriptor helper composes DMA timing and optional SPAD stall timing.

An explicit `tu_perf_tick()` adds its argument again. The API cannot know whether that tick represents a new interval or duplicates one already charged by a recorder.

### Worked example 1: 18 becomes 24

The canonical v4 probe records:

```text
DMA read:  active=10, stall=2  -> +12 cycles
MMA:       active=5,  stall=1  ->  +6 cycles
---------------------------------------------
perf total                         18 cycles
compute-owned interval              6 cycles
```

At 1 GHz, the perf object reports 18 ns. The probe then calls `tu_perf_tick(..., 6)` explicitly:

```text
PERF_ADDITIVE total=18 wall_ns=18 dma_read=64 dma_stall=2 compute=6 macs=8 leak=0.018
PERF_DUPLICATE after_explicit_tick=24 compute=6
```

The compute subcounter remains six, while global perf time becomes 24. The second call may be legitimate if it represents a new interval; in this sequence it deliberately demonstrates duplicate ownership.

The public API cannot enforce a global policy. A production integration needs one of these conventions:

1. operation recorders own time, and callers never tick the same interval;
2. callers own time, and recorders update only event counts;
3. a scheduler owns a common clock and passes deltas to otherwise timeless recorders.

Mixing conventions silently changes rates and leakage.

### Snapshot, diff, and merge are incomplete algebra

A snapshot is a byte copy plus a snapshot-cycle field. Diff and merge do not cover every struct member.

Diff omits both WS/OS cycle fields, GBuf conflicts, both DRAM row hit/miss fields, all three bandwidth-utilization fields, wall time, six scalar energy parameters, and the embedded power-enable flag. Many integer differences clamp at zero, while energy doubles can become negative.

Merge omits those same families, the cached `energy_total_pj`, outer counter enable, and outer clock frequency. It therefore retains the destination's clock and enable state even while adding many source counters. A merged object is not a complete sum of two measurement contracts.

Use diff or merge only after identifying every field required by the claim. For a new integration, a generated field inventory or explicit versioned schema is safer than assuming whole-struct algebra.

### Reset is not “clear everything”

`tu_perf_reset()` saves frequency and the entire power substructure, calls `tu_perf_init()`, then restores power. This behavior has three consequences:

- ordinary counters and total cycles clear;
- clock frequency is preserved;
- all power parameters **and accumulated component energy** are preserved;
- `tu_perf_init()` unconditionally sets outer `enabled=true`.

Canonical v4 begins with a disabled counter at 777 MHz and 99 pJ accumulated MAC energy. After reset:

```text
PERF_RESET enabled=1 freq=777 energy_mac=99.0 total=0
```

Reset is neither a full energy reset nor enable-state preserving. Lifecycle documentation should state this exact contract.

## 17.4 Derived metrics: five denominators, not one

Consider a perf object at 1 GHz with ten recorded cycles, 100 DMA bytes, and ten MACs. Derived seconds are 10 ns. The canonical result is:

```text
DMA bandwidth = 100 B / 10 ns = 10 GB/s
reported MAC-throughput field = 10 MAC / 10 ns = 0.001 TMAC/s
```

Tusim reports the latter as `0.001 TOPS`, reproducing its field label. Dimensionally, the underlying quantity is `0.001 TMAC/s`; it equals `0.002 TOPS` only under the explicit convention of two operations per MAC.

```text
PERF_METRICS dma_gbps=10.000 tops=0.001000 efficiency=0.003906250 util=0.500 hit=1.000
```

For the pinned compiled array, `TU_PE_ROWS × TU_PE_COLS = 256`. MAC efficiency is:

```text
10 / (256 × 10) = 0.00390625.
```

This denominator does not include frequency. It describes recorded MACs relative to compiled peak MAC opportunities over recorded cycles. It can exceed one if callers record more MACs than that denominator permits. The implementation does not clamp it.

Scratchpad hit rate is defined from counters as:

```text
1 - bank_conflicts / (reads + writes).
```

With one access and two conflicts, the implementation reports `-1.0`. Again, no clamp protects interpretation.

Energy-per-MAC divides the sum of six component-energy fields by MAC count. Average power instead divides component energy by derived seconds. In the embedded perf implementation, the conversion applies an extra factor of 1,000. One pJ over one ns is physically one mW, but the implementation reports 1,000 mW:

```text
PERF_UNBOUNDED efficiency=2.0 hit=-1.0 reported_power_mw=1000.0 physical_power_mw=1.0 cached_total=0.0
```

The cached-looking embedded `energy_total_pj` has no normal recorder producer. Metrics and reports sum component fields directly, so component energy can be nonzero while the cached total remains zero.

A report should therefore print or retain the raw numerator, raw denominator, clock assumption, and formula version alongside each derived metric.

## 17.5 Two trace producers

### Caller-owned event trace

`perf/event_trace` creates a caller-owned context, registers signals, records pending changes, and writes VCD. No ordinary workload caller constructs it at the pin.

Its first tick has unusual semantics. The first `tu_trace_tick(trace, delta)` writes the header and `#0`, then returns without applying `delta` and without flushing pending changes. Canonical v4 records:

```text
TRACE_CONTEXT first_cycle=0 dirty=1 enabled=0
TRACE_CONTEXT second_cycle=3 dirty=0
```

A second tick flushes the pending change at the old time and then advances. The fixed `$timescale 1 ns` declaration is file metadata; it does not prove that caller deltas are physical nanoseconds.

The implementation-private global enable flag remains false and has no public setter path, while context creation, signal changes, and ticks do not consult it. Therefore `tu_trace_is_enabled()==false` does not prevent direct API use. Enablement is a caller/integration responsibility, not one coherent global gate.

Close emits no dedicated documented EOF marker. A focused test's search for `$end` is satisfied by ordinary VCD header directives; it does not prove a special end-of-file record.

### Process-global logging trace

`infra/logging` owns a separate fixed array of 65,536 events, a count, and a global cycle scalar. `tu_mma()` calls its event insertion function directly. Trace-enable configuration does not gate insertion.

When full, the buffer silently drops later events. Clear resets both count and cycle. Ordinary non-test callers insert MMA events but do not advance the logging cycle, so those events normally remain at timestamp zero.

Its VCD exporter emits a new timestamp only for a strict increase. Equal or decreasing event cycles therefore appear under the previous timestamp. The exporter then emits the final global cycle even when it regresses. This is source-defined serialization behavior, not a monotonic hardware timeline.

### Worked example 2: same file format, different contracts

The canonical logging probe inserts one event at cycle 0, advances the process-global trace cycle to 9, and then inserts a second event:

```text
TRACE_LOG count=2 first=0 second=9 global=9
```

This does not correspond to the event-trace context's first/second-tick sequence. The two APIs happen to emit VCD-like text, but they do not share context, signal schema, buffer, enable state, or timestamp owner.

Use the caller-owned event trace when explicit signals and an explicit trace lifecycle are required. Use the logging trace only when its fixed event schema and global storage are acceptable. To correlate them, add an explicit bridge event and a common-clock definition; do not align files merely by equal timestamp numbers.

## 17.6 Standalone cycle model: executable in isolation, not integrated

`perf/cycle_model.[ch]` provides functional, estimated, and enum-named `CYCLE_ACCURATE` modes. The source is present and the runner compiles it directly. Its focused suite passes 21/21. However, `cycle_model.o` is absent from `TU_OBJS`, no Makefile test rule exists, and no non-test caller outside its own implementation reaches it.

The safe classification is **source-present and executable in isolation**, not integrated runtime timing.

- `FUNCTIONAL` returns zero accounting; it does not verify functional correctness.
- `ESTIMATED` applies fill + compute + drain equations.
- `CYCLE_ACCURATE` executes source-defined serial heuristics using private pipeline, bank, DRAM, and DMA submodels.

The enum name is not calibration evidence.

### Worked example 3: estimated tile and bridge ownership

For a `2 × 3 × 4` tile under the probe's estimated parameters:

```text
fill    = 2 × 3 = 6
compute = 4
 drain  = 2 × 2 = 4
--------------------
total             14 cycles
```

The model reports:

```text
CYCLE_EST tile=14 current=14
```

In named-cycle mode, a direct 32-byte write on fresh bank state returns 15 cycles. The attached perf object receives all 15 through the **read** recorder:

```text
CYCLE_WRITE cycles=15 cm=15 perf=15 read_bytes=32 write_bytes=0 read_cycles=15 write_cycles=0
```

This exposes a direction defect: modeled writes populate perf read counters.

The model also has two ways to advance paired state. A model operation can advance private model time and invoke a perf recorder, while `tu_cycle_model_advance()` advances both model and attached perf time. The probe's explicit bridge shows equality:

```text
CYCLE_BRIDGE cm=20 perf=20
```

That equality reflects the chosen bridge calls. It is not proof of a global simulator clock.

### Bank and DMA qualifications

The private bank model increments `conflict_count` whenever a nonzero access leaves budget below maximum. One isolated access can therefore be labeled a conflict despite zero stall:

```text
CYCLE_BANK isolated_stall=0 reads=1 conflicts=1 utilization=0.500
```

Its average utilization divides cumulative accesses by one instantaneous capacity constant, without an elapsed-window denominator; it can exceed one.

Cycle-model DMA passes its `is_read` boolean directly to a DRAM API parameter named `is_write`. Fresh HBM2 channels at 1 GHz therefore receive reversed timing direction:

```text
CYCLE_DMA_DIRECTION read_arg=21 write_arg=28 write_perf_read=4 write_perf_write=0
```

Reset reconstructs non-ideal DRAM channels at 1 GHz and does not reset attached perf state. For HBM2E, HBM3, DDR4, DDR5, and LPDDR5, this changes the creation-time frequency—1800, 3200, or 1600 MHz depending on type—to 1000 MHz, while prior attached perf counters survive.

These defects do not make the model useless. They define the conditions under which it can be used: isolated source experiments, explicit parameter disclosure, and property-level validation. They prohibit presenting its output as calibrated end-to-end runtime cycles.

## 17.7 Two energy producers

### Embedded perf energy

The perf substructure uses scalar pJ parameters and explicit action recorders. At initialization, pinned defaults include:

- MAC: 1.0 pJ;
- SRAM read: 0.5 pJ;
- SRAM write: 0.5 pJ;
- DRAM access: 20 pJ;
- DMA byte: 0.05 pJ;
- leakage: 0.001 pJ per perf tick cycle.

These are hardcoded estimates. DMA reads charge DRAM energy by active cycles; writes do not follow the same rule. DRAM actions charge once per call. Leakage advances only with perf ticks. A caller that double-ticks also double-charges leakage.

The component fields, not `energy_total_pj`, drive metrics. Every energy report must name which actions were recorded and which were omitted.

### Standalone table-based power model

`tu_power_model_t` is separate. It records precision-dependent MACs, memory actions, 64-byte DRAM transactions, page-miss activation, DMA bytes, clock-tree cycles, heuristic area, leakage, snapshots, and its own frequency. The object is linked and focused-tested 20/20, but ordinary `tu_core_create()` does not construct it. Its config helper is reached by tests/docs only and chooses node/frequency heuristically from geometry and bandwidth.

Canonical v4's 7-nm example uses 256 MAC units, 64 KiB SPAD, 256 KiB GBuf, and a 30% area overhead:

```text
area = (256 × 160 + (64 + 256) × 2400) × 1.30 / 10^6
     = 1.051648 mm².
```

The action energies are:

```text
MAC                         2.0000 pJ
SPAD                        0.4000 pJ
DRAM read + activation    370.0000 pJ
DMA                         0.6400 pJ
clock tree                  0.1000 pJ
leakage                    52.5824 pJ
-----------------------------------
total                     425.7224 pJ
```

Over ten ns, average power is:

```text
425.7224 pJ / 10 ns = 42.57224 mW.
```

The retained line is:

```text
POWER_TABLE area=1.051648 mac=2.000 spad=0.400 dram=370.000 dma=0.640 clock=0.100 leak=52.5824 total=425.7224 avg_mw=42.5722
```

This is a reproducible estimate from a specific table and action sequence, not measured silicon power.

### Cache, reset, and const qualifications

Standalone `energy_total_pj` is cached. After `tu_power_compute_total()`, later action recording can leave it stale. Average-power reporting reuses a nonzero stale total. Energy-per-MAC recomputes only when the cache is zero. Recompute after the final action before deriving a report.

Reset preserves node, frequency, and enable, but clears activity and loses the prior area estimate. Area-dependent leakage is then disabled until area is recomputed. The function named `tu_power_get_energy_per_mac(const ...)` casts away const and may populate the cached total as a read-side effect.

Standalone diff directly subtracts unsigned cycles and activity. Decreasing snapshots wrap:

```text
POWER_DECREASING_DIFF cycles=18446744073709551606 macs=18446744073709551606 energy_mac=-2.000
```

A caller must establish snapshot ordering before interpreting such a diff.

Several declared table parameters—including DRAM idle power, NoC-hop energy, PE-register energy, and per-byte memory leakage values—do not contribute to the retained total path. Table presence is not action coverage.

## 17.8 Configuration reachability: declaration is not effect

Measurement configuration must be traced field by field through:

```text
shipped JSON/YAML -> parser -> validation -> runtime conversion
                  -> object construction -> consumer -> output
```

At the pin:

- trace enable and output-file fields are parsed/retained, but they do not create or gate an event-trace context;
- JSON/YAML trace format fields are shipped but not parsed into trace behavior;
- `trace_max_events` defaults to 65,536 but is not parsed, converted, or consumed by the fixed logging buffer;
- `detailed_stalls` is parsed and propagated but no downstream measurement producer reads it;
- shipped `power.enabled` and `power.model` fields are not a proved ordinary runtime construction path for the standalone power model;
- cycle-model configuration is dropped by runtime conversion, while direct construction takes explicit mode and compiled constants.

These distinctions define four useful labels:

| Label | Meaning |
|---|---|
| Operational | parsed or selected and read by the claimed consumer |
| Retained-only | stored or copied but no behavioral reader found |
| Default-only | initialized in code but not exposed through the claimed parser path |
| Decorative | shipped or documented without a proved consumer path |

Configuration reviews should require an A/B discriminator: change one field while holding inputs constant and demonstrate changed consumer state or output. If no change is observed and no source reader exists, record the field as non-operational rather than promising future behavior.

## 17.9 Trade-offs: choosing a measurement surface by regime

| Regime | Preferred surface | Benefit | Main cost/risk | Required verification |
|---|---|---|---|---|
| Ordinary API activity census | legacy `g_tu` fields | already reached by core operations | heterogeneous definitions and formula time | field-by-field producer audit |
| Custom experiment with explicit accounting | `tu_perf_counters_t` | broad event taxonomy and reports | caller owns time; duplicate ticks; incomplete lifecycle algebra | interval policy and raw numerator/denominator retention |
| Signal-oriented debugging | event-trace context | explicit signals and lifecycle | no ordinary integration; unusual first tick | first/second tick test and timestamp-unit statement |
| Lightweight MMA event logging | logging trace | reached insertion and fixed buffer | weak timing path, silent overflow, nonmonotonic export | capacity and timestamp-order checks |
| Isolated timing alternative study | standalone cycle model | multiple configurable heuristic modes | unlinked, uncalibrated, direction/reset/stat defects | direct compile, invariants, sensitivity, no runtime claim |
| Low-cost action energy estimate | embedded perf energy | colocated with perf actions | asymmetric action coverage, duplicate leakage, power unit defect | action census and independent dimensional check |
| Architecture energy/area alternative | standalone power model | richer tables, area, leakage, precision | no ordinary constructor, cache/reset hazards, unused table fields | action trace, cache recomputation, table provenance |
| End-to-end latency or power claim | none alone | — | no integrated common timeline or calibration | explicit bridges, common schedule, external reference |

A realistic configurable model should retain materially distinct alternatives. The decision is not “which model is fastest?” It is “which abstraction answers this question at acceptable complexity and error?”

Instrumentation itself has cost. Scalar counters require state width, overflow policy, and read/reset synchronization. Event traces consume buffer capacity and export bandwidth; fixed buffers can lose data silently, while backpressure would perturb the modeled schedule. VCD serialization adds host storage and I/O overhead. Canonical v4 characterizes semantic behavior and buffer limits but does not quantify physical counter area, trace power, runtime perturbation, or host-export cost. Those costs must be measured or modeled separately before selecting instrumentation for a production or hardware-correlated regime.

- For debugging ordering, a trace can be more valuable than a scalar cycle estimate.
- For compiler cost comparison, a consistent estimated model may be sufficient even without calibration.
- For architecture sign-off, neither a source-defined heuristic nor hardcoded energy table is sufficient without comparison and error bounds.
- For regression detection, exact counter deltas can be useful even when their physical interpretation is limited.

## 17.10 Verification: what canonical v4 proves

The binding evidence is [`20260805-ch17-canonical-v4`](../../experiments/runs/ch17-measurement/20260805-ch17-canonical-v4/). It was sealed from book commit `94ed20d18245cbdb4dc3936c1e7c216e4cbc38ea` against the exact Tusim pin.

The run retains:

- 31 source/config/test/document hashes;
- 96 structural predicates and 127 total checks;
- source-pin and source-hash negative controls;
- focused perf 12/12, event trace 31/31, logging 7/7, power 20/20, and runner-compiled cycle 21/21 results;
- a perf mutation producing 11/12 and nonzero exit;
- exact probe output with `failures=0`;
- a real `assert(False)` validator mutation rejected under normal and optimized Python;
- retained input hashes, input commit, toolchain, source-cleanliness fingerprints, and final bundle hashes.

The independent post-v4 reviewer exported and rebuilt the pinned source, reproduced the audit and probe, checked all 14 bundled inputs against the sealing commit, verified all 43 retained entries and four final bundle hashes, recomputed the formulas, and returned PASS with no BLOCK, MAJOR, MINOR, or NIT findings.

This evidence proves the bounded contracts exercised or structurally gated at one source revision. It does not prove complete workload integration, realistic physical timing, trace completeness, or calibrated power.

A useful verification ladder is:

1. **source reachability:** find every producer and non-test caller;
2. **structural gate:** pin implementation and enforce expected relationships;
3. **focused execution:** drive one discriminating state transition;
4. **negative control:** mutate pin, source, assertion, or expected value and require failure;
5. **arithmetic recomputation:** derive every printed quantity without trusting the probe's check;
6. **integration test:** prove an ordinary workload constructs and drives the surface;
7. **calibration:** compare with a named reference under matched configuration.

Chapter 17 reaches different rungs for different surfaces. Do not promote all of them to the highest rung achieved by any one surface.

> **Fidelity box — safe and unsafe conclusions**
>
> **Safe:** canonical v4 reproduces exact source-defined counter, trace, cycle, and energy behaviors at the pinned commit. It establishes linkage and caller boundaries, configuration gaps, arithmetic, and named defects.
>
> **Unsafe:** “Tusim reports one coherent cycle count,” “CYCLE_ACCURATE is calibrated,” “VCD timestamps are physical nanoseconds,” “all shipped measurement fields work,” “power is CACTI-calibrated,” or “the benchmark measures application performance.”
>
> Tusim's `mac_throughput_tops` field is also not dimensionally TOPS: it computes TMAC/s. Multiplication by two is valid only under the explicitly stated two-operations-per-MAC convention.
>
> **Required label:** cycle and energy outputs discussed here are estimated unless a separate retained calibration record is supplied.

## 17.11 Common failure modes

1. **Counter-name equivalence.** Adding two fields named `cycles` without proving compatible intervals.
2. **Reporter-as-producer.** Treating a pretty table as evidence that its numerators were recorded correctly.
3. **Double-owned time.** Calling an operation recorder and ticking the same interval again.
4. **Whole-struct assumptions.** Treating diff, merge, or reset as complete without a field census.
5. **Denominator or unit collapse.** Describing bandwidth, efficiency, energy/MAC, and power as if they shared one formula, or relabeling a MAC/s field as operations/s without the explicit two-operations-per-MAC conversion.
6. **Clamped interpretation of unclamped values.** Assuming efficiency and hit rate remain in `[0,1]`.
7. **Timescale promotion.** Reading `$timescale 1 ns` as proof that caller ticks model nanoseconds.
8. **Trace-family conflation.** Combining the event context and logging buffer because both emit VCD.
9. **Enum-name fidelity.** Treating `CYCLE_ACCURATE` as a validation result.
10. **Source-presence integration.** Assuming a `.c` file or linked object is reached by workloads.
11. **Configuration-by-documentation.** Assuming a JSON/YAML field affects execution without a consumer.
12. **Cached-total staleness.** Recording more actions after computing standalone total energy.
13. **Table-provenance inflation.** Calling hardcoded constants CACTI-derived or calibrated without retained generation evidence.
14. **Green smoke promotion.** Treating a zero-return benchmark with no numerical oracle as measurement validation.
15. **Unordered snapshots.** Interpreting wrapped standalone diffs as huge real activity.

## 17.12 Development questions

The evidence exposes several design questions rather than silently prescribing fixes:

- Should timing ownership move to one scheduler clock, or should every recorder become explicitly timeless?
- Should perf diff/merge be generated from a schema so new fields cannot be omitted silently?
- Should reset APIs separate `clear_activity`, `restore_defaults`, and `preserve_configuration`?
- Should each derived metric return its numerator and denominator as structured metadata?
- Should trace timestamps use a typed clock domain rather than raw integers?
- Should logging overflow be observable through a dropped-event counter?
- Should the standalone cycle model be linked only after its DMA direction, bank statistics, and reset contracts are corrected?
- Should energy tables carry provenance, valid ranges, precision definitions, and calibration error?
- Should configuration validation reject retained-only and decorative fields instead of accepting them?
- What minimum bridge events would permit correlation among operator, DMA, DRAM, cycle, trace, and energy surfaces?

Each proposed change should preserve useful alternatives. A lightweight approximate mode can coexist with a more detailed mode if the API makes fidelity, cost, and assumptions explicit.

## Summary

A measurement value is a contract, not a noun. At the pinned Tusim edition, legacy counters, perf counters, two trace producers, a standalone cycle model, embedded energy, and standalone power remain distinct. Their state owners, callers, clocks, reset behavior, configuration paths, and fidelity differ.

`tu_perf_counters_t` offers broad accounting but leaves interval ownership to callers. Its recorders add time, explicit ticks can add it again, diff/merge omit fields, and reset preserves power state while re-enabling the object. Its derived metrics use several denominators and include unclamped ratios and a power-unit defect.

The two trace APIs both produce VCD-like output but do not form one stream. The cycle model is executable in isolation yet unlinked from ordinary runtime construction and contains source-defined DMA, bank, and reset limitations. The two energy producers use different actions, tables, caches, and clocks; neither is calibrated by its name or comments.

The durable decision rule is:

```text
name the producer;
name the event;
name the interval and clock;
retain numerator and denominator;
prove configuration reachability;
state omissions and fidelity;
then interpret the number.
```

## Review questions

1. Why does equality between two cycle fields not establish a common timeline?
2. Which perf recorder paths advance global time, and which named recorder paths do not?
3. Why can the canonical additive sequence report 24 total cycles while compute remains six?
4. What fields make perf diff and merge incomplete?
5. What state does perf reset preserve, clear, and unexpectedly change?
6. Give the distinct denominators for bandwidth, the MAC-throughput field, MAC efficiency, energy/MAC, and average power. Why is the field's TOPS label dimensionally qualified?
7. Why can MAC efficiency exceed one and scratchpad hit rate become negative?
8. Contrast the first-tick behavior and enablement of the event trace with the logging trace.
9. Why is the standalone `CYCLE_ACCURATE` mode classified as estimated and unintegrated?
10. Explain the cycle-model DMA direction defect and the write-to-read perf accounting defect.
11. Why can standalone power reports become stale after additional action recording?
12. What evidence would be required to call Tusim's power tables CACTI-derived and calibrated?
13. Classify `trace_max_events` and `detailed_stalls` at the pin.
14. What does canonical v4 prove, and what does it deliberately not prove?

### Selected answer key

1. The fields have different owners, producers, events, and clocks. Integer equality does not provide a bridge.
2. DMA read/write, internal DMA, MMA/op, idle, SPAD stall, and DRAM stall paths advance time according to their contracts. The public descriptor helper composes DMA time with optional SPAD-stall time. GBuf, request-file, and pipeline-bubble recorders do not.
3. The MMA recorder adds six to both compute and global perf time; the later explicit tick adds six only to global time, duplicating the logical compute interval.
4. Named omissions include WS/OS cycles, GBuf conflicts, row hits/misses, bandwidth-utilization fields, wall time, energy parameters, power enable, cached total on merge, and destination outer clock/enable semantics.
5. It clears ordinary counters/cycles, preserves frequency and the whole power substructure including accumulated energy, and re-enables a disabled outer counter.
6. Bandwidth uses bytes/derived seconds; the field labeled TOPS uses MACs/derived seconds and is therefore TMAC/s; efficiency uses MACs/(compiled PEs×cycles); energy/MAC uses component energy/MAC count; power uses component energy/derived seconds. Under two operations per MAC, multiply TMAC/s by two to obtain TOPS.
7. The formulas are not clamped, and callers can author inconsistent numerators or conflict counts.
8. Event trace's first tick writes header/#0 and drops the delta while retaining dirty changes; its direct API ignores the private false enable flag. Logging uses a fixed global event buffer and separate global cycle, with direct MMA insertion and no equivalent context lifecycle.
9. It is absent from `TU_OBJS`, has no ordinary caller, and has no retained RTL/silicon calibration. The enum selects a heuristic implementation, not a validated fidelity level.
10. The cycle model passes `is_read` into a parameter interpreted as `is_write`, reversing DRAM timing. It also always invokes the perf read recorder, so writes populate read counters.
11. `energy_total_pj` is cached and a nonzero cached value can be reused after later actions. Explicit recomputation is required after the final action.
12. Retain exact CACTI version, configurations, raw outputs, table-generation mapping, matched Tusim parameters, comparison targets, methodology, and error statistics.
13. `trace_max_events` is default-only and unconsumed by the fixed buffer; `detailed_stalls` is parsed and retained but has no identified measurement consumer.
14. It proves exact bounded source behavior, arithmetic, tests, negative controls, and provenance at one pin. It does not prove integrated workload timing, complete tracing, or calibrated power/cycle accuracy.

## Design exercises

1. **Measurement-contract schema.** Design a versioned record that stores producer ID, event definition, interval, clock domain, numerator, denominator, configuration hash, fidelity, and omissions. Explain migration when a new counter field is added.
2. **Single-owner timing.** Refactor the additive perf example conceptually under each of the three timing-ownership conventions. State which APIs would become timeless and how leakage would advance.
3. **Complete diff/merge.** Propose generated diff and merge semantics for every perf field. Decide which configuration fields must match, which may be copied, and which invalidate a merge.
4. **Trace correlation.** Define a bridge that correlates event trace, logging trace, DMA completion, and operator events without assuming equal raw timestamps. Include overflow and reset behavior.
5. **Cycle-model alternatives.** Compare three variants: current lightweight heuristic, corrected queue-aware software model, and RTL co-simulation. Evaluate performance, area/power insight, accuracy, implementation complexity, and verification cost.
6. **Power calibration experiment.** Specify a reproducible table-generation and calibration workflow using a named memory/arithmetic reference. Include process, voltage, frequency, geometry, activity, uncertainty, fitting, held-out validation, and artifact retention.
7. **Configuration A/B test.** Choose `trace_max_events` or `detailed_stalls` and design the minimal consumer and mutation test that would promote it from non-operational to operational.
8. **Counterexample search.** Construct inputs that make MAC efficiency exceed one, hit rate negative, standalone diff wrap, and cached average power stale. For each, decide whether to clamp, reject, or expose the raw inconsistency.

## Primary references

- IEEE Std 1800-2023, *IEEE Standard for SystemVerilog—Unified Hardware Design, Specification, and Verification Language*, clause 21.7, “Value change dump (VCD) files,” DOI: [10.1109/IEEESTD.2024.10458102](https://doi.org/10.1109/IEEESTD.2024.10458102). Used only for VCD syntax and timescale context.
- Mark Horowitz, “1.1 Computing's energy problem (and what we can do about it),” *2014 IEEE International Solid-State Circuits Conference*, pp. 10–14, DOI: [10.1109/ISSCC.2014.6757323](https://doi.org/10.1109/ISSCC.2014.6757323). Used for technology-dependent, order-of-magnitude energy motivation, not Tusim parameter transfer.
- Hewlett Packard Enterprise, [CACTI first-party repository](https://github.com/HewlettPackard/cacti). Used to define requirements for a reproducible characterization workflow; no retained CACTI run calibrates the pinned Tusim tables.
- Arm, [Arm Architecture Reference Manual for A-profile architecture](https://developer.arm.com/documentation/ddi0487/latest/), Performance Monitors Extension. Vendor-scoped context for explicit event and interval configuration, not a definition of Tusim counters.
- Chapter-specific verified scope ledger: [`references/ch17-measurement-primary-sources.md`](../../references/ch17-measurement-primary-sources.md).
