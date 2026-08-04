# Chapter 15 — Framing and Evidence Plan

**Working title:** DRAM Service Models and Bandwidth Claims  
**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (read-only)  
**Plan authority:** `PLAN.md` revision dated 2026-08-04  
**Status:** canonical v1 sealed; skeptical review blocked drafting and required a v2 evidence amendment for metering, reset, sweep arithmetic, configuration consumers, hierarchy reachability, and inferior-exit gating.

## 1. Fresh whole-book basis

The post-Chapter-14 review compared all written chapters with the historical 29-chapter proposal and the pinned source. Its durable evidence is `notes/whole-book-replanning-2026-08-04.md`. The review selected DRAM next because it is the last substantial off-chip feeding model whose own clocks, equations, configuration reachability, and integration boundaries have not received a chapter.

This is not merely the old Plan 14 slot revived. Chapters 9 and 10 already established that Tusim has multiple disconnected memory and DMA surfaces. Chapter 15 asks a narrower system question after those findings: which output from the standalone DRAM surface can support which bandwidth or latency claim?

## 2. Ranked scope candidates

| Rank | Candidate | Reader decision and evidence | Principal risk | Disposition |
|---|---|---|---|---|
| 1 | **DRAM Service Models and Bandwidth Claims** | distinguish stateful access accounting, stateless bulk estimates, hierarchy delegation, config declarations, and historical analytical sweeps; linked source, aggregate suite, docs, and discriminating probes are available | docs call the model cycle-accurate and DMA-integrated although execution does not establish those claims | **selected** |
| 2 | Double Buffering and Legal Overlap | choose active/shadow ownership and distinguish the standalone state machine from descriptor DMA and the pipeline controller | prior chapters establish boundaries but not reader-decision coverage | next Chapter 16 after cross-chapter audit amendment |
| 3 | Measurement Surfaces | choose producer/interval/units across counters, trace, cycle, and power modules | requires the DRAM and double-buffer producers to be named first | planned Chapter 17 |
| 4 | Resource Multiplexing | compare contexts, scheduling, and liveness | important remaining gap but independent of the off-chip feeding arc | planned Chapter 18 |
| 5 | Verification as Architecture | choose a verification rung and fail-closed gate | would synthesize before all major source surfaces are taught | planned Chapter 19 |

## 3. Reader decision

Given a DRAM technology/preset, clock, address stream, transfer size, and consuming Tusim API, decide:

1. whether the result came from a stateful access call, a stateless estimator, the memory-hierarchy wrapper, or a separate analytical report;
2. which clocks, budgets, counters, and state transitions produced it;
3. whether configuration values reach that consumer;
4. whether the result is a local deterministic equation, an integration observation, or a calibrated physical claim; and
5. which architecture alternatives remain meaningful once bus width, DRAM bandwidth, latency, channels, row policy, complexity, energy, and verification cost are separated.

## 4. Opening architecture question

**When does a number labeled “DRAM cycles” describe service demand, caller-driven accounting, or elapsed memory time—and when does it describe none of them?**

## 5. Scope

### In scope

- DRAM presets and custom parameter records;
- stateless `tu_dram_estimate_transfer()`;
- stateful `tu_dram_read/write()`, caller-driven `tu_dram_tick()`, channel bookkeeping, bandwidth windows, and statistics;
- the memory hierarchy's fixed-HBM2 construction and DRAM delegation;
- JSON/YAML declaration, parser/default/dump/doc behavior, runtime-conversion drop, and consumer reachability;
- the absence of descriptor-DMA→DRAM calls;
- the separate source-present `perf/cycle_model` DRAM channel only as a boundary, not as a second full chapter inside this one;
- the historical DRAM type×clock sweep as analytical evidence whose equations and provenance must be labeled independently from the standalone model;
- architecture trade-offs and the calibration evidence needed for physical conclusions.

### Explicitly out of scope

- re-auditing descriptor ownership/queues (Chapter 10);
- SRAM bank behavior (Chapter 9) or pipeline overlap (Chapters 10 and 14);
- the standalone double-buffer state machine and legal-overlap decision (Chapter 16);
- full performance-counter, trace, cycle-model, and power-model contracts (Chapter 17);
- a complete DRAM controller, JEDEC timing tutorial, or claim of real HBM/DDR device equivalence;
- modifying the pinned Tusim source to repair findings.

## 6. Initial source map

| Surface | Pinned evidence | Question |
|---|---|---|
| standalone model | `tu_cmodel/memory/dram_model.[ch]` | what state and equations produce access, stall, estimate, and stats outputs? |
| hierarchy consumer | `tu_cmodel/memory/memory_hierarchy.[ch]` | which DRAM outputs survive delegation and which are discarded? |
| descriptor DMA | `tu_cmodel/dma_descriptor.c` | is any DRAM model called from ordinary descriptor execution? |
| configuration | `config/tu_config.{json,yaml}`, `infra/config.[ch]`, `tu_config.h` | which DRAM values are declared, parsed, dropped, compiled, or manually consumed? |
| focused tests | `tests/test_dram.c`, `tests/test_memory_hierarchy.c`, `Makefile` | what exact properties and aggregate membership are demonstrated? |
| current docs | `docs/dram-model.md`, `docs/bandwidth-modeling.md` | which statements agree with execution and which are historical/overclaims? |
| exploration report | `docs/exploration/dram-type-clock-sweep.md` | is the table generated by this model or by a separate formula? |
| adjacent alternative | `tu_cmodel/perf/cycle_model.[ch]` | how do we prevent two DRAM abstractions from being conflated? |

## 7. Evidence ladders

### 7.1 Stateful access ladder

preset/custom record → model construction → zeroed runtime state → explicit caller ticks → access call → base-latency output + separate stall output → stats derived from cumulative bytes and caller-driven current cycle.

### 7.2 Estimate ladder

preset/custom bandwidth + fixed 1 GHz conversion → `ceil(bytes / bandwidth_bytes_per_cycle)` + read/write latency → returned scalar. No access state, channel state, bandwidth window, row mode, or stats mutation.

### 7.3 Configuration ladder

YAML/JSON declaration → parser/default struct → validation (or absence) → `tu_config_to_runtime()` → construction/consumer. Each DRAM field must be classified separately; similar values in a preset and config do not prove propagation.

### 7.4 Integration ladder

archive membership → focused test → memory-hierarchy caller → ordinary descriptor/MMA caller → calibrated external reference. The chapter must stop at the achieved rung.

## 8. Discriminating executable probes

The probe must hand-check and print at least:

1. HBM2/HBM3 preset geometry and estimator results;
2. zero initial bandwidth budget and the first-access window stall;
3. same-channel and different-channel stall bookkeeping without implicit time advance;
4. refill after exactly 1,000 caller ticks;
5. row mode's flat read-only penalty and conflict count;
6. derived bandwidth/utilization above peak when bytes are recorded at current cycle zero;
7. `tu_dram_set_core_clock()` no-op versus the separate clock argument accepted by the peak helper;
8. hierarchy fixed-HBM2 construction, stall-only delegation, and lack of DRAM backing-store byte effects;
9. parsed HBM3/bandwidth/row settings versus enum-only preset construction;
10. focused test result, mutation control, static linkage, and source-hash drift control.
11. the request ordinal at which double-counted pending-plus-remaining-budget logic first produces a bandwidth stall;
12. reset after a moved window start, proving stale-window unsigned-underflow refill and history-dependent post-reset behavior;
13. static rejection of unsafe custom zero-channel/zero-burst cases rather than executing undefined behavior;
14. independent recomputation of contradictory 8-GHz and 1-GHz claims in the historical type×clock sweep;
15. absence of non-test hierarchy-wrapper callers and the separate full-config power-model bandwidth consumer;
16. GDB inferior exit parsing for both passing binaries and the deliberately failing mutation.

## 9. Skeptical-review gates

- Hand-recompute every probe value from pinned equations; do not trust the transcript or CHECKs.
- Distinguish returned `cycles` from returned `stall`, `current_cycle`, channel availability, cumulative cycle counters, and elapsed time.
- Check initial-state and refill-window boundaries (0, 999, 1000 ticks).
- Check whether admission compares consumed traffic with total or remaining budget; test the exact threshold rather than one post-refill request.
- Reset only after moving the window start; superficial reset-at-start tests cannot expose stale-window state.
- Verify read and write paths separately; do not infer symmetry.
- Inventory every non-test caller and every config-field reader.
- Prove whether test membership is aggregate, standalone, or source-only.
- Recompute historical sweep rows and conclusions from their own constants; report prose is not trusted evidence.
- Treat JSON loading, YAML-to-header generation, compiled constants, full-config direct consumers, and runtime conversion as five distinct reachability paths.
- Separate the standalone model from `perf/cycle_model` and the historical sweep formula.
- Reject “cycle accurate,” “DMA integrated,” “sliding window,” “row hit/miss,” “achieved bandwidth,” and “real-world preset” wording unless the exact claim is bounded by execution and provenance.
- State the validation ladder and absence of RTL/silicon calibration.

## 10. Claims the chapter must not make

- that an access call delays completion or advances simulated time;
- that returned base cycles include returned stall cycles;
- that channel bookkeeping implements a queued concurrent controller;
- that row-buffer hits/misses are tracked by the standalone model;
- that config-loaded DRAM values select global DMA or memory-hierarchy behavior;
- that the descriptor DMA queries this model;
- that historical sweep TOPS values were executed through the standalone model;
- that preset labels validate a physical DDR/HBM device, area, power, or sign-off performance;
- that any DRAM/cycle output can be added to other chapter metrics without a shared schedule and clock contract.
