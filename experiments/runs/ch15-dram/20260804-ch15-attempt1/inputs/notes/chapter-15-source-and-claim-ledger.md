# Chapter 15 — Source and Claim Ledger

**Title:** DRAM Service Models and Bandwidth Claims  
**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (read-only)  
**Status vocabulary:** verified / qualified / rejected / blocked.  
**Evidence precedence:** executable reproduction > focused tests > headers/current source > current docs > historical reports.

## Standalone model and equations

- **C15.1 (verified):** `dram_model.[ch]` is linked into `libtucmodel.a` and exposes ideal, HBM2, HBM2e, HBM3, DDR4, DDR5, LPDDR5, and custom records. Preset names and fields are executable declarations, not validated device models.
- **C15.2 (verified):** The bulk estimator is stateless: for non-ideal models it returns `ceil(num_bytes / bandwidth_gbps) + selected_latency`, because the implementation assumes 1 GHz and treats numeric GB/s as bytes/cycle. It does not consult current time, channel availability, pending bytes, bandwidth window, row mode, bus width, burst length, bank count, or row size. Probe: HBM2 64-B read = 51; HBM3 819-B read = 41.
- **C15.3 (verified):** A newly created non-ideal model has `current_cycle=0`, `bandwidth_available=0`, and `bw_window_size_cycles=0`. The first `ensure_bandwidth()` establishes a 1,000-cycle window but does not fill its budget; therefore the first positive-size access is charged a 1,000-cycle bandwidth stall.
- **C15.4 (verified):** `tu_dram_read/write()` return base latency in `cycles_out` and contention in `stall_out` separately. They update channel availability and counters but do not advance `current_cycle`; neither output is elapsed completion time by itself.
- **C15.5 (verified):** Channel selection is `(addr / burst_length) % num_channels`. At fixed caller time, a repeated access to the same HBM2 channel adds the prior 50-cycle availability gap; an access to a fresh channel avoids that term but still receives the empty-budget window stall. No queue, completion event, or data transfer is modeled.
- **C15.6 (verified):** After exactly 1,000 calls to `tu_dram_tick()`, the HBM2 budget refills to `256 × 1000 = 256000` bytes, pending counters reset, and a 64-B access on an available channel has stall 0 and leaves 255936 bytes. This is a fixed non-sliding refill window controlled entirely by caller ticks.
- **C15.7 (verified):** Enabling row modeling adds a flat ten cycles and increments `total_row_conflicts` on every read; there is no row identity/open-row state. The write path contains no row-mode branch. “Row hit/miss model” is rejected; “optional flat read penalty” is verified.
- **C15.8 (verified):** `tu_dram_set_core_clock()` discards both arguments. Stateful metering and the estimator assume 1 GHz internally, while `tu_dram_peak_bw_per_cycle()` accepts an independent clock argument. HBM2 reports 256 B/cycle at 1 GHz and 128 at 2 GHz without mutating the model.
- **C15.9 (verified/qualified):** Derived effective bandwidth is cumulative bytes divided by `max(current_cycle,1)` under a fixed 1 GHz conversion. A 1,024-B read at cycle zero reports 1,024 GB/s and utilization 4.0 against HBM2's 256 GB/s. Values are caller-clock-dependent arithmetic and are not clamped achieved bandwidth.
- **C15.10 (verified):** Ideal DRAM is a special functional sentinel: reads/writes report zero cycles/stalls and only increment byte/access counters; it still has no backing store.
- **C15.11 (qualified):** Several preset fields are decorative in the standalone access path. `bus_width_bytes`, `banks_per_channel`, and `row_buffer_size` do not affect access or estimator equations; burst length affects channel mapping; channels allocate availability state; bandwidth and latency affect named equations.
- **C15.12 (verified, static):** Type validation checks only `type >= TU_DRAM_TYPE_COUNT`; a negative cast can index before `dram_names`/`dram_presets`. This undefined path is recorded statically and must not be executed.

## Hierarchy, DMA, and configuration reachability

- **C15.13 (verified):** `tu_mem_hierarchy_init()` constructs HBM2 unconditionally (falling back to ideal only on allocation failure), not from full/runtime config or compiled `TU_DRAM_TYPE`.
- **C15.14 (verified):** Hierarchy DRAM reads/writes call the standalone model but discard `cycles_out`, retain only `stall_out`, and perform no backing-store byte copy. A DRAM “read” leaves the caller buffer unchanged. Hierarchy ticks advance both hierarchy and DRAM clocks explicitly.
- **C15.15 (verified):** Descriptor DMA has no `tu_dram_*` call. Its service estimate remains separate from the standalone DRAM model; Chapter 10's integration boundary remains authoritative.
- **C15.16 (verified):** JSON/YAML declare DRAM type, bandwidth, row mode, core clock, and latency values, but the parser reads type/bandwidth/row mode and memory latency only. `core_clock_ghz` is ignored; `dram_channels` remains its default because the shipped DRAM block has no channels key and the parser has no reader there.
- **C15.17 (verified):** `tu_config_to_runtime()` drops all DRAM fields. The runtime config has no standalone DRAM object. An explicit caller can manually pass parsed `dram_type` to `tu_dram_create`, but enum construction uses preset bandwidth/row mode rather than the parsed overrides.
- **C15.18 (verified):** Full-config validation contains no DRAM-type, positive-bandwidth, channel-count, latency, or clock validation. Unsupported DRAM strings silently map to ideal through `parse_dram_type_str()`.
- **C15.19 (verified):** A separate DRAM channel implementation exists in `perf/cycle_model.[ch]`, with row state and different equations. It is absent from `TU_OBJS` at the pin and is not the standalone model. Chapter 15 uses it only to prevent false conflation; Chapter 16 owns its detailed metric provenance.

## Test and document provenance

- **C15.20 (verified):** `test-dram` is a real Makefile target and a member of aggregate `make test`; its focused harness reports 12/12 and returns nonzero on a failed test. Static archive linkage must be forced by the chapter runner to avoid stale shared-library selection from `-L. -ltucmodel`.
- **C15.21 (qualified):** The focused suite checks type creation, custom-field retention, ideal zero results, nonzero preset latency, counters, broad estimator ranges, null behavior, reset, tick count, peak conversion, print survival, and positive preset fields. It does not gate initial refill, returned-cycle/stall separation, same/different-channel behavior, row read/write asymmetry, over-peak derived utilization, config reachability, hierarchy byte effects, or DMA integration.
- **C15.22 (rejected/qualified):** `docs/dram-model.md` claims cycle-accurate access modeling, sliding-window-like bandwidth behavior, realistic row hit/miss, DMA query integration, and physically sourced presets. At the pin, the safe replacements are deterministic caller-ticked accounting, fixed-window refill, flat read penalty, future DMA integration, and uncalibrated source constants.
- **C15.23 (qualified):** `docs/exploration/dram-type-clock-sweep.md` is a 42-point analytical table using `min(bus_bytes_per_cycle, DRAM_GB/s / clock)` plus a separate compute formula. It does not call `dram_model.c`, does not include its preset latency/access state/window/channel equations, and must be labeled historical analytical evidence rather than standalone-model execution.
- **C15.24 (blocked):** No audited source establishes calibration against RTL, FPGA, silicon, DRAMSim/Ramulator, or measured device traffic. Exact physical latency, sustained bandwidth, row-hit rate, energy, and technology recommendations are blocked.

## Audit-integrity claims

- **C15.25 (planned):** `ch15_source_audit.py` will pin the relevant source/config/test/doc hashes and enforce entry-point, equation, reachability, test-membership, and documentation-conflict predicates; a source mutation must fail and restoration must pass.
- **C15.26 (planned):** The probe and focused tests will compile explicitly against the rebuilt static archive with no `NEEDED libtucmodel` dependency.
- **C15.27 (planned):** A focused-test mutation will produce a nonzero result with the expected pass-count change.
- **C15.28 (planned):** Canonical provenance will prove detached/clean Tusim at the pin before/after, unchanged ignored inventory, immutable bundled inputs, unchanged book state outside the run, and no push.
