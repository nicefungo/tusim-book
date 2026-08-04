# Chapter 15 DRAM Service Audit — 2026-08-04

- **Chapter:** DRAM Service Models and Bandwidth Claims
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical runner:** `experiments/run_ch15_dram_audit.sh`
- **Canonical retained run:** `experiments/runs/ch15-dram/20260804-ch15-canonical-v2/` (planned amended seal; supersedes v1 only after every gate passes)
- **Verdict vocabulary:** source predicates and executable observations match the pinned snapshot; this is not RTL, device, or silicon calibration

## Question

When Tusim emits a number labeled DRAM cycles, bandwidth, utilization, or stall, which API, clock, state transition, and caller produced it? The audit separates the standalone stateful access surface, its stateless bulk estimator, memory-hierarchy delegation, parsed configuration, descriptor-DMA reachability, and a historical analytical type×clock sweep.

## Scope decision

A whole-book review after Chapter 14 superseded the historical 29-chapter proposal with an evidence-compressed first edition. A later cross-chapter audit amended the target from 21 to 22 chapters after finding that prior chapters bounded but did not teach the standalone double-buffer surface. DRAM remains Chapter 15 because it is the last unaudited off-chip service model; Chapter 16 now covers double buffering/legal overlap, followed by metric provenance in Chapter 17. The decision and amendment are recorded in `PLAN.md` and `notes/whole-book-replanning-2026-08-04.md`. The canonical run bundles the pre-amendment report and 21-chapter plan at input commit `688fd1d`; this post-seal editorial amendment changes no frozen source or executable finding.

## Provenance and containment

The canonical runner must require detached/clean Tusim at the exact pin, clean book `main`, unchanged book remotes, unchanged ignored Tusim inventory, and no push. It exports the pin into a disposable tree, builds only the static archive, rejects dynamic Tusim dependencies, bounds binaries under GDB/timeout (a terminal lifecycle-guard workaround), preserves committed inputs and logs, creates a run-relative SHA-256 manifest, and verifies both repositories after execution. The pinned `make clean` recipe is not invoked because prior chapters established its process-global `/tmp` hazard.

## Static source gate

`experiments/ch15_source_audit.py` pins 17 source/config/test/doc hashes and enforces 53 predicates (70 checks total): public model entry points; fixed-window, double-accounting, reset, estimator, row-penalty, clock, and custom-validation markers; fixed-HBM2 hierarchy construction, stall-only delegation, and absence of non-test hierarchy callers; JSON parsing versus YAML generation; the separate full-config power consumer; missing descriptor integration; runtime-converter drops; DRAM target and aggregate membership; and source-present/non-archive `perf/cycle_model` separation. Appending one byte to `dram_model.c` in the disposable copy must trip the hash gate.

## Executable evidence plan

1. Build `libtucmodel.a` from the exported pin and prove `dram_model.o` and `memory_hierarchy.o` membership.
2. Compile `tests/test_dram.c` explicitly against that archive and require `12/12`.
3. Compile and run the official memory-hierarchy suite; require `10/10` and normal inferior exit.
4. Mutate the custom-bandwidth expectation from 500 to 501 in the disposable test; require `11/12`, `wrong BW`, and GDB's inferior exit code 01. Passing binaries must say `exited normally`; GDB's own zero process status is not accepted as evidence.
5. Compile and execute `ch15_dram_probe.c`; require:
   - HBM2 64-B read estimate 51 and HBM3 819-B read estimate 41;
   - first HBM2 access `cycles=50, stall=1000, current=0, budget=0`;
   - same-channel stall 1050, next-channel stall 1000, with no implicit time advance;
   - after 1,000 ticks, 64-B service on an available channel has stall 0 and leaves budget 255936;
   - row mode adds ten read cycles and one conflict while the following write remains 50 cycles;
   - a 1,024-B access at cycle zero derives 1,024 GB/s and 4.0 utilization;
   - double-accounted metering first emits the window stall on 64-B request 2,001 after refill, with pending 128064 and remaining budget 127936;
   - reset after moving the window start leaves start/size stale and immediately refills through unsigned subtraction, producing no initial window stall;
   - peak helper changes with its explicit clock argument while the estimator ignores the no-op setter;
   - hierarchy DRAM is fixed HBM2, returns the standalone stall only, leaves the caller byte unchanged, and does not tick implicitly;
   - parsed HBM3/bandwidth/row/latency values differ from enum-only preset construction;
   - probe failure count is zero.
6. Run `ch15_sweep_recompute.py` against the pinned historical report; require corrected HBM2/DDR5/DDR4 8-GHz values, the DDR4 1-GHz contradiction, and a fail-closed historical-report fingerprint.

## Fidelity labels carried into the manuscript

- Preset fields and equations are **implemented declarations**, not calibrated device models.
- Stateless estimates, access cycles, access stalls, channel availability, caller-driven current cycles, and derived stats are different quantities.
- The fixed bandwidth window and channel bookkeeping are deterministic analytical state, not queued event completion.
- The bandwidth admission path double-counts traffic and reset is history-dependent; it does not enforce the advertised capacity or define a faithful token bucket.
- Row mode is a flat read-only penalty, not row-buffer hit/miss tracking.
- Hierarchy delegation is reachable but has no DRAM backing store and drops base latency; descriptor DMA does not call the model.
- JSON load, YAML-to-header generation, compiled constants, full-config direct consumers, and runtime conversion are separate paths. Runtime conversion drops DRAM fields; the power model alone directly consumes full-config bandwidth as a clock heuristic.
- The historical type×clock report is a separate analytical formula, not execution of `dram_model.c`, and material rows/recommendations contradict its own constants.
- No audited evidence calibrates bandwidth, latency, utilization, rows, energy, area, or technology labels against RTL, a memory simulator, FPGA, or silicon.

## Predraft closure condition

Drafting is allowed only after the canonical run exists, `ch15_predraft_validate.py` passes against its immutable committed inputs, and a skeptical review independently rechecks equations, initial/window boundaries, read/write asymmetry, config consumers, integration callers, test meaning, sweep provenance, and prohibited physical claims.
