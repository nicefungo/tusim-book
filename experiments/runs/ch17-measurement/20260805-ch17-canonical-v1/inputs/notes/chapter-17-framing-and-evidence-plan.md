# Chapter 17 — Framing and Evidence Plan

## Status and authority

- Work unit: Chapter 17 framing only; no claim ledger, canonical audit, predraft gate, or manuscript has begun.
- Planned title: **Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy**.
- Book baseline inspected: `main` at `d9b4ac3baaca6b99acf11cd376906101986d4d7a`.
- Tusim evidence pin: detached, clean, and read-only at `e918c80b6fce833cd1fcae97730fa841c2176f25`.
- Governing plan: `PLAN.md` §§4, 6, 7, and 9 plus `notes/whole-book-coverage-review-2026-08-05-after-ch16.md`.
- Chapter 16 is closed. Its controller ledgers are contrast evidence only, not a Chapter 17 clock or producer.
- Safety: keep the pinned Tusim checkout detached, clean, and read-only; do not push, publish, or rebuild the curated publish branch.

## Reader decision and opening question

**Reader decision:** given a number, counter snapshot, trace timestamp, cycle estimate, energy total, or derived rate in Tusim, select the exact producer, caller, interval, units, configuration surface, clock assumption, and fidelity rung that make the observation interpretable—without merging adjacent surfaces into one fictional execution timeline.

**Opening architecture question:**

> A Tusim run reports cycles, utilization, bandwidth, a VCD timestamp, energy in pJ, and average power. Which operation actually produced each value, which interval does it cover, and which pairs—if any—may be compared or combined?

The chapter succeeds if a reader can answer that question by tracing provenance rather than by trusting field names such as `total_cycles`, `cycle_accurate`, `power`, or `trace`.

## Global-plan consistency and triggered risks

- **Chapter 17/19 overlap — triggered and resolved by boundary.** Chapter 17 owns producer identity, caller reachability, interval, units, configuration, clock, derivation, and fidelity. Chapter 19 retains evidence selection, unsafe green-gate interpretation, test architecture, mutation, CI, and verification strategy.
- **Broad synthesis becoming a catalogue — triggered and resolved by one decision matrix.** The chapter is organized around selecting and interpreting a measurement contract, not around listing APIs.
- **Source-edition drift — not triggered.** The edition pin is unchanged.
- **Stable numbering — not triggered.** No merge, split, reorder, or renumber is proposed.
- **Completed-chapter supplement backlog — not triggered.** Chapters 8, 10, and 14 remain closed; Chapter 17 may use their observations as named examples but will not revise them.
- **Fictional integration — remains globally active.** No counter, trace, cycle model, power model, DRAM model, engine return, or Chapter 16 controller ledger may be added merely because each uses the word “cycle.”

Fresh reconnaissance supports the planned Chapter 17 boundary. No `PLAN.md` amendment is justified at framing time.

## Ranked scope candidates

### Rank 1 — One provenance-first measurement chapter — **selected**

**Boundary.** Keep performance counters, both trace implementations, the source-present cycle model, both energy-accounting surfaces, and the manual benchmark consumer in one chapter, but teach them through one producer/interval/unit/config/clock matrix.

**Reader payoff.** The reader learns a reusable procedure for deciding what a metric means and whether two observations are comparable. The negative integration evidence is central rather than incidental.

**Evidence strength.** Strong and discriminating: three library-linked families, one source-present/non-archive cycle model, two trace producers, two energy models, explicit config paths, focused tests, aggregate-membership differences, one ordinary-operation trace caller, and several documentation/source contradictions.

**Continuity.** Best fit after Chapters 14–16, which exposed heterogeneous engine, DRAM, and controller accounting but intentionally deferred the general provenance framework.

**Cost/risk.** Broad source set and terminology density. Control this by using the provenance matrix as the spine, importing prior producers as examples, and excluding verification methodology and physical calibration.

### Rank 2 — Counters and tracing now; split cycle and energy estimation into a new chapter

**Boundary.** Chapter 17 would cover aggregate counters and trace streams; a new chapter would cover analytical/cycle and energy models.

**Benefit.** More room for energy-table provenance, cycle-model equations, and calibration literature.

**Why not selected.** It creates a second chapter without a distinct reader decision: cycle and energy outputs still require the same producer/interval/unit/config/clock choice. It also delays the exact comparison discipline readers need before Chapter 18 and changes the governed 22-chapter architecture without present evidence of overload.

### Rank 3 — Wired observability only; defer standalone models

**Boundary.** Teach the legacy `g_tu` counters and logging trace because they have ordinary-operation effects; omit or defer standalone performance counters, `event_trace`, cycle model, and power model.

**Benefit.** Narrowest executable-integration story and least risk of implying unsupported runtime composition.

**Why not selected.** It would mistake reachability for coverage. The disconnected and partly connected surfaces are precisely where users can misread names, docs, and green tests. Deferring them would leave the planned measurement-provenance reader decision incomplete.

### Rank 4 — Energy-first architecture trade-off chapter

**Boundary.** Center Chapter 17 on pJ/MAC, memory hierarchy energy, technology scaling, area, and TOPS/W; treat counters and tracing as supporting infrastructure.

**Benefit.** Attractive architecture-design narrative and clear multi-objective trade-offs.

**Why not selected.** The pinned energy tables are uncalibrated for Tusim, producer calls are not integrated into ordinary operation, and the source makes stronger calibration statements than current evidence supports. An energy-first chapter would invite physical recommendations before action counts, intervals, and clocks are trustworthy.

## Fresh source and evidence inventory

### Build, test, and archive classification

A disposable `git archive` of the exact pin was built outside the source checkout. Focused programs were linked explicitly against the freshly built static archive; `cycle_model.c` and `performance_counters.c` were compiled directly because `cycle_model.o` is not an archive member.

| Surface | Implementation size | Focused evidence | Make rule | In aggregate `make test` | Archive status | Fresh disposable result |
|---|---:|---|---:|---:|---|---|
| performance counters | 687 C + 267 H lines | `tests/test_perf_counters.c` (305 lines) | `test-perf` | yes | linked | 12/12, rc 0 |
| `perf/event_trace` | 228 C + 136 H lines | `tests/test_trace.c` (192 lines) | `test-trace` | yes | linked | 31/31, rc 0 |
| logging event buffer/VCD | 288 C + 157 H lines | `tests/test_logging.c` (219 lines) | `test-logging` | yes | linked | 7/7, rc 0 |
| cycle model | 767 C + 441 H lines | `tests/test_cycle_model.c` (532 lines) | none | no | **not linked** | runner-compiled 21/21, rc 0 |
| standalone power model | 641 C + 350 H lines | `tests/test_power_model.c` (544 lines) | `test-power` | no | linked | 20/20, rc 0 |
| manual benchmark consumer | test source, 450 lines | `tests/test_benchmark.c` | `test-bench` | no | test-only | rc 0; no fail-closed result count |

A green focused program proves only the exercised standalone contract. It does not prove an ordinary-operation caller, configuration effect, common interval, common clock, physical calibration, or safe cross-surface composition.

### Producer/caller/interval/unit/config/clock matrix

| Surface / producer | Producer and real caller at the pin | Interval and reset | Units | Configuration path | Clock or timestamp contract | Framing conclusion |
|---|---|---|---|---|---|---|
| legacy `tu_state_t` ledgers | `tu_cmodel.c`, dataflow callbacks, DMA wrappers, and engine-local code update `total_dma_bytes`, MMA calls/tiles/FLOPs, and `estimated_cycles`; ordinary public operations reach parts of this state | process-global or core-snapshot lifetime; lifecycle behavior differs by field family | bytes, calls, tiles, FLOPs, source-formula “cycles” | runtime geometry and selected compiled constants; no universal metric selector | no proved common elapsed clock across DMA, dataflow, engines, and controller ledgers | import as an existing producer family; do not treat it as the new performance-counter subsystem |
| `tu_perf_counters_t` | explicit `tu_perf_*record*` calls; non-test implementation caller is the separate `cycle_model.c`; tests and `test_benchmark.c` call it manually; no ordinary `g_tu`/`tu_core_t` ownership was found | caller-owned object lifetime; reset; snapshot/diff; merge | bytes, words, events, MACs, FLOPs, caller-supplied cycles, pJ, derived rates | full config parses `counters_enabled`; runtime conversion retains it; ordinary initialization has no counter-object construction/consumer | `total_cycles` is an additive ledger advanced by recording calls and explicit ticks at a caller-supplied MHz, not observed wall time | linked and focused-tested, but not uniformly wired; every field needs a producer census |
| `perf/event_trace` context | only its implementation, focused test, and docs call `tu_trace_create/add_signal/signal/tick`; no non-test workload caller found | caller-owned trace context from create to close; explicit tick deltas | signal values plus integer `current_cycle`; VCD header declares 1 ns | full config parses `performance.tracing.{enabled,output_file}` and runtime conversion retains both; no context creation consumes them; private `g_trace_enabled` remains false | caller-selected tick increments are emitted beneath a fixed `1 ns` timescale; no mapping to the cycle model or core clock | standalone VCD writer, not integrated cycle tracing |
| logging event buffer/VCD | `tu_mma()` calls `tu_trace_event()` directly; tests are the only callers of `tu_trace_set_cycle()` found | process-global fixed buffer, cleared explicitly; events stop silently at 65,536 | event count, component/opcode, four 32-bit operands, global integer cycle | separate `tu_log_config_t.trace_enabled/trace_file`; default init does not gate `tu_trace_event`; runtime trace config is not copied into this logging config | ordinary MMA events use the untouched global trace cycle (normally zero); tests manually set 0/10/20 | a second, incompatible trace producer; it must not be described as the same `event_trace` stream |
| `cycle_model` | explicit standalone API; callers found only in its focused test and docs | model-object lifetime; own reset reconstructs submodels | source-defined cycles, accesses, words, stalls, conflicts, bytes, rates | mode passed explicitly; submodels use compiled `TU_*` constants; parsed `tu_config_t.cycle_model` is omitted by `tu_config_to_runtime()`; object absent from `TU_OBJS` | private `current_cycle`; calls may feed a separately supplied `tu_perf_counters_t`; ordinary core operations do not advance it | source-present estimated model despite `CYCLE_ACCURATE` name; no runtime integration or calibration is established |
| embedded power counters inside `tu_perf_counters_t` | performance-counter recording calls add pJ using manually configured scalar costs | same interval as the owning perf object and its additive cycle ledger | pJ, pJ/MAC, derived mW | manual `tu_perf_power_config`; not the standalone technology-node table | leakage and average power depend on perf `total_cycles` and caller-supplied MHz | one energy producer; keep separate from `tu_power_model_t` |
| standalone `tu_power_model_t` | explicit `tu_power_record_*` and `tu_power_tick`; callers found only in test/docs; `tu_power_model_from_config()` has no non-test caller | model-object lifetime; reset; snapshot/diff | action counts, pJ, mW, mm², MHz, V | direct full-config helper heuristically selects 7/5 nm and 1/2 GHz from PE geometry and DRAM bandwidth; `counters_enabled` gates it; no ordinary constructor call | own caller-advanced `total_cycles` at its own MHz; unrelated to perf, trace, cycle-model, DRAM, engine, or controller clocks unless a caller explicitly bridges them | linked table-based estimator, not ordinary-operation energy and not sign-off/calibrated Tusim power |
| `test_benchmark.c` manual consumer | executes core MMA/DMA but separately invents transfer costs and a tile formula, then records them into a private perf object | one benchmark context | manually supplied bytes/FLOPs/cycles and derived rates | fixed 1 GHz perf clock plus runtime core geometry | `tu_perf_compute_record_mma()` already ticks the perf ledger, then `bench_mma()` explicitly calls `tu_perf_tick(cycles)` again; compute time is double-added before DMA records | useful forensic consumer, not measured application performance or an integration certificate |
| Chapter 14–16 engine/DRAM/controller metrics | distinct producers already sealed by prior chapters | engine call, DRAM caller window, controller lifetime, or manual report interval | heterogeneous cycles, stalls, events, bytes, ratios | producer-specific | no common clock proved | contrast examples only; Chapter 17 must not reopen or sum them |

## Fresh contradictions and high-value audit questions

1. **“Called by DMA” declaration versus callers.** `tu_perf_from_dma_descriptor()` says descriptor execution calls it, but the only actual call found is its focused test.
2. **“Called automatically during `tu_core_create()`” versus callers.** `tu_power_model_from_config()` has no non-test caller.
3. **Trace config versus execution.** Full config parses and retains trace enable/file fields, but `perf/event_trace` creates no context from them; its private enable flag has no setter and stays false.
4. **Two trace implementations.** The event-trace context and the logging event buffer share `tu_trace_*` naming but have different types, storage, callers, intervals, VCD schemas, and clocks.
5. **Ordinary trace timestamp.** `tu_mma()` emits a logging trace event, but no non-test caller advances the logging trace cycle, so ordinary events are not a demonstrated temporal execution trace.
6. **Cycle-model reachability.** The cycle model is source-present, runner-compilable, and focused-green but absent from `TU_OBJS`, has no Makefile test rule, and has no non-test caller.
7. **Parsed mode is not selected mode.** JSON/YAML carry cycle-model requests; the parser stores `tu_config_t.cycle_model`; runtime conversion drops it; the standalone model takes an explicit mode and compiled constants.
8. **Counter time is producer time.** DMA, compute, memory-stall, idle, and explicit tick calls all add to `total_cycles`; serial addition is an accounting policy, not observed concurrency.
9. **Cycle-to-counter coupling needs exact accounting.** Cycle-model tile/DMA calls invoke perf recording APIs that themselves tick the perf ledger; `tu_cycle_model_advance()` also ticks it. Caller composition can duplicate intervals.
10. **DMA direction defect candidate.** The cycle model records every modeled DMA transfer with `tu_perf_dma_record_read()` even when `is_read` is false.
11. **Benchmark double-accounting candidate.** Its compute recorder advances total cycles, followed by a second explicit tick of the same computed interval.
12. **Two power models.** The embedded perf-energy scalars and standalone technology-node model differ in action granularity, tables, area/leakage treatment, config paths, and clock ownership.
13. **Calibration language is unproven.** Tusim power docs/source use “calibrated,” “CACTI-derived,” and accuracy percentages without a retained CACTI invocation, characterized table provenance, fitting record, or Tusim-to-RTL/silicon comparison in the inspected evidence.
14. **Documented VCD behavior is not sufficient evidence.** The event-trace docs claim config-created tracing and no-ops when disabled, while the source API remains explicitly caller-driven and does not check that config.
15. **Green test scope.** `test-power` and `test-bench` are outside aggregate `make test`; the cycle suite has no Makefile rule; the benchmark returns zero without a summarized fail-closed oracle.

These are framing findings, not yet ledger claims. The next stage must hash, predicate, probe, and skeptically review them before drafting.

## Selected chapter boundary

### In scope

1. A general measurement contract: producer, caller, event/action definition, interval, denominator, units, clock, configuration authority, reset/merge semantics, fidelity, and calibration.
2. Legacy top-level counters as contrast to the newer `tu_perf_counters_t` surface.
3. Performance-counter recording, additive time, snapshots/diffs/merges, derived rates, and reachability.
4. Both trace producers, their schemas, timestamps, capacity/lifecycle, config gaps, and VCD claim limits.
5. The standalone cycle model as a separately linked and separately clocked estimate; mode/config/linkage and perf-coupling boundaries.
6. Embedded perf energy and standalone power-model energy as two different action-count estimators.
7. The manual benchmark as a consumer-side provenance case study.
8. Cross-producer comparison rules: equality, subtraction, normalization, rate derivation, and summation are allowed only after producer/interval/unit/clock compatibility is proved.
9. Architecture alternatives: ad hoc ledgers, monotonic counter banks, event streams, trace-driven reconstruction, explicit cycle simulators, action-count energy models, and externally calibrated models—with performance, area/power, complexity, and verification costs.

### Explicitly out of scope

- A unified Tusim elapsed timeline, total latency, total energy per inference, or TOPS/W result.
- Treating Chapter 14 engine returns, Chapter 15 DRAM clocks, or Chapter 16 controller ledgers as one clock.
- Re-teaching each prior subsystem’s implementation.
- Verification architecture, CI design, mutation methodology, and evidence-selection taxonomy owned by Chapter 19.
- Physical sign-off power, technology-node recommendations, thermal/DVFS modeling, or claims that hardcoded tables reproduce CACTI, RTL, FPGA, or silicon.
- Changing Tusim source, fixing instrumentation, or proposing one mandatory integrated architecture; design improvements remain evidence-backed future work.

## Planned source hierarchy

### Pinned implementation authority

- `tu_cmodel/tu_cmodel.{h,c}`, `tu_core.{h,c}`, `tu_config.h`
- `tu_cmodel/infra/config.{h,c}`, `logging.{h,c}`
- `tu_cmodel/perf/performance_counters.{h,c}`
- `tu_cmodel/perf/event_trace.{h,c}`
- `tu_cmodel/perf/cycle_model.{h,c}`
- `tu_cmodel/perf/power_model.{h,c}`
- Makefile recipes/archive membership and the focused/config/benchmark tests listed above
- the four current docs, treated below executable source and tests
- prior sealed Chapter 14–16 evidence only for named contrast producers

### Primary literature already verified in `references/foundations.md`

- [SHA14] Aladdin: pre-RTL dependence/resource performance modeling; no transfer of validation to Tusim.
- [SAM18] SCALE-Sim: configurable systolic performance modeling; “cycle accurate” remains abstraction-bounded.
- [PAR19] Timeloop and [KWO19] MAESTRO: explicit workload/mapping/resource assumptions for analytical metrics.
- [WU19] Accelergy: action counts plus plug-in energy values; uncertainty propagates from counts and component models.
- [JOU17] TPU and [GEN21] Gemmini: measured/system evidence is implementation- and workload-specific and must not be transferred numerically.

### Metadata and authority still required before the claim ledger

- Verify the exact official IEEE VCD specification edition/identifier and inspect the normative timestamp/value-change clauses; do not rely on the Tusim docs’ “IEEE 1364-2001” label alone.
- Verify the exact Horowitz ISSCC record cited by `power_model.c` and bound what its operation-energy examples establish.
- Locate an exact first-party CACTI version/release or paper matching the source’s “CACTI 7.0” claim. If no table-generation artifact maps CACTI inputs to Tusim constants, classify the constants as undocumented/hardcoded estimates rather than CACTI-reproduced values.
- Verify any vendor architecture/whitepaper identifiers before using A100/H100/TPU power figures; chip-level TDP divided by peak throughput must not be presented as per-MAC circuit energy calibration.
- Seek a primary performance-counter/PMU source only for general interval/event semantics; vendor semantics must remain vendor-scoped.

## Planned claim families and evidence ladders

1. **Identity and reachability:** source present → archive member → linked → public/runtime caller → ordinary operation → discriminating effect.
2. **Configuration:** declared → defaulted → parsed → validated → converted → retained → consumed → observable A/B effect.
3. **Producer semantics:** exact increment site, event/action represented, success/failure dependence, caller-supplied versus derived values.
4. **Interval semantics:** construction/reset/snapshot boundaries, wrap/underflow behavior, merge rules, lifecycle, and object/global ownership.
5. **Units and dimensions:** bytes versus words/accesses/events; MACs versus FLOPs; cycles versus ns; pJ versus mW; frequency conversion and denominator.
6. **Clock ownership:** caller tick, source formula, cycle-model state, VCD timestamp, logging cycle, DRAM window, engine return, and controller ledger remain distinct until a bridge is proved.
7. **Derived metrics:** reproduce every formula and denominator; check zero intervals, duplicated ticks, omitted fields, mixed frequencies, and impossible bounds.
8. **Energy/area provenance:** action counts, table values, node/voltage/frequency assumptions, area heuristic, leakage interval, calibration artifact, and uncertainty.
9. **Documentation fidelity:** “implemented,” “integrated,” “cycle accurate,” “zero overhead,” “calibrated,” and “called automatically” must be checked against source and callers.

## Executable audit plan for the next stage

No canonical audit is authorized by this framing file. The next stage should create the Chapter 17 claim ledger first, then a fail-closed archive-only audit with at least these discriminators:

1. Hash all four perf families, config/runtime/core/logging surfaces, Makefile, focused tests, benchmark, docs, and claim-bearing book inputs.
2. Enforce exact library-member, Make-rule, aggregate-membership, and non-test caller inventories.
3. Probe ordinary `tu_mma()` before/after legacy counters, `tu_perf_counters_t`, both trace stores, cycle-model state, and both power models.
4. Probe config A/B paths for `cycle_model`, counters, detailed stalls, trace enable/file, geometry, and DRAM bandwidth; distinguish full-config direct consumers from runtime conversion.
5. Construct a literal interval census showing which recording calls advance perf total cycles, compute cycles, memory stalls, energy leakage, and wall-clock conversion.
6. Mutation-test snapshot/diff/merge field coverage, reset behavior, decreasing snapshots, mixed frequency, and enable transitions.
7. Prove or reject the benchmark double-tick and cycle-model DMA-direction findings with exact expected values.
8. Generate both trace formats for the same bounded operation; compare event identity, timestamp progression, schema, and overflow behavior without calling either a hardware waveform.
9. Compare the cycle model’s functional/estimated/named-cycle-accurate modes on one discriminating tile and one DMA transfer; keep its clock separate from direct MMA, DRAM Chapter 15, and pipeline Chapter 16.
10. Feed one identical explicit action census into embedded perf energy and standalone power energy; explain every difference in action granularity, parameters, area/leakage, and interval.
11. Recompute representative pJ, average-power, area, bandwidth, throughput, utilization, hit-rate, and efficiency formulas dimensionally.
12. Retain focused green controls and forced-failure mutations; do not let test success certify caller reachability or calibration.
13. Verify source and book repositories before and after; all builds and probes run only in a disposable archive.

## Skeptical predraft gate

Drafting remains blocked until an independent review can answer **yes** to all of the following:

1. Does every number name exactly one producer and caller?
2. Does every interval have explicit start/reset/snapshot/end semantics?
3. Are event, action, byte/word/access, MAC/FLOP, cycle/ns, pJ/mW/mm² units dimensionally correct?
4. Are the two trace producers and two power producers kept separate everywhere?
5. Is `cycle_model` described as source-present/non-archive/non-ordinary-operation unless new evidence disproves that classification?
6. Are config declarations separated from parsed, converted, consumed, and effect-proven settings?
7. Does every derived rate state its denominator and frequency source?
8. Are snapshot, diff, merge, reset, overflow, and lifecycle exceptions complete?
9. Are benchmark/manual-recording values labeled as caller-authored estimates rather than measurements?
10. Are prior engine/DRAM/controller counters used only as named contrasts, never summed?
11. Are “cycle accurate,” “calibrated,” “CACTI-derived,” and vendor-energy claims bounded by inspected primary evidence and retained calibration artifacts?
12. Does the scope remain Chapter 17 measurement semantics rather than Chapter 19 verification methodology?

## Exact next action

Create `notes/chapter-17-source-and-claim-ledger.md` from this selected boundary. Preserve separate claim identifiers for every producer, caller, interval, unit, configuration path, clock, derived metric, and calibration statement. Do not draft manuscript prose or create a canonical run until the ledger and its explicit limitation wording are complete.