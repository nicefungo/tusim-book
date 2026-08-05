# Chapter 17 — Source and Claim Ledger

**Title:** Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy
**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (read-only)
**Status vocabulary:** verified / qualified / rejected / blocked
**Predraft status:** open; drafting is blocked until a post-review canonical seal closes the gate.

## Measurement contract

- **C17.1 (verified):** Every observation requires a producer, caller, event/action definition, interval, units, configuration authority, clock/timestamp owner, derivation, and fidelity label. Shared field names do not establish shared semantics.
- **C17.2 (rejected):** Tusim has no proved unified elapsed timeline at the pin. Legacy state ledgers, performance-counter time, event-trace ticks, logging trace cycles, cycle-model state, DRAM windows, engine returns, controller ledgers, and power-model cycles may not be summed without an explicit bridge.
- **C17.3 (qualified):** Equality, subtraction, normalization, and rate comparison are valid only for compatible producers and intervals. A numerical match is not evidence of common ownership or calibration.

## Legacy state and performance counters

- **C17.4 (verified):** `tu_state_t` owns legacy byte, MMA, FLOP, tile, and `estimated_cycles` ledgers reached by ordinary core operations. Their producers and reset/snapshot behavior are field-specific; they are not aliases of `tu_perf_counters_t`.
- **C17.5 (verified):** `tu_perf_counters_t` is caller-owned, library-linked, and focused-tested. No ordinary `g_tu` or `tu_core_t` constructor owns one. Its non-test implementation caller is the separately compiled `cycle_model.c`; the benchmark records values manually.
- **C17.6 (rejected):** The header statement that `tu_perf_from_dma_descriptor()` is called by descriptor execution is false at the pin. No descriptor implementation call exists.
- **C17.7 (verified):** Perf recording functions advance `total_cycles` additively: DMA read/write add active+stall, internal DMA adds active, MMA/op adds active+stall, idle adds idle, SPAD/DRAM add only supplied stall, and explicit `tu_perf_tick()` adds its argument. The descriptor helper composes DMA time and optional SPAD stall. GBuf, request-file, and pipeline-bubble recorders add no time.
- **C17.8 (qualified):** `wall_clock_ns = floor(total_cycles / clock_freq_mhz * 1000)`. It is a conversion of the caller-authored additive ledger, not observed host time or a hardware clock.
- **C17.9 (verified):** `tu_perf_compute_record_mma()` classifies dataflow 0 as WS and every nonzero value as OS; storage has no RS bucket. A label is not evidence of the dataflow actually executed.
- **C17.10 (qualified):** Snapshot is a byte copy plus snapshot cycle. Diff clamps decreasing integer fields to zero but directly subtracts energy doubles; it omits both WS/OS cycles, GBuf conflicts, both DRAM row hit/miss fields, all three bandwidth-utilization fields, wall time, and all six scalar energy parameters plus the embedded power-enable flag. Merge omits the same field families, `energy_total_pj`, outer counter enable, and outer clock frequency. The source audit checks every named field and the probe gives each family a nondefault sentinel; neither operation is a complete algebra over the struct.
- **C17.11 (qualified):** Reset reconstructs counters while preserving the entire prior power substructure, including accumulated energy as well as parameters. The comment “keep energy parameters” is narrower than behavior; reset is not a full energy reset.
- **C17.12 (qualified):** Derived DMA/DRAM bandwidth, TOPS, efficiency, energy/MAC, and average power divide caller-recorded numerators by caller-authored `total_cycles` and frequency. Peak efficiency uses compiled `TU_PE_ROWS*TU_PE_COLS`, not runtime core geometry. MAC efficiency is unclamped and can exceed one; `spad_hit_rate = 1-conflicts/accesses` can be negative. Embedded `power_mw` has an extra factor of 1,000: 1 pJ over 1 ns reports 1,000 mW rather than 1 mW.
- **C17.13 (rejected):** The manual benchmark is not a measurement or integration certificate. It invents fixed DMA costs and an MMA formula, records MMA cycles through `tu_perf_compute_record_mma()`, then ticks the same compute interval again, exactly double-adding compute time. It returns zero without a fail-closed result-count oracle.

## Two trace producers

- **C17.14 (verified):** `perf/event_trace` is a caller-owned signal-change VCD writer. Its callers are implementation/tests/docs only; no ordinary workload caller creates a context or signals it.
- **C17.15 (qualified):** The first `tu_trace_tick(trace, delta)` writes the header and `#0` then returns without applying `delta` or flushing pending changes. Later ticks flush at the old time and then advance. The fixed `$timescale 1 ns` declaration does not prove caller deltas are nanoseconds.
- **C17.15a (rejected):** `tu_trace_close()` does not emit a dedicated documented EOF marker. It may flush pending values and emits a final timestamp equal to `current_cycle`; the focused test's search for `$end` is satisfied by ordinary header directives and does not prove an EOF record.
- **C17.16 (rejected):** Parsed/retained trace enable and output-file fields do not create or gate an event-trace context. The implementation-private `g_trace_enabled` has no setter and remains false, while public create/signal/tick do not consult it.
- **C17.17 (verified):** `infra/logging` owns a second process-global fixed event buffer, cycle scalar, and VCD exporter. `tu_mma()` calls `tu_trace_event()` directly; trace-enable configuration does not gate event insertion.
- **C17.18 (qualified):** The logging buffer silently drops events after 65,536; clear resets count and cycle; ordinary non-test callers do not advance its cycle, so ordinary MMA events normally retain timestamp zero. The VCD exporter emits event timestamps only on strict increases, placing equal/decreasing events under the prior timestamp, then emits the final global cycle even if it regresses.
- **C17.19 (rejected):** The two trace families are not one stream. They differ in storage, schema, capacity, lifecycle, callers, tick semantics, config path, and timestamp ownership.
- **C17.20 (qualified):** VCD syntax records ordered timestamp/value changes under a declared timescale; VCD compliance does not validate that Tusim timestamps represent physical nanoseconds or a complete execution waveform.

## Standalone cycle model

- **C17.21 (verified):** `perf/cycle_model.[ch]` is source-present, runner-compilable, and focused-green 21/21, but `cycle_model.o` is absent from `TU_OBJS`, there is no Makefile test rule, and no non-test caller outside its own implementation.
- **C17.22 (rejected):** Parsed `tu_config_t.cycle_model` is not the selected runtime mode. `tu_config_to_runtime()` drops it; model construction takes an explicit mode and compiled `TU_*` constants.
- **C17.23 (qualified):** `FUNCTIONAL` returns zero accounting; it does not verify function. `ESTIMATED` uses fill+compute+drain. The enum named `CYCLE_ACCURATE` executes a source-defined serial heuristic with pipeline, bank, DRAM, and DMA submodels; no RTL/silicon calibration or ordinary runtime integration is established.
- **C17.23a (qualified):** The top-level named-cycle tile call completes each issued entry within the same call. Ordinary sequential calls therefore do not demonstrate overlapping in-flight hazards; the focused hazard test synthesizes tracker state directly. DMA arbitration likewise depends on manually populated channel-cycle state rather than an ordinary queued transfer path.
- **C17.23b (rejected):** Bank `conflict_count` increments after any nonzero access that leaves the budget below maximum, including one isolated, nonstalling access. Reported average utilization divides cumulative accesses by one instantaneous bank-capacity constant, without an elapsed-window denominator, and can exceed one.
- **C17.24 (verified):** In named-cycle mode, tile execution advances private model time and then the attached perf MMA recorder independently advances perf time by the same elapsed interval. `tu_cycle_model_advance()` also advances both. These are explicit coupling policies, not proof of one global simulator clock.
- **C17.25 (rejected):** `tu_cycle_model_dma_transfer()` always calls `tu_perf_dma_record_read()`, including when `is_read=false`; modeled writes therefore populate perf read counters and leave write counters zero.
- **C17.25a (rejected):** The cycle-model DMA boolean `is_read` is passed directly to `tu_dram_access()`'s `is_write` parameter. For fresh HBM2 channels at 1 GHz and four bytes, the read argument gets 21 cycles while the write argument gets 28: DRAM timing direction is reversed, in addition to the perf-direction defect.
- **C17.25b (qualified):** Cycle-model reset reconstructs every non-ideal DRAM channel at 1 GHz and does not reset the attached perf object. For HBM2E/HBM3 this changes the creation-time frequency, while prior perf counters survive.
- **C17.26 (qualified):** DMA perf recording receives the whole model elapsed interval as `active_cycles` and arbitration again as `stall_cycles`, so arbitration can be counted twice in perf total time. SRAM stall is not separately passed to perf memory counters.
- **C17.27 (qualified):** Cycle-model bank identity uses raw byte-address modulo bank count rather than generic SRAM's `(addr/bank_width)%banks`; its DRAM and bank state are private. Results do not transfer to direct MMA or Chapter 15 DRAM.

## Two energy producers

- **C17.28 (verified):** Embedded perf energy uses caller-configured scalar pJ costs and action calls. DMA reads charge DRAM energy by `active_cycles`, writes do not; DRAM action calls charge once per call; leakage advances only with perf ticks.
- **C17.28a (rejected):** Embedded `energy_total_pj` has no recorder producer. Metrics and reports sum six component fields directly; the cached-looking total can remain zero after nonzero energy activity.
- **C17.29 (verified):** `tu_power_model_t` is a separate table-based action-count estimator with precision-dependent MACs, hierarchy actions, 64-byte DRAM transactions, page-miss activation, DMA bytes, clock-tree cycles, heuristic area, leakage, snapshots, and its own frequency.
- **C17.30 (rejected):** `tu_power_model_from_config()` is not automatically called by `tu_core_create()`; its callers are tests/docs only. It heuristically chooses node/frequency from PE geometry and DRAM bandwidth and gates enable from `counters_enabled`.
- **C17.31 (qualified):** Standalone reset preserves node/frequency/enabled and clears activity. Standalone diff directly subtracts unsigned activity and cycles, so decreasing snapshots wrap rather than clamp; energy differences can be negative.
- **C17.32 (qualified):** Average power is energy divided by the model's caller-advanced cycle interval and MHz. Area uses `(MAC area + SPAD area + GBuf area)*1.30`; the 30% overhead and node tables are heuristics.
- **C17.32a (qualified):** `energy_total_pj` is cached, not continuously maintained. After `tu_power_compute_total()`, later action recording leaves the cached total stale; `tu_power_get_avg_power_mw()` reuses a nonzero stale total and `tu_power_get_energy_per_mac()` recomputes only when the cache equals zero. Recompute explicitly after the final action.
- **C17.32b (qualified):** Several table parameters—including DRAM idle power, NoC-hop energy, PE-register energy, and per-byte memory leakage values—are declared but not consumed by the retained total-energy path. Table presence is not action coverage.
- **C17.32c (qualified):** Standalone reset preserves node/frequency/enable but loses the prior area estimate, disabling area-dependent leakage until area is recomputed. `tu_power_get_energy_per_mac(const ...)` casts away const and may populate the cached total as a read-side effect.
- **C17.33 (rejected):** Source/docs words “calibrated” and “CACTI-derived” are unsupported for Tusim by a retained CACTI invocation, table-generation record, fitting method, or comparison against RTL/FPGA/silicon. Hardcoded tables are estimated inputs.
- **C17.34 (qualified):** Horowitz 2014 supports order-of-magnitude operation/data-movement examples for a stated process and methodology, not Tusim's FP16 MAC, memory, node-scaling, or chip-level tables. Vendor TDP/peak ratios do not establish per-MAC circuit energy.
- **C17.35 (rejected):** Embedded perf energy and standalone power energy cannot be compared as if they observed the same action census unless a caller explicitly maps actions, parameters, area, interval, and clock. The pin supplies no such bridge.

## Configuration, tests, documents, and scope

- **C17.36 (verified):** Full config parsing, runtime conversion, standalone full-config helpers, compiled constants, manual construction, and ordinary-operation effects are distinct configuration surfaces.
- **C17.37 (qualified):** `test-perf`, `test-trace`, and `test-logging` have Make rules and aggregate membership. `test-power` and `test-bench` have rules but are outside aggregate `test`. Cycle-model test source has no rule and is runner-compiled.
- **C17.37a (rejected):** Shipped JSON and YAML declare `power.enabled` and `power.model`, but the JSON loader does not parse a power block and no ordinary consumer reads these shipped fields. This is separate from the standalone `tu_power_model_from_config()` helper, which heuristically consumes other full-config fields.
- **C17.37b (rejected):** Shipped tracing `format` is not parsed. `trace_max_events` is defaulted and documented in `tu_config_t` but is not parsed, converted to runtime config, or consumed by either fixed-capacity trace producer.
- **C17.37c (rejected):** `detailed_stalls` is parsed and copied into runtime config, but no implementation measurement producer reads it. Retention is not behavioral effect.
- **C17.38 (qualified):** Focused-green controls certify only their bounded standalone assertions. They do not certify caller reachability, config effect, common clocks, complete diff/merge coverage, physical timing, or calibration.
- **C17.39 (rejected):** Current performance, tracing, cycle, power, and benchmark documentation overstates automatic integration, cycle accuracy, measurement, zero-overhead disable behavior, or calibration where contradicted by pinned callers and executable behavior.
- **C17.40 (verified):** Chapter 17 owns measurement provenance and cross-producer comparison rules. Chapter 19 retains evidence selection, mutation methodology, CI, and verification architecture; prior chapter metrics appear only as named contrasts.
- **C17.41 (qualified):** Architecture alternatives are regime-specific: ad hoc ledgers minimize implementation cost but maximize semantic drift; monotonic counter banks improve low-overhead summaries but need exact event/interval contracts; event streams preserve ordering at storage/analysis cost; explicit cycle simulators can expose hazards at high model/validation cost; action-count energy models enable sensitivity studies but inherit action/table uncertainty; calibrated models require retained external references and ongoing maintenance.

## Predraft gate

Drafting remains blocked until a canonical archive-only run hashes all claim-bearing surfaces, enforces caller/config/build classifications, executes focused controls and forced failures, reproduces exact counter/trace/cycle/energy discriminators, seals immutable evidence, and receives independent skeptical review. Every surviving numeric statement must name one producer, interval, unit, clock, and limitation.
